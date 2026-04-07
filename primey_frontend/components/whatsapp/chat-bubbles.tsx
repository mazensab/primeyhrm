"use client"

import { Ellipsis } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

import MessageStatusIcon from "./message-status-icon"

// ============================================================
// 📂 الملف: components/whatsapp/chat-bubbles.tsx
// 🟢 Mham Cloud - WhatsApp Chat Bubbles
// ------------------------------------------------------------
// ✅ ضبط الفقاعات لتقترب من المرجع المدفوع
// ✅ تصحيح موضع زر الثلاث نقاط
// ✅ تحسين عرض الفقاعات وتموضع الوقت
// ✅ تحسين فقاعة الصور
// ============================================================

type ChatMessageProps = {
  id?: number
  own_message?: boolean
  content?: string
  data?: {
    images?: string[]
  }
}

function BubbleMenu() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-9 w-9 rounded-full text-muted-foreground shadow-none"
        >
          <Ellipsis className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-40">
        <DropdownMenuGroup>
          <DropdownMenuItem>Forward</DropdownMenuItem>
          <DropdownMenuItem>Star</DropdownMenuItem>
          <DropdownMenuItem>Delete</DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function BubbleMeta({ ownMessage }: { ownMessage?: boolean }) {
  return (
    <div
      className={cn(
        "mt-2 flex items-center gap-1.5 px-1 text-[12px] text-muted-foreground",
        ownMessage ? "justify-end" : "justify-start"
      )}
    >
      <time>05:23 PM</time>
      {ownMessage ? <MessageStatusIcon status="read" /> : null}
    </div>
  )
}

function TextChatBubble({ message }: { message: ChatMessageProps }) {
  const isOwn = Boolean(message.own_message)

  return (
    <div
      className={cn(
        "flex w-full flex-col",
        isOwn ? "items-end" : "items-start"
      )}
    >
      <div
        className={cn(
          "flex w-full items-end gap-2",
          isOwn ? "justify-end" : "justify-start"
        )}
      >
        {/* الرسالة الصادرة: القائمة على اليسار */}
        {isOwn ? <BubbleMenu /> : null}

        <Card
          className={cn(
            "border shadow-none",
            isOwn
              ? "max-w-[560px] rounded-[22px] bg-background"
              : "max-w-[620px] rounded-[22px] bg-background"
          )}
        >
          <CardContent className="px-5 py-4 text-[14px] leading-8">
            {message.content}
          </CardContent>
        </Card>

        {/* الرسالة الواردة: القائمة على اليمين */}
        {!isOwn ? <BubbleMenu /> : null}
      </div>

      <BubbleMeta ownMessage={isOwn} />
    </div>
  )
}

function ImageChatBubble({ message }: { message: ChatMessageProps }) {
  const isOwn = Boolean(message.own_message)
  const images = message?.data?.images ?? []

  return (
    <div
      className={cn(
        "flex w-full flex-col",
        isOwn ? "items-end" : "items-start"
      )}
    >
      <div
        className={cn(
          "flex w-full items-end gap-2",
          isOwn ? "justify-end" : "justify-start"
        )}
      >
        {isOwn ? <BubbleMenu /> : null}

        <Card className="max-w-[460px] rounded-[22px] border bg-background shadow-none">
          <CardContent className="p-3">
            <div
              className={cn("grid gap-2", {
                "grid-cols-1": images.length <= 1,
                "grid-cols-2": images.length > 1,
              })}
            >
              {images.map((image, key) => (
                <figure
                  key={key}
                  className="overflow-hidden rounded-[16px] bg-muted/20"
                >
                  <img
                    src={image}
                    alt={`message-media-${key + 1}`}
                    className="aspect-[4/3] h-full w-full object-cover"
                    loading="lazy"
                  />
                </figure>
              ))}
            </div>
          </CardContent>
        </Card>

        {!isOwn ? <BubbleMenu /> : null}
      </div>

      <BubbleMeta ownMessage={isOwn} />
    </div>
  )
}

export default function ChatBubble({
  message,
  type,
}: {
  message?: ChatMessageProps
  type?: string
}) {
  if (!message) return null

  switch (type) {
    case "image":
      return <ImageChatBubble message={message} />
    case "text":
    default:
      return <TextChatBubble message={message} />
  }
}