"use client"

// ============================================================
// 📂 الملف: components/whatsapp/chat-list-item-dropdown.tsx
// 🟢 Primey HR Cloud - WhatsApp Chat List Item Dropdown
// ============================================================

import { Archive, BellOff, MoreHorizontal, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export default function ChatListItemDropdown() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-8 w-8 rounded-full"
        >
          <MoreHorizontal className="h-4 w-4" />
        </Button>
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