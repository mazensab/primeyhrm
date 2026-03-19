"use client"

import * as React from "react"
import { MinusIcon } from "lucide-react"

import { cn } from "@/lib/utils"

type SlotState = {
  char: string
  isActive: boolean
  hasFakeCaret: boolean
}

type InputOTPContextValue = {
  slots: SlotState[]
  value: string
  maxLength: number
  disabled?: boolean
  setFocusedIndex: (index: number) => void
  handleSlotChange: (index: number, nextChar: string) => void
  handleSlotKeyDown: (index: number, e: React.KeyboardEvent<HTMLInputElement>) => void
  handleSlotPaste: (index: number, e: React.ClipboardEvent<HTMLInputElement>) => void
}

const InputOTPContext = React.createContext<InputOTPContextValue | null>(null)

type InputOTPProps = Omit<React.ComponentProps<"div">, "onChange"> & {
  value?: string
  onChange?: (value: string) => void
  maxLength: number
  disabled?: boolean
  containerClassName?: string
  pattern?: string
  children: React.ReactNode
}

function InputOTP({
  className,
  containerClassName,
  value = "",
  onChange,
  maxLength,
  disabled,
  children,
  ...props
}: InputOTPProps) {
  const [focusedIndex, setFocusedIndex] = React.useState(0)

  const normalizedValue = React.useMemo(() => {
    return (value ?? "").slice(0, maxLength)
  }, [value, maxLength])

  const slots = React.useMemo<SlotState[]>(() => {
    return Array.from({ length: maxLength }, (_, index) => {
      const char = normalizedValue[index] ?? ""
      const isActive = focusedIndex === index
      const hasFakeCaret = isActive && !char

      return {
        char,
        isActive,
        hasFakeCaret,
      }
    })
  }, [focusedIndex, maxLength, normalizedValue])

  const updateValueAt = React.useCallback(
    (index: number, nextChar: string) => {
      const chars = Array.from({ length: maxLength }, (_, i) => normalizedValue[i] ?? "")
      chars[index] = nextChar
      const nextValue = chars.join("").slice(0, maxLength)
      onChange?.(nextValue)
    },
    [maxLength, normalizedValue, onChange]
  )

  const handleSlotChange = React.useCallback(
    (index: number, nextChar: string) => {
      if (disabled) return

      const char = nextChar.slice(-1)

      if (!char) {
        updateValueAt(index, "")
        return
      }

      updateValueAt(index, char)

      if (index < maxLength - 1) {
        setFocusedIndex(index + 1)
      }
    },
    [disabled, maxLength, updateValueAt]
  )

  const handleSlotKeyDown = React.useCallback(
    (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
      if (disabled) return

      if (e.key === "Backspace") {
        e.preventDefault()

        if (normalizedValue[index]) {
          updateValueAt(index, "")
          return
        }

        if (index > 0) {
          updateValueAt(index - 1, "")
          setFocusedIndex(index - 1)
        }
        return
      }

      if (e.key === "ArrowLeft") {
        e.preventDefault()
        if (index > 0) setFocusedIndex(index - 1)
        return
      }

      if (e.key === "ArrowRight") {
        e.preventDefault()
        if (index < maxLength - 1) setFocusedIndex(index + 1)
      }
    },
    [disabled, maxLength, normalizedValue, updateValueAt]
  )

  const handleSlotPaste = React.useCallback(
    (index: number, e: React.ClipboardEvent<HTMLInputElement>) => {
      if (disabled) return

      e.preventDefault()
      const pasted = e.clipboardData.getData("text").replace(/\s+/g, "")
      if (!pasted) return

      const chars = Array.from({ length: maxLength }, (_, i) => normalizedValue[i] ?? "")
      let cursor = index

      for (const ch of pasted) {
        if (cursor >= maxLength) break
        chars[cursor] = ch
        cursor += 1
      }

      onChange?.(chars.join("").slice(0, maxLength))
      setFocusedIndex(Math.min(cursor, maxLength - 1))
    },
    [disabled, maxLength, normalizedValue, onChange]
  )

  const contextValue = React.useMemo<InputOTPContextValue>(
    () => ({
      slots,
      value: normalizedValue,
      maxLength,
      disabled,
      setFocusedIndex,
      handleSlotChange,
      handleSlotKeyDown,
      handleSlotPaste,
    }),
    [
      slots,
      normalizedValue,
      maxLength,
      disabled,
      handleSlotChange,
      handleSlotKeyDown,
      handleSlotPaste,
    ]
  )

  return (
    <InputOTPContext.Provider value={contextValue}>
      <div
        data-slot="input-otp"
        className={cn("disabled:cursor-not-allowed", className)}
        {...props}
      >
        <div
          className={cn(
            "flex items-center gap-2 has-disabled:opacity-50",
            containerClassName
          )}
        >
          {children}
        </div>
      </div>
    </InputOTPContext.Provider>
  )
}

function InputOTPGroup({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="input-otp-group"
      className={cn("flex items-center", className)}
      {...props}
    />
  )
}

function InputOTPSlot({
  index,
  className,
  ...props
}: React.ComponentProps<"div"> & {
  index: number
}) {
  const inputOTPContext = React.useContext(InputOTPContext)

  if (!inputOTPContext) {
    throw new Error("InputOTPSlot must be used within <InputOTP />")
  }

  const { char, hasFakeCaret, isActive } = inputOTPContext.slots[index] ?? {
    char: "",
    hasFakeCaret: false,
    isActive: false,
  }

  return (
    <div
      data-slot="input-otp-slot"
      data-active={isActive}
      className={cn(
        "data-[active=true]:border-ring data-[active=true]:ring-ring/50 data-[active=true]:aria-invalid:ring-destructive/20 dark:data-[active=true]:aria-invalid:ring-destructive/40 aria-invalid:border-destructive data-[active=true]:aria-invalid:border-destructive dark:bg-input/30 border-input relative flex h-9 w-9 items-center justify-center border-y border-r text-sm shadow-xs transition-all outline-none first:rounded-l-md first:border-l last:rounded-r-md data-[active=true]:z-10 data-[active=true]:ring-[3px]",
        className
      )}
      {...props}
    >
      <input
        value={char}
        disabled={inputOTPContext.disabled}
        onFocus={() => inputOTPContext.setFocusedIndex(index)}
        onChange={(e) => inputOTPContext.handleSlotChange(index, e.target.value)}
        onKeyDown={(e) => inputOTPContext.handleSlotKeyDown(index, e)}
        onPaste={(e) => inputOTPContext.handleSlotPaste(index, e)}
        inputMode="numeric"
        autoComplete="one-time-code"
        className="absolute inset-0 h-full w-full cursor-text border-0 bg-transparent text-center text-transparent caret-transparent outline-none"
        aria-label={`OTP digit ${index + 1}`}
      />

      <span aria-hidden="true">{char}</span>

      {hasFakeCaret && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="animate-caret-blink bg-foreground h-4 w-px duration-1000" />
        </div>
      )}
    </div>
  )
}

function InputOTPSeparator({ ...props }: React.ComponentProps<"div">) {
  return (
    <div data-slot="input-otp-separator" role="separator" {...props}>
      <MinusIcon />
    </div>
  )
}

export { InputOTP, InputOTPContext, InputOTPGroup, InputOTPSlot, InputOTPSeparator }