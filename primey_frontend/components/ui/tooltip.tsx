"use client"

import * as React from "react"
import * as TooltipPrimitive from "@radix-ui/react-tooltip"

import { cn } from "@/lib/utils"

/* ======================================================
   Tooltip Provider
====================================================== */

function TooltipProvider({
  delayDuration = 0,
  ...props
}: React.ComponentProps<typeof TooltipPrimitive.Provider>) {
  return (
    <TooltipPrimitive.Provider
      delayDuration={delayDuration}
      {...props}
    />
  )
}

/* ======================================================
   Tooltip Root
====================================================== */

const Tooltip = TooltipPrimitive.Root

/* ======================================================
   ✅ FIX — forwardRef REQUIRED for asChild
====================================================== */

const TooltipTrigger = React.forwardRef<
  React.ElementRef<typeof TooltipPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Trigger>
>(({ ...props }, ref) => {
  return <TooltipPrimitive.Trigger ref={ref} {...props} />
})

TooltipTrigger.displayName = "TooltipTrigger"

/* ======================================================
   Tooltip Content
====================================================== */

const TooltipContent = React.forwardRef<
  React.ElementRef<typeof TooltipPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>
>(({ className, sideOffset = 4, children, ...props }, ref) => {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Content
        ref={ref}
        sideOffset={sideOffset}
        className={cn(
          "z-50 rounded-md bg-foreground px-3 py-1.5 text-xs text-background animate-in fade-in-0 zoom-in-95",
          className
        )}
        {...props}
      >
        {children}
        <TooltipPrimitive.Arrow className="fill-foreground" />
      </TooltipPrimitive.Content>
    </TooltipPrimitive.Portal>
  )
})

TooltipContent.displayName = "TooltipContent"

/* ====================================================== */

export {
  Tooltip,
  TooltipTrigger,
  TooltipContent,
  TooltipProvider,
}