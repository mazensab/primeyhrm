"use client"

// ============================================================
// 📂 الملف: components/whatsapp/chat-footer.tsx
// 🟢 Mham Cloud - WhatsApp Chat Footer
// ------------------------------------------------------------
// ✅ إزالة البطاقة الخارجية المحيطة بالفوتر
// ✅ جعل الفوتر أقرب للمرجع المدفوع
// ✅ الحفاظ على نفس الربط والسلوك الحالي
// ✅ تخفيف سماكة الحقل والأزرار
// ============================================================

import { KeyboardEvent } from "react"
import { Mic, Paperclip, PlusCircleIcon, SmileIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

type ChatFooterTranslations = {
  composerPlaceholder: string
  send: string
  comingSoon: string
}

type ChatFooterProps = {
  value: string
  disabled?: boolean
  sending?: boolean
  t: ChatFooterTranslations
  onChange: (value: string) => void
  onSend: () => void
}

export default function ChatFooter({
  value,
  disabled = false,
  sending = false,
  t,
  onChange,
  onSend,
}: ChatFooterProps) {
  const safeValue = value ?? ""
  const canSend = !disabled && !sending && safeValue.trim().length > 0

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      if (canSend) onSend()
    }
  }

  return (
    <div className="relative flex items-center">
      <Input
        type="text"
        value={safeValue}
        disabled={disabled || sending}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={t.composerPlaceholder}
        className="h-9 rounded-xl border px-3 !text-[13px] !shadow-none pe-28 lg:h-10 lg:pe-44"
      />

      <div className="absolute end-2 flex items-center">
        <div className="block lg:hidden">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                className="h-8 w-8 rounded-full p-0"
                disabled={disabled || sending}
              >
                <PlusCircleIcon className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>

            <DropdownMenuContent>
              <DropdownMenuSeparator />
              <DropdownMenuItem>{t.comingSoon}: Emoji</DropdownMenuItem>
              <DropdownMenuItem>{t.comingSoon}: Add File</DropdownMenuItem>
              <DropdownMenuItem>{t.comingSoon}: Send Voice</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="hidden lg:block">
          <TooltipProvider>
            <div className="flex items-center">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    className="h-8 w-8 rounded-full p-0"
                    disabled={disabled || sending}
                  >
                    <SmileIcon className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top">Emoji</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    className="h-8 w-8 rounded-full p-0"
                    disabled={disabled || sending}
                  >
                    <Paperclip className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top">Select File</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    className="h-8 w-8 rounded-full p-0"
                    disabled={disabled || sending}
                  >
                    <Mic className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="top">Send Voice</TooltipContent>
              </Tooltip>
            </div>
          </TooltipProvider>
        </div>

        <Button
          type="button"
          variant="outline"
          className="ms-2 h-8 rounded-lg px-3 text-[13px] shadow-none"
          disabled={!canSend}
          onClick={onSend}
        >
          {sending ? "..." : t.send}
        </Button>
      </div>
    </div>
  )
}