"use client";

// ======================================================
// 🔐 Mham Cloud — AUTH Ω PROVIDER
// Reactive Enterprise Session Core
// ======================================================

import React, {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import { useRouter } from "next/navigation";

// ======================================================
// TYPES
// ======================================================

export type AuthSession = {
  authenticated: boolean;
  is_superuser: boolean;
  role?: string | null;
  company?: any;
  company_id?: number | null;
  user?: any;
  subscription?: any;
};

// ======================================================
// CONTEXT
// ======================================================

const AuthContext = createContext<AuthSession | null>(null);

// ======================================================
// PROVIDER
// ======================================================

export function AuthProvider({
  children,
  initialUser,
}: {
  children: React.ReactNode;
  initialUser: AuthSession;
}) {
  const router = useRouter();

  const [session, setSession] = useState<AuthSession>(initialUser);

  /**
   * =====================================================
   * 🔄 SESSION VALIDATION LOOP
   * =====================================================
   * prevents expired-cookie ghost session
   */
  useEffect(() => {
    let active = true;

    async function validateSession() {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/auth/whoami/`,
          {
            credentials: "include",
            cache: "no-store",
          }
        );

        if (!res.ok) throw new Error();

        const data = await res.json();

        if (!data?.authenticated && active) {
          // broadcast logout to all tabs
          localStorage.setItem("primey_logout", Date.now().toString());
          router.replace("/login");
          return;
        }

        if (active) {
          setSession(data);
        }
      } catch {
        router.replace("/login");
      }
    }

    /**
     * check every 60s
     */
    const interval = setInterval(validateSession, 60000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [router]);

  /**
   * =====================================================
   * 🧠 MULTI TAB LOGOUT SYNC
   * =====================================================
   */
  useEffect(() => {
    function syncLogout(e: StorageEvent) {
      if (e.key === "primey_logout") {
        router.replace("/login");
      }
    }

    window.addEventListener("storage", syncLogout);

    return () => window.removeEventListener("storage", syncLogout);
  }, [router]);

  return (
    <AuthContext.Provider value={session}>
      {children}
    </AuthContext.Provider>
  );
}

// ======================================================
// HOOK
// ======================================================

export function useAuth(): AuthSession {
  const ctx = useContext(AuthContext);

  if (!ctx) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return ctx;
}