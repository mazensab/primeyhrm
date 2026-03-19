"use client"

import * as React from "react"
import { CheckIcon, ChevronDownIcon, XIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupInput,
} from "@/components/ui/input-group"

type ComboboxValueType = string | string[] | null

type ComboboxContextType = {
  open: boolean
  setOpen: React.Dispatch<React.SetStateAction<boolean>>
  value: ComboboxValueType
  setValue: (value: ComboboxValueType) => void
  search: string
  setSearch: React.Dispatch<React.SetStateAction<string>>
  multiple: boolean
  anchorRef: React.RefObject<HTMLDivElement | null>
}

const ComboboxContext = React.createContext<ComboboxContextType | null>(null)

function useComboboxContext() {
  const context = React.useContext(ComboboxContext)

  if (!context) {
    throw new Error("Combobox components must be used within <Combobox />")
  }

  return context
}

type ComboboxRootProps = Omit<
  React.ComponentProps<"div">,
  "defaultValue" | "value" | "onChange"
> & {
  value?: ComboboxValueType
  defaultSelectedValue?: ComboboxValueType
  onValueChange?: (value: ComboboxValueType) => void
  open?: boolean
  defaultOpen?: boolean
  onOpenChange?: (open: boolean) => void
  multiple?: boolean
}

function Combobox({
  className,
  children,
  value,
  defaultSelectedValue = null,
  onValueChange,
  open,
  defaultOpen = false,
  onOpenChange,
  multiple = false,
  ...props
}: ComboboxRootProps) {
  const [internalOpen, setInternalOpen] = React.useState(defaultOpen)
  const [internalValue, setInternalValue] =
    React.useState<ComboboxValueType>(defaultSelectedValue)
  const [search, setSearch] = React.useState("")
  const anchorRef = React.useRef<HTMLDivElement | null>(null)

  const resolvedOpen = open ?? internalOpen
  const resolvedValue = value ?? internalValue

  const setOpen = React.useCallback(
    (next: React.SetStateAction<boolean>) => {
      const nextValue = typeof next === "function" ? next(resolvedOpen) : next
      if (open === undefined) {
        setInternalOpen(nextValue)
      }
      onOpenChange?.(nextValue)
    },
    [open, onOpenChange, resolvedOpen]
  )

  const setValue = React.useCallback(
    (nextValue: ComboboxValueType) => {
      if (value === undefined) {
        setInternalValue(nextValue)
      }
      onValueChange?.(nextValue)
    },
    [value, onValueChange]
  )

  return (
    <ComboboxContext.Provider
      value={{
        open: resolvedOpen,
        setOpen,
        value: resolvedValue,
        setValue,
        search,
        setSearch,
        multiple,
        anchorRef,
      }}
    >
      <div
        data-slot="combobox"
        className={cn("relative", className)}
        {...props}
      >
        {children}
      </div>
    </ComboboxContext.Provider>
  )
}

function ComboboxValue({
  className,
  placeholder = "Select...",
  ...props
}: React.ComponentProps<"span"> & {
  placeholder?: React.ReactNode
}) {
  const { value } = useComboboxContext()

  const content = React.useMemo(() => {
    if (Array.isArray(value)) {
      return value.length ? value.join(", ") : placeholder
    }

    if (value === null || value === undefined || value === "") {
      return placeholder
    }

    return value
  }, [value, placeholder])

  return (
    <span
      data-slot="combobox-value"
      className={cn("truncate", className)}
      {...props}
    >
      {content}
    </span>
  )
}

function ComboboxTrigger({
  className,
  children,
  onClick,
  ...props
}: React.ComponentProps<"button">) {
  const { open, setOpen } = useComboboxContext()

  return (
    <button
      type="button"
      data-slot="combobox-trigger"
      aria-expanded={open}
      className={cn(
        "[&_svg:not([class*='size-'])]:size-4 inline-flex items-center gap-2",
        className
      )}
      onClick={(event) => {
        onClick?.(event)
        if (!event.defaultPrevented) {
          setOpen((prev) => !prev)
        }
      }}
      {...props}
    >
      {children}
      <ChevronDownIcon
        data-slot="combobox-trigger-icon"
        className="text-muted-foreground pointer-events-none size-4"
      />
    </button>
  )
}

function ComboboxClear({
  className,
  onClick,
  ...props
}: React.ComponentProps<"button">) {
  const { multiple, setValue, setSearch } = useComboboxContext()

  return (
    <button
      type="button"
      data-slot="combobox-clear"
      className={cn(className)}
      onClick={(event) => {
        onClick?.(event)
        if (!event.defaultPrevented) {
          setValue(multiple ? [] : null)
          setSearch("")
        }
      }}
      {...props}
    >
      <XIcon className="pointer-events-none size-4" />
    </button>
  )
}

function ComboboxInput({
  className,
  children,
  disabled = false,
  showTrigger = true,
  showClear = false,
  onChange,
  ...props
}: React.ComponentProps<"input"> & {
  showTrigger?: boolean
  showClear?: boolean
}) {
  const { setSearch, setOpen, anchorRef } = useComboboxContext()

  return (
    <div ref={anchorRef} className={cn("w-auto", className)}>
      <InputGroup className="w-auto">
        <InputGroupInput
          disabled={disabled}
          data-slot="combobox-input"
          onFocus={() => setOpen(true)}
          onChange={(event) => {
            setSearch(event.target.value)
            onChange?.(event)
          }}
          {...props}
        />
        <InputGroupAddon align="inline-end">
          {showTrigger && (
            <InputGroupButton
              size="icon-xs"
              variant="ghost"
              asChild
              data-slot="input-group-button"
              className="data-pressed:bg-transparent"
              disabled={disabled}
            >
              <ComboboxTrigger />
            </InputGroupButton>
          )}
          {showClear && (
            <ComboboxClear
              disabled={disabled}
              className="inline-flex items-center justify-center"
            />
          )}
        </InputGroupAddon>
        {children}
      </InputGroup>
    </div>
  )
}

function ComboboxContent({
  className,
  children,
  ...props
}: React.ComponentProps<"div"> & {
  side?: "top" | "right" | "bottom" | "left"
  sideOffset?: number
  align?: "start" | "center" | "end"
  alignOffset?: number
  anchor?: unknown
}) {
  const { open } = useComboboxContext()

  if (!open) {
    return null
  }

  return (
    <div className="absolute top-full left-0 z-50 mt-1 w-full">
      <div
        data-slot="combobox-content"
        className={cn(
          "bg-popover text-popover-foreground ring-foreground/10 relative max-h-96 min-w-full overflow-hidden rounded-md shadow-md ring-1 duration-100",
          className
        )}
        {...props}
      >
        {children}
      </div>
    </div>
  )
}

function ComboboxList({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) {
  const { search } = useComboboxContext()

  return (
    <div
      data-slot="combobox-list"
      data-empty={React.Children.count(children) === 0 || undefined}
      data-search={search || undefined}
      className={cn(
        "max-h-[calc(24rem-2.25rem)] overflow-y-auto p-1",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

function ComboboxItem({
  className,
  children,
  value,
  onClick,
  ...props
}: React.ComponentProps<"button"> & {
  value: string
}) {
  const { value: selectedValue, setValue, setOpen, multiple } =
    useComboboxContext()

  const isSelected = Array.isArray(selectedValue)
    ? selectedValue.includes(value)
    : selectedValue === value

  return (
    <button
      type="button"
      data-slot="combobox-item"
      data-selected={isSelected ? "true" : undefined}
      className={cn(
        "data-[selected=true]:bg-accent data-[selected=true]:text-accent-foreground relative flex w-full cursor-default items-center gap-2 rounded-sm py-1.5 pr-8 pl-2 text-sm outline-hidden select-none hover:bg-accent hover:text-accent-foreground disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      onClick={(event) => {
        onClick?.(event)

        if (event.defaultPrevented) {
          return
        }

        if (multiple) {
          const current = Array.isArray(selectedValue) ? selectedValue : []
          const next = current.includes(value)
            ? current.filter((item) => item !== value)
            : [...current, value]
          setValue(next)
        } else {
          setValue(value)
          setOpen(false)
        }
      }}
      {...props}
    >
      {children}
      {isSelected ? (
        <span
          data-slot="combobox-item-indicator"
          className="pointer-events-none absolute right-2 flex size-4 items-center justify-center"
        >
          <CheckIcon className="pointer-events-none size-4" />
        </span>
      ) : null}
    </button>
  )
}

function ComboboxGroup({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div data-slot="combobox-group" className={cn(className)} {...props}>
      {children}
    </div>
  )
}

function ComboboxLabel({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="combobox-label"
      className={cn(
        "text-muted-foreground px-2 py-1.5 text-xs pointer-coarse:px-3 pointer-coarse:py-2 pointer-coarse:text-sm",
        className
      )}
      {...props}
    />
  )
}

function ComboboxCollection({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="combobox-collection"
      className={cn(className)}
      {...props}
    >
      {children}
    </div>
  )
}

function ComboboxEmpty({
  className,
  children = "No results found.",
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="combobox-empty"
      className={cn(
        "text-muted-foreground flex w-full justify-center py-2 text-center text-sm",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

function ComboboxSeparator({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="combobox-separator"
      className={cn("bg-border -mx-1 my-1 h-px", className)}
      {...props}
    />
  )
}

function ComboboxChips({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) {
  const { anchorRef } = useComboboxContext()

  return (
    <div
      ref={anchorRef}
      data-slot="combobox-chips"
      className={cn(
        "dark:bg-input/30 border-input focus-within:border-ring focus-within:ring-ring/50 flex min-h-9 flex-wrap items-center gap-1.5 rounded-md border bg-transparent bg-clip-padding px-2.5 py-1.5 text-sm shadow-xs transition-[color,box-shadow] focus-within:ring-[3px]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

function ComboboxChip({
  className,
  children,
  showRemove = true,
  value,
  ...props
}: React.ComponentProps<"div"> & {
  showRemove?: boolean
  value?: string
}) {
  const { value: selectedValue, setValue, multiple } = useComboboxContext()

  const handleRemove = () => {
    if (!multiple || !value) return
    const current = Array.isArray(selectedValue) ? selectedValue : []
    setValue(current.filter((item) => item !== value))
  }

  return (
    <div
      data-slot="combobox-chip"
      className={cn(
        "bg-muted text-foreground flex h-[calc(--spacing(5.5))] w-fit items-center justify-center gap-1 rounded-sm px-1.5 text-xs font-medium whitespace-nowrap has-disabled:pointer-events-none has-disabled:cursor-not-allowed has-disabled:opacity-50",
        className
      )}
      {...props}
    >
      {children}
      {showRemove && (
        <Button
          type="button"
          variant="ghost"
          size="icon-xs"
          className="-ml-1 opacity-50 hover:opacity-100"
          data-slot="combobox-chip-remove"
          onClick={handleRemove}
        >
          <XIcon className="pointer-events-none size-4" />
        </Button>
      )}
    </div>
  )
}

function ComboboxChipsInput({
  className,
  onChange,
  onFocus,
  ...props
}: React.ComponentProps<"input">) {
  const { setSearch, setOpen } = useComboboxContext()

  return (
    <input
      data-slot="combobox-chip-input"
      className={cn("min-w-16 flex-1 bg-transparent outline-none", className)}
      onFocus={(event) => {
        setOpen(true)
        onFocus?.(event)
      }}
      onChange={(event) => {
        setSearch(event.target.value)
        onChange?.(event)
      }}
      {...props}
    />
  )
}

function useComboboxAnchor() {
  return React.useRef<HTMLDivElement | null>(null)
}

export {
  Combobox,
  ComboboxInput,
  ComboboxContent,
  ComboboxList,
  ComboboxItem,
  ComboboxGroup,
  ComboboxLabel,
  ComboboxCollection,
  ComboboxEmpty,
  ComboboxSeparator,
  ComboboxChips,
  ComboboxChip,
  ComboboxChipsInput,
  ComboboxTrigger,
  ComboboxValue,
  useComboboxAnchor,
}