"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowLeft,
  ArrowRight,
  Eye,
  EyeOff,
  Loader2,
  Mail,
  ShieldCheck,
  Languages,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";

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

export default function ResetGuestPasswordPage() {
  const [locale, setLocale] = useState<AppLocale>("ar");

  const [identifier, setIdentifier] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const API = process.env.NEXT_PUBLIC_API_URL;

  const isArabic = locale === "ar";
  const BackIcon = isArabic ? ArrowRight : ArrowLeft;

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
      console.error("Reset password locale initialization error:", error);
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
      console.error("Reset password language toggle error:", error);
    }
  };

  /* =========================================
     RESET PASSWORD HANDLER
  ========================================= */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;

    const cleanIdentifier = identifier.trim();

    if (!cleanIdentifier) {
      toast.error(
        isArabic ? "الرجاء إدخال اسم المستخدم أو البريد الإلكتروني" : "Please enter username or email"
      );
      return;
    }

    if (!newPassword || !confirmPassword) {
      toast.error(
        isArabic ? "الرجاء إدخال كلمة المرور الجديدة" : "Please enter the new password"
      );
      return;
    }

    if (newPassword.length < 8) {
      toast.error(
        isArabic ? "يجب أن تكون كلمة المرور الجديدة 8 أحرف على الأقل" : "New password must be at least 8 characters"
      );
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error(
        isArabic ? "كلمتا المرور غير متطابقتين" : "Passwords do not match"
      );
      return;
    }

    setLoading(true);

    try {
      await fetch(`${API}/api/auth/csrf/`, {
        credentials: "include",
      });

      const csrfToken = getCookie("csrftoken");

      if (!csrfToken) {
        throw new Error(isArabic ? "رمز الحماية CSRF غير موجود" : "CSRF token missing");
      }

      const res = await fetch(`${API}/api/auth/resetguest-password/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
          identifier: cleanIdentifier,
          new_password: newPassword,
          confirm_password: confirmPassword,
        }),
      });

      const data = await res.json().catch(() => null);

      if (!res.ok) {
        throw new Error(
          data?.message ||
            data?.error ||
            (isArabic ? "فشلت إعادة تعيين كلمة المرور" : "Failed to reset password")
        );
      }

      setDone(true);
      setIdentifier("");
      setNewPassword("");
      setConfirmPassword("");
      setShowNewPassword(false);
      setShowConfirmPassword(false);

      toast.success(
        data?.message ||
          (isArabic ? "تمت إعادة تعيين كلمة المرور بنجاح" : "Password reset successfully")
      );
    } catch (error: any) {
      toast.error(error?.message || (isArabic ? "خطأ في الخادم" : "Server error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="flex min-h-screen items-center justify-center bg-muted/40 px-4 py-8"
      dir={isArabic ? "rtl" : "ltr"}
    >
      <Card className="w-full max-w-md rounded-2xl border bg-background shadow-lg">
        <CardContent className="p-8">
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
              {isArabic ? "إعادة تعيين كلمة المرور" : "Reset Password"}
            </h2>
            <p className="text-muted-foreground mt-2 text-sm">
              {isArabic
                ? "أدخل اسم المستخدم أو البريد الإلكتروني وحدد كلمة مرور جديدة"
                : "Enter your username or email and set a new password"}
            </p>
          </div>

          {/* SUCCESS */}
          {done && (
            <div className="mt-6 rounded-xl border bg-muted/50 p-4">
              <div className="flex items-start gap-3">
                <ShieldCheck className="mt-0.5 h-5 w-5" />
                <div className={isArabic ? "text-right" : "text-left"}>
                  <p className="font-medium">
                    {isArabic ? "اكتملت إعادة تعيين كلمة المرور" : "Password reset completed"}
                  </p>
                  <p className="text-muted-foreground mt-1 text-sm">
                    {isArabic
                      ? "تم تحديث كلمة المرور بنجاح. تم إرسال إشعار عبر البريد الإلكتروني إذا كان الحساب يحتوي على بريد إلكتروني."
                      : "Your password has been updated successfully. A notification email has been sent if the account has an email address."}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* FORM */}
          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                {isArabic ? "اسم المستخدم أو البريد الإلكتروني" : "Username or Email"}
              </label>

              <div className="relative">
                <Mail
                  className={`text-muted-foreground absolute top-1/2 h-4 w-4 -translate-y-1/2 ${
                    isArabic ? "right-3" : "left-3"
                  }`}
                />
                <Input
                  dir={isArabic ? "rtl" : "ltr"}
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  placeholder={
                    isArabic ? "أدخل اسم المستخدم أو البريد الإلكتروني" : "Enter username or email"
                  }
                  className={`${isArabic ? "pr-10 text-right" : "pl-10 text-left"}`}
                  autoComplete="username"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                {isArabic ? "كلمة المرور الجديدة" : "New Password"}
              </label>

              <div className="relative">
                <Input
                  type={showNewPassword ? "text" : "password"}
                  dir={isArabic ? "rtl" : "ltr"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder={isArabic ? "أدخل كلمة المرور الجديدة" : "Enter new password"}
                  className={`${isArabic ? "pl-12 text-right" : "pr-12 text-left"}`}
                  autoComplete="new-password"
                />

                <button
                  type="button"
                  onClick={() => setShowNewPassword((prev) => !prev)}
                  className={`absolute top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-muted-foreground transition hover:bg-muted hover:text-foreground ${
                    isArabic ? "left-3" : "right-3"
                  }`}
                  aria-label={
                    showNewPassword
                      ? isArabic
                        ? "إخفاء كلمة المرور"
                        : "Hide password"
                      : isArabic
                      ? "إظهار كلمة المرور"
                      : "Show password"
                  }
                >
                  {showNewPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">
                {isArabic ? "تأكيد كلمة المرور" : "Confirm Password"}
              </label>

              <div className="relative">
                <Input
                  type={showConfirmPassword ? "text" : "password"}
                  dir={isArabic ? "rtl" : "ltr"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder={isArabic ? "أكد كلمة المرور الجديدة" : "Confirm new password"}
                  className={`${isArabic ? "pl-12 text-right" : "pr-12 text-left"}`}
                  autoComplete="new-password"
                />

                <button
                  type="button"
                  onClick={() => setShowConfirmPassword((prev) => !prev)}
                  className={`absolute top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-muted-foreground transition hover:bg-muted hover:text-foreground ${
                    isArabic ? "left-3" : "right-3"
                  }`}
                  aria-label={
                    showConfirmPassword
                      ? isArabic
                        ? "إخفاء كلمة المرور"
                        : "Hide password"
                      : isArabic
                      ? "إظهار كلمة المرور"
                      : "Show password"
                  }
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {isArabic ? "جارٍ إعادة التعيين..." : "Resetting..."}
                </>
              ) : isArabic ? (
                "إعادة تعيين كلمة المرور"
              ) : (
                "Reset Password"
              )}
            </Button>

            <Link
              href="/login"
              className="text-muted-foreground hover:text-foreground inline-flex w-full items-center justify-center gap-2 text-sm transition"
            >
              <BackIcon className="h-4 w-4" />
              {isArabic ? "العودة إلى تسجيل الدخول" : "Back to login"}
            </Link>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}