"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { Eye, EyeOff, Languages } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/* =========================================
   ✅ Read CSRF Cookie
========================================= */
function getCookie(name: string) {
  if (typeof document === "undefined") return null;

  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);

  if (parts.length === 2) {
    return parts.pop()?.split(";").shift();
  }

  return null;
}

type AppLocale = "ar" | "en";

export default function Page() {
  const router = useRouter();

  const [locale, setLocale] = useState<AppLocale>("ar");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isArabic = locale === "ar";

  useEffect(() => {
    try {
      const savedLocale =
        typeof window !== "undefined"
          ? (window.localStorage.getItem("primey-locale") as AppLocale | null)
          : null;

      const nextLocale: AppLocale = savedLocale === "en" ? "en" : "ar";
      setLocale(nextLocale);

      if (typeof document !== "undefined") {
        document.documentElement.lang = nextLocale;
        document.documentElement.dir = nextLocale === "ar" ? "rtl" : "ltr";
        document.body.setAttribute("dir", nextLocale === "ar" ? "rtl" : "ltr");
      }
    } catch (error) {
      console.error("Login locale initialization error:", error);
    }
  }, []);

  const toggleLanguage = () => {
    try {
      const nextLocale: AppLocale = locale === "ar" ? "en" : "ar";
      setLocale(nextLocale);

      if (typeof window !== "undefined") {
        window.localStorage.setItem("primey-locale", nextLocale);
      }

      if (typeof document !== "undefined") {
        document.documentElement.lang = nextLocale;
        document.documentElement.dir = nextLocale === "ar" ? "rtl" : "ltr";
        document.body.setAttribute("dir", nextLocale === "ar" ? "rtl" : "ltr");
      }
    } catch (error) {
      console.error("Login language toggle error:", error);
    }
  };

  /* =========================================
     LOGIN HANDLER
  ========================================= */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;

    setLoading(true);
    setError(null);

    try {
      const API = process.env.NEXT_PUBLIC_API_URL;

      await fetch(`${API}/api/auth/csrf/`, {
        credentials: "include",
      });

      const csrfToken = getCookie("csrftoken");

      if (!csrfToken) {
        throw new Error(
          isArabic ? "رمز الحماية CSRF غير موجود" : "CSRF token missing"
        );
      }

      const loginRes = await fetch(`${API}/api/auth/login/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
          username,
          password,
          remember,
        }),
      });

      if (!loginRes.ok) {
        throw new Error(
          isArabic
            ? "اسم المستخدم أو كلمة المرور غير صحيحة"
            : "Invalid username or password"
        );
      }

      const whoamiRes = await fetch(`${API}/api/auth/whoami/`, {
        credentials: "include",
      });

      if (!whoamiRes.ok) {
        throw new Error(
          isArabic ? "فشل التحقق من الجلسة" : "Session validation failed"
        );
      }

      const user = await whoamiRes.json();

      const isInternalSystemUser =
        user?.is_superuser === true ||
        user?.role === "system" ||
        user?.role === "SUPER_ADMIN" ||
        user?.role === "SYSTEM_ADMIN" ||
        user?.role === "SUPPORT";

      if (isInternalSystemUser) {
        router.replace("/system");
      } else {
        router.replace("/company");
      }
    } catch (err: any) {
      setError(err.message || (isArabic ? "فشل تسجيل الدخول" : "Login failed"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 px-4">
      <div className="w-full max-w-md rounded-2xl border bg-background p-8 shadow-lg">
        <div className="mb-4 flex justify-end">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={toggleLanguage}
            className="h-9 rounded-xl"
          >
            <Languages className="h-4 w-4" />
            <span>{isArabic ? "EN" : "عربي"}</span>
          </Button>
        </div>

        {/* LOGO */}
        <div className="mb-6 flex justify-center">
          <Image
            src="/logo/primey.svg"
            alt="Primey Logo"
            width={140}
            height={120}
            priority
          />
        </div>

        {/* HEADER */}
        <div className="text-center">
          <h2 className="text-3xl font-bold">
            {isArabic ? "مرحبًا بعودتك" : "Welcome back"}
          </h2>
          <p className="text-muted-foreground mt-2 text-sm">
            {isArabic
              ? "يرجى تسجيل الدخول إلى حسابك"
              : "Please sign in to your account"}
          </p>
        </div>

        {/* FORM */}
        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          <Input
            required
            dir={isArabic ? "rtl" : "ltr"}
            placeholder={isArabic ? "اسم المستخدم" : "Username"}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className={isArabic ? "text-right" : "text-left"}
          />

          {/* Password Field With Toggle */}
          <div className="relative">
            <Input
              type={showPassword ? "text" : "password"}
              required
              dir={isArabic ? "rtl" : "ltr"}
              placeholder={isArabic ? "كلمة المرور" : "Password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={`${
                isArabic ? "pl-11 text-right" : "pr-11 text-left"
              }`}
            />

            <button
              type="button"
              onClick={() => setShowPassword((prev) => !prev)}
              className={`absolute top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-muted-foreground transition hover:bg-muted hover:text-foreground ${
                isArabic ? "left-3" : "right-3"
              }`}
              aria-label={
                showPassword
                  ? isArabic
                    ? "إخفاء كلمة المرور"
                    : "Hide password"
                  : isArabic
                  ? "إظهار كلمة المرور"
                  : "Show password"
              }
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          </div>

          {/* Remember + Forgot */}
          <div
            className={`flex items-center justify-between text-sm ${
              isArabic ? "flex-row-reverse" : ""
            }`}
          >
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={remember}
                onChange={() => setRemember(!remember)}
              />
              {isArabic ? "تذكرني" : "Remember me"}
            </label>

            <Link
              href="/reset-password"
              className="text-primary font-medium hover:underline"
            >
              {isArabic ? "إعادة تعيين كلمة المرور؟" : "Reset password?"}
            </Link>
          </div>

          {error && (
            <p className={`text-sm text-red-500 ${isArabic ? "text-right" : "text-left"}`}>
              {error}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading
              ? isArabic
                ? "جارٍ تسجيل الدخول..."
                : "Signing in..."
              : isArabic
              ? "تسجيل الدخول"
              : "Sign in"}
          </Button>
        </form>
      </div>
    </div>
  );
}