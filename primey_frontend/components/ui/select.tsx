"use client"

import * as React from "react"
import * as SelectPrimitive from "@radix-ui/react-select"
import { CheckIcon, ChevronDownIcon, ChevronUpIcon } from "lucide-react"

import { cn } from "@/lib/utils"

/* -------------------------------------------------------------------------- */
/* Root                                                                       */
/* -------------------------------------------------------------------------- */

const Select = SelectPrimitive.Root
const SelectGroup = SelectPrimitive.Group
const SelectValue = SelectPrimitive.Value

/* -------------------------------------------------------------------------- */
/* Trigger                                                                    */
/* -------------------------------------------------------------------------- */

function SelectTrigger({
  className,
  size = "default",
  children,
  ...props
}: React.ComponentPropsWithoutRef<typeof SelectPrimitive.Trigger> & {
  size?: "sm" | "default"
}) {
  return (
    <SelectPrimitive.Trigger
      data-slot="select-trigger"
      data-size={size}
      className={cn(
        "border-input flex w-fit items-center justify-between gap-2 rounded-md border bg-transparent px-3 py-2 text-sm shadow-xs outline-none",
        "focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50",
        size === "default" && "h-9",
        size === "sm" && "h-8",
        className
      )}
      {...props}
    >
      {children}

      <SelectPrimitive.Icon asChild>
        <ChevronDownIcon className="size-4 opacity-50" />
      </SelectPrimitive.Icon>
    </SelectPrimitive.Trigger>
  )
}

/* -------------------------------------------------------------------------- */
/* Content                                                                    */
/* -------------------------------------------------------------------------- */

function SelectContent({
  className,
  children,
  position = "popper",
  ...props
}: React.ComponentPropsWithoutRef<typeof SelectPrimitive.Content>) {
  return (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Content
        data-slot="select-content"
        position={position}
        className={cn(
          "bg-popover text-popover-foreground relative z-50 min-w-[8rem] overflow-hidden rounded-md border shadow-md",
          className
        )}
        {...props}
      >
        <SelectScrollUpButton />

        <SelectPrimitive.Viewport className="p-1">
          {children}
        </SelectPrimitive.Viewport>

        <SelectScrollDownButton />
      </SelectPrimitive.Content>
    </SelectPrimitive.Portal>
  )
}

/* -------------------------------------------------------------------------- */
/* Label                                                                      */
/* -------------------------------------------------------------------------- */

function SelectLabel(
  props: React.ComponentPropsWithoutRef<typeof SelectPrimitive.Label>
) {
  return (
    <SelectPrimitive.Label
      className={cn("px-2 py-1.5 text-xs text-muted-foreground")}
      {...props}
    />
  )
}

/* -------------------------------------------------------------------------- */
/* Item                                                                       */
/* -------------------------------------------------------------------------- */

function SelectItem({
  className,
  children,
  ...props
}: React.ComponentPropsWithoutRef<typeof SelectPrimitive.Item>) {
  return (
    <SelectPrimitive.Item
      className={cn(
        "relative flex cursor-default select-none items-center rounded-sm py-1.5 pr-8 pl-2 text-sm",
        "focus:bg-accent focus:text-accent-foreground",
        className
      )}
      {...props}
    >
      <span className="absolute right-2 flex size-3.5 items-center justify-center">
        <SelectPrimitive.ItemIndicator>
          <CheckIcon className="size-4" />
        </SelectPrimitive.ItemIndicator>
      </span>

      <SelectPrimitive.ItemText>
        {children}
      </SelectPrimitive.ItemText>
    </SelectPrimitive.Item>
  )
}

/* -------------------------------------------------------------------------- */

function SelectSeparator(
  props: React.ComponentPropsWithoutRef<typeof SelectPrimitive.Separator>
) {
  return (
    <SelectPrimitive.Separator
      className="bg-border my-1 h-px"
      {...props}
    />
  )
}

function SelectScrollUpButton(
  props: React.ComponentPropsWithoutRef<
    typeof SelectPrimitive.ScrollUpButton
  >
) {
  return (
    <SelectPrimitive.ScrollUpButton
      className="flex items-center justify-center py-1"
      {...props}
    >
      <ChevronUpIcon className="size-4" />
    </SelectPrimitive.ScrollUpButton>
  )
}

function SelectScrollDownButton(
  props: React.ComponentPropsWithoutRef<
    typeof SelectPrimitive.ScrollDownButton
  >
) {
  return (
    <SelectPrimitive.ScrollDownButton
      className="flex items-center justify-center py-1"
      {...props}
    >
      <ChevronDownIcon className="size-4" />
    </SelectPrimitive.ScrollDownButton>
  )
}

/* -------------------------------------------------------------------------- */

export {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectScrollDownButton,
  SelectScrollUpButton,
  SelectValue,
}