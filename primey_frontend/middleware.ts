import { NextRequest, NextResponse } from "next/server";

const API = process.env.NEXT_PUBLIC_API_URL;

/*
==================================================
✅ Mham Cloud — AUTH MIDDLEWARE V5.4
Optimized Session Guard
✅ Compatible with project original API pattern
==================================================
*/

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // ------------------------------------------------
  // 🌍 PUBLIC ROUTES
  // ------------------------------------------------
  const publicRoutes = [
    "/",
    "/login",
    "/register",
    "/forgot-password",
    "/pricing",
  ];

  const isPublic = publicRoutes.some(
    (route) => pathname === route || pathname.startsWith(route + "/")
  );

  // ------------------------------------------------
  // 🚫 SKIP STATIC / NEXT INTERNAL
  // ------------------------------------------------
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon.ico") ||
    pathname.startsWith("/images") ||
    pathname.startsWith("/logo") ||
    pathname.startsWith("/icons") ||
    pathname.startsWith("/currency")
  ) {
    return NextResponse.next();
  }

  // ------------------------------------------------
  // 🍪 READ SESSION COOKIE ONLY
  // ------------------------------------------------
  const sessionCookie = req.cookies.get("sessionid")?.value || "";

  /**
   =================================================
   🚨 FAST PATH
   No real Django session
   =================================================
   */
  if (!sessionCookie) {
    if (!isPublic) {
      return redirect(req, "/login");
    }

    return NextResponse.next();
  }

  try {
    if (!API) {
      throw new Error("NEXT_PUBLIC_API_URL is not configured");
    }

    // ------------------------------------------------
    // 🔐 WHOAMI VALIDATION
    // ✅ Project standard:
    // NEXT_PUBLIC_API_URL=http://localhost:8000
    // so final URL must be:
    // /api/auth/whoami/
    // ------------------------------------------------
    const res = await fetch(`${API}/api/auth/whoami/`, {
      method: "GET",
      headers: {
        cookie: `sessionid=${sessionCookie}`,
        Accept: "application/json",
      },
      cache: "no-store",
    });

    if (!res.ok) {
      throw new Error("whoami failed");
    }

    const data = await res.json();

    const authenticated = data?.authenticated === true;

    const isInternalSystemUser =
      data?.is_superuser === true ||
      data?.role === "system" ||
      data?.role === "SUPER_ADMIN" ||
      data?.role === "SYSTEM_ADMIN" ||
      data?.role === "SUPPORT";

    /**
     =================================================
     ❌ NOT AUTHENTICATED
     =================================================
     */
    if (!authenticated) {
      if (!isPublic) {
        return redirect(req, "/login");
      }

      return NextResponse.next();
    }

    /**
     =================================================
     ✅ BLOCK LOGIN AFTER AUTH
     =================================================
     */
    if (pathname === "/login") {
      return redirect(req, isInternalSystemUser ? "/system" : "/company");
    }

    /**
     =================================================
     🟦 SYSTEM ROLE GUARD
     =================================================
     */
    if (pathname.startsWith("/system") && !isInternalSystemUser) {
      return redirect(req, "/company");
    }

    /**
     =================================================
     🏢 COMPANY ROLE GUARD
     =================================================
     */
    if (pathname.startsWith("/company") && isInternalSystemUser) {
      return redirect(req, "/system");
    }

    return NextResponse.next();
  } catch (error) {
    console.error("Middleware auth validation failed:", error);

    /**
     =================================================
     🚑 BACKEND OFFLINE SAFE MODE
     =================================================
     */
    if (!isPublic) {
      return redirect(req, "/login");
    }

    return NextResponse.next();
  }
}

/*
==================================================
✅ HARD REDIRECT HELPER
Fix App Router Blank Layout
==================================================
*/

function redirect(req: NextRequest, path: string) {
  const url = new URL(path, req.url);

  const response = NextResponse.redirect(url, 307);

  response.headers.set("x-middleware-cache", "no-cache");

  return response;
}

/*
==================================================
✅ ROUTE PROTECTION MAP
==================================================
*/

export const config = {
  matcher: [
    "/system",
    "/system/:path*",
    "/company",
    "/company/:path*",
    "/login",
    "/pricing",
  ],
};