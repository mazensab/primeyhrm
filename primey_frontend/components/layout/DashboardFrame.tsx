// ======================================================
// 🏛 PRIMEY HR CLOUD — DASHBOARD FRAME
// Reusable Visual Frame with Sidebar Variant
// RTL Ready Layout Frame
// ======================================================

import {
  SidebarProvider,
  SidebarInset,
} from "@/components/ui/sidebar"

import { AppSidebar } from "@/components/layout/sidebar/app-sidebar"
import { SiteHeader } from "@/components/layout/header"

type DashboardFrameProps = {
  children: React.ReactNode
  sidebarType: "system" | "company"
}

export default function DashboardFrame({
  children,
  sidebarType,
}: DashboardFrameProps) {
  return (
    <SidebarProvider>
      <AppSidebar type={sidebarType} />

      <SidebarInset className="bg-sidebar">
        <div className="flex flex-1 flex-col p-4 md:p-2">
          <div
            className="
              flex flex-1 flex-col
              overflow-hidden
              rounded-xl
              bg-muted/20
              shadow-sm
            "
          >
            <SiteHeader />

            <main className="flex-1 p-6 pt-5">
              {children}
            </main>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}