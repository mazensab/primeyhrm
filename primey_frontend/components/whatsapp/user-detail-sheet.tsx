"use client"

// ============================================================
// 📂 الملف: components/whatsapp/user-detail-sheet.tsx
// 🟢 Primey HR Cloud - WhatsApp User Detail Sheet
// ------------------------------------------------------------
// ✅ إزالة الاعتماد على context الأصلي
// ✅ إزالة generate-avatar-fallback غير الموجود
// ✅ الحفاظ على الشكل البصري كمرحلة أولى
// ✅ جاهز لاحقًا للربط مع بيانات المحادثة الحقيقية
// ============================================================

import React from "react"
import { Mail, MapPin, Phone, User2 } from "lucide-react"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Separator } from "@/components/ui/separator"

function getAvatarFallback(name: string) {
  const clean = (name || "").trim()
  if (!clean) return "NA"

  const parts = clean.split(/\s+/).filter(Boolean)
  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase()
  }

  return `${parts[0][0] ?? ""}${parts[1][0] ?? ""}`.toUpperCase()
}

type UserDetailSheetProps = {
  open?: boolean
  onOpenChange?: (open: boolean) => void
}

export default function UserDetailSheet({
  open = false,
  onOpenChange,
}: UserDetailSheetProps) {
  const user = {
    name: "WhatsApp Contact",
    phone: "+966500000000",
    email: "contact@example.com",
    location: "Saudi Arabia",
    avatar: "",
    role: "Customer",
    status: "Active",
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-md">
        <SheetHeader className="text-start">
          <SheetTitle>Contact details</SheetTitle>
          <SheetDescription>
            Contact profile preview until backend binding is completed.
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          <div className="flex flex-col items-center text-center">
            <Avatar className="h-20 w-20">
              <AvatarImage src={user.avatar} alt={user.name} />
              <AvatarFallback>{getAvatarFallback(user.name)}</AvatarFallback>
            </Avatar>

            <h3 className="mt-3 text-lg font-semibold">{user.name}</h3>

            <div className="mt-2 flex items-center gap-2">
              <Badge variant="secondary">{user.role}</Badge>
              <Badge>{user.status}</Badge>
            </div>
          </div>

          <Separator />

          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <User2 className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Full name</p>
                <p className="text-sm font-medium">{user.name}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Phone className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Phone</p>
                <p className="text-sm font-medium">{user.phone}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Mail className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Email</p>
                <p className="text-sm font-medium">{user.email}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <MapPin className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Location</p>
                <p className="text-sm font-medium">{user.location}</p>
              </div>
            </div>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}