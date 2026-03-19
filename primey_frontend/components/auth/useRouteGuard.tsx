"use client";

// ======================================================
// 🔐 PRIMEY HR CLOUD — ROUTE GUARD
// Client Runtime Protection
// ======================================================

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/providers/AuthProvider";

type Props = {
  children: React.ReactNode;
  role: "system" | "company";
};

export default function RouteGuard({
  children,
  role,
}: Props) {
  const router = useRouter();
  const session = useAuth();

  useEffect(() => {
    if (!session?.authenticated) {
      router.replace("/login");
      return;
    }

    const isInternalSystemUser =
      session?.is_superuser === true ||
      session?.role === "system" ||
      session?.role === "SUPER_ADMIN" ||
      session?.role === "SYSTEM_ADMIN" ||
      session?.role === "SUPPORT";

    /**
     * SYSTEM AREA
     */
    if (
      role === "system" &&
      !isInternalSystemUser
    ) {
      router.replace("/company");
      return;
    }

    /**
     * COMPANY AREA
     */
    if (
      role === "company" &&
      isInternalSystemUser
    ) {
      router.replace("/system");
      return;
    }
  }, [session, role, router]);

  return <>{children}</>;
}