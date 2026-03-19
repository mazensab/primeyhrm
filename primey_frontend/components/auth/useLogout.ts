"use client";

// ======================================================
// 🔐 PRIMEY HR CLOUD — AUTH Ω SMART LOGOUT
// Enterprise Logout Hook
// ======================================================

import { useRouter } from "next/navigation";

export function useLogout() {

  const router = useRouter();

  async function logout() {

    try {

      /**
       * ----------------------------------------
       * ✅ CALL DJANGO LOGOUT API
       * ----------------------------------------
       */
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/auth/logout/`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

    } catch {
      // ignore network failure
    }

    /**
     * ----------------------------------------
     * 🧠 MULTI TAB LOGOUT SYNC
     * ----------------------------------------
     */
    localStorage.setItem(
      "primey_logout",
      Date.now().toString()
    );

    /**
     * ----------------------------------------
     * 🚀 HARD REDIRECT
     * ----------------------------------------
     */
    router.replace("/login");

    /**
     * prevent back navigation cache
     */
    router.refresh();
  }

  return logout;
}