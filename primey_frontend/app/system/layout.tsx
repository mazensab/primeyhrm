// ======================================================
// 🔐 Mham Cloud — SYSTEM LAYOUT
// Uses Shared DashboardFrame with System Sidebar
// ======================================================

import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/server-auth";

import { AuthProvider } from "@/components/providers/AuthProvider";
import RouteGuard from "@/components/auth/useRouteGuard";
import DashboardFrame from "@/components/layout/DashboardFrame";

export default async function SystemLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession();

  if (!session) redirect("/login");

  const isInternalSystemUser =
    session?.is_superuser === true ||
    session?.role === "system" ||
    session?.role === "SUPER_ADMIN" ||
    session?.role === "SYSTEM_ADMIN" ||
    session?.role === "SUPPORT";

  if (!isInternalSystemUser) redirect("/company");

  return (
    <AuthProvider initialUser={session}>
      <RouteGuard role="system">
        <DashboardFrame sidebarType="system">
          {children}
        </DashboardFrame>
      </RouteGuard>
    </AuthProvider>
  );
}