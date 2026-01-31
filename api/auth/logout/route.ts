import { NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL!;

export async function POST(request: Request) {
  const cookies = request.headers.get("cookie") || "";

  // 1️⃣ جلب CSRF من Django
  const csrfRes = await fetch(`${API_BASE}/api/auth/csrf/`, {
    credentials: "include",
    headers: { cookie: cookies },
  });

  const setCookie = csrfRes.headers.get("set-cookie") || "";

  // استخراج csrftoken
  const csrfMatch = setCookie.match(/csrftoken=([^;]+)/);
  const csrftoken = csrfMatch?.[1];

  // 2️⃣ تنفيذ logout الحقيقي
  const res = await fetch(`${API_BASE}/api/auth/logout/`, {
    method: "POST",
    credentials: "include",
    headers: {
      cookie: cookies,
      "X-CSRFToken": csrftoken || "",
      Referer: API_BASE,
    },
  });

  if (!res.ok) {
    return NextResponse.json(
      { error: "Logout failed" },
      { status: res.status }
    );
  }

  // 3️⃣ تنظيف كوكيز الواجهة
  const response = NextResponse.json({ success: true });
  response.cookies.delete("sessionid");
  response.cookies.delete("csrftoken");

  return response;
}
