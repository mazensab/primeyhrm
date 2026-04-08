"use client"

// ============================================================
// 📂 الملف: components/whatsapp/chat-list-item-dropdown.tsx
// 🟢 Mham Cloud - WhatsApp Chat List Item Dropdown
// ------------------------------------------------------------
// ✅ دعم children لاستخدام زر مخصص من الخارج
// ✅ الحفاظ على الزر الافتراضي عند عدم تمرير children
// ✅ متوافق مع استخدامه الحالي داخل chat-list-item.tsx
// ============================================================

import type { ReactNode } from "react"
import { Archive, BellOff, MoreHorizontal, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

type ChatListItemDropdownProps = {
  children?: ReactNode
}

export default function ChatListItemDropdown({
  children,
}: ChatListItemDropdownProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        {children ? (
          children
        ) : (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-8 w-8 rounded-full"
          >
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        )}
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-44">
        <DropdownMenuItem>View profile</DropdownMenuItem>

        <DropdownMenuItem>
          <BellOff className="me-2 h-4 w-4" />
          Mute
        </DropdownMenuItem>

        <DropdownMenuItem>
          <Archive className="me-2 h-4 w-4" />
          Archive
        </DropdownMenuItem>

        <DropdownMenuItem className="text-destructive focus:text-destructive">
          <Trash2 className="me-2 h-4 w-4" />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}