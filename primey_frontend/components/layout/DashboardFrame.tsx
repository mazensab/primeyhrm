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
import { cn } from "@/lib/utils"

type DashboardFrameProps = {
  children: React.ReactNode
  sidebarType: "system" | "company"
  compact?: boolean
}

export default function DashboardFrame({
  children,
  sidebarType,
  compact = false,
}: DashboardFrameProps) {
  return (
    <SidebarProvider>
      <AppSidebar type={sidebarType} />

      <SidebarInset className="bg-sidebar">
        <div
          className={cn(
            "flex flex-1 flex-col",
            compact ? "p-2 md:p-2" : "p-4 md:p-2"
          )}
        >
          <div
            className={cn(
              "flex flex-1 flex-col overflow-hidden",
              compact
                ? "rounded-lg bg-muted/10 shadow-none"
                : "rounded-xl bg-muted/20 shadow-sm"
            )}
          >
            <SiteHeader />

            <main
              className={cn(
                "flex-1",
                compact ? "p-2 pt-2 md:p-3 md:pt-2" : "p-6 pt-5"
              )}
            >
              {children}
            </main>
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}