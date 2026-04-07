// ======================================================
// 🏢 Mham Cloud — COMPANY LAYOUT
// التخطيط العام الخاص بمنطقة الشركة
// يعتمد على DashboardFrame المشترك مع Company Sidebar
// ======================================================

import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/server-auth";

import { AuthProvider } from "@/components/providers/AuthProvider";
import RouteGuard from "@/components/auth/useRouteGuard";
import DashboardFrame from "@/components/layout/DashboardFrame";

export default async function CompanyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession();

  if (!session) redirect("/login");

  return (
    <AuthProvider initialUser={session}>
      <RouteGuard role="company">
        <DashboardFrame sidebarType="company">
          {children}
        </DashboardFrame>
      </RouteGuard>
    </AuthProvider>
  );
}