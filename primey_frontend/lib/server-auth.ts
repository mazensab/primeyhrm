// ======================================================
// PRIMEY HR CLOUD
// Server Authentication Guard (Next.js 15 SAFE)
// ======================================================

import { cookies } from "next/headers";

const API = process.env.NEXT_PUBLIC_API_URL!;

/**
 * ======================================================
 * ✅ SERVER SESSION VALIDATOR
 * Used inside Layout Guards
 * ======================================================
 */
export async function getServerSession() {

  /**
   * --------------------------------------------------
   * ✅ NEXT 15 REQUIRED (ASYNC COOKIES)
   * --------------------------------------------------
   */
  const cookieStore = await cookies();

  const cookieHeader = cookieStore
    .getAll()
    .map(c => `${c.name}=${c.value}`)
    .join("; ");

  /**
   * 🚨 No cookies → anonymous user
   */
  if (!cookieHeader) {
    return null;
  }

  try {

    const res = await fetch(
      `${API}/api/auth/whoami/`,
      {
        method: "GET",
        headers: {
          cookie: cookieHeader,
        },
        cache: "no-store",
      }
    );

    if (!res.ok) {
      return null;
    }

    const data = await res.json();

    if (!data?.authenticated) {
      return null;
    }

    return data;

  } catch {

    /**
     * Backend offline safe mode
     */
    return null;
  }
}