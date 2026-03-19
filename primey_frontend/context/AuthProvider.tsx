"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useRef,
  ReactNode,
} from "react";

type AuthUser = any | null;

type AuthContextType = {
  user: AuthUser;
  authenticated: boolean;
  loading: boolean;
  setUser: (u: AuthUser) => void;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({
  children,
  initialUser,
}: {
  children: ReactNode;
  initialUser: AuthUser;
}) {

  /**
   * =====================================================
   * ✅ USER STATE (Hydrated from Server)
   * =====================================================
   */
  const [user, _setUser] =
    useState<AuthUser>(initialUser);

  /**
   * =====================================================
   * 🔐 Ω+ Session Version Baseline
   * =====================================================
   * يبدأ من النسخة القادمة من Server Hydration
   */
  const versionRef = useRef<number | null>(
    initialUser?.session?.version ?? null
  );

  /**
   * =====================================================
   * 🔐 Broadcast Channel (Multi-Tab)
   * =====================================================
   */
  const channelRef = useRef<BroadcastChannel | null>(null);

  useEffect(() => {

    if (typeof window === "undefined") return;

    const channel = new BroadcastChannel("primey-auth");
    channelRef.current = channel;

    channel.onmessage = (event) => {

      if (event.data === "LOGOUT") {
        _setUser(null);
      }

    };

    return () => {
      channel.close();
    };

  }, []);

  /**
   * =====================================================
   * 🔐 Wrapped setUser
   * =====================================================
   */
  const setUser = (u: AuthUser) => {

    if (!u && channelRef.current) {
      channelRef.current.postMessage("LOGOUT");
    }

    _setUser(u);
  };

  /**
   * =====================================================
   * 🔄 Ω+ Drift Detection Engine
   * =====================================================
   * يتحقق كل 30 ثانية من session.version
   */
  useEffect(() => {

    if (!user) return;

    const API = process.env.NEXT_PUBLIC_API_URL;

    const interval = setInterval(async () => {

      try {

        const res = await fetch(
          `${API}/api/auth/whoami/`,
          { credentials: "include" }
        );

        if (!res.ok) return;

        const data = await res.json();

        if (!data?.authenticated) {
          setUser(null);
          return;
        }

        const serverVersion =
          data?.session?.version ?? null;

        if (
          serverVersion !== null &&
          versionRef.current !== null &&
          serverVersion !== versionRef.current
        ) {
          // Version mismatch → Force logout
          setUser(null);
          return;
        }

      } catch {
        // Silent fail (Network / backend issue)
      }

    }, 30000); // 30s

    return () => clearInterval(interval);

  }, [user]);

  return (
    <AuthContext.Provider
      value={{
        user,
        authenticated: !!user,
        loading: false,
        setUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

/**
 * =====================================================
 * ✅ Hook
 * =====================================================
 */
export function useAuth() {

  const ctx = useContext(AuthContext);

  if (!ctx) {
    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return ctx;
}