"use client"

import * as React from "react"
import type { DateRange } from "react-day-picker"
import { CalendarIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useIsMobile } from "@/hooks/use-mobile"

const dateFilterPresets = [
  { name: "Today", value: "today" },
  { name: "Yesterday", value: "yesterday" },
  { name: "This Week", value: "thisWeek" },
  { name: "Last 7 Days", value: "last7Days" },
  { name: "Last 28 Days", value: "last28Days" },
  { name: "This Month", value: "thisMonth" },
  { name: "Last Month", value: "lastMonth" },
  { name: "This Year", value: "thisYear" },
] as const

function cloneDate(date: Date) {
  return new Date(date.getTime())
}

function startOfDay(date: Date) {
  const d = cloneDate(date)
  d.setHours(0, 0, 0, 0)
  return d
}

function endOfDay(date: Date) {
  const d = cloneDate(date)
  d.setHours(23, 59, 59, 999)
  return d
}

function subDays(date: Date, days: number) {
  const d = cloneDate(date)
  d.setDate(d.getDate() - days)
  return d
}

function startOfMonth(date: Date) {
  const d = cloneDate(date)
  d.setDate(1)
  d.setHours(0, 0, 0, 0)
  return d
}

function endOfMonth(date: Date) {
  const d = new Date(date.getFullYear(), date.getMonth() + 1, 0)
  d.setHours(23, 59, 59, 999)
  return d
}

function subMonths(date: Date, months: number) {
  const d = cloneDate(date)
  const currentDay = d.getDate()

  d.setDate(1)
  d.setMonth(d.getMonth() - months)

  const lastDayOfTargetMonth = new Date(
    d.getFullYear(),
    d.getMonth() + 1,
    0
  ).getDate()

  d.setDate(Math.min(currentDay, lastDayOfTargetMonth))
  return d
}

function startOfYear(date: Date) {
  const d = new Date(date.getFullYear(), 0, 1)
  d.setHours(0, 0, 0, 0)
  return d
}

function startOfWeek(date: Date) {
  const d = startOfDay(date)
  const day = d.getDay()
  d.setDate(d.getDate() - day)
  return d
}

function formatDate(date: Date, withMonthName = true) {
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: withMonthName ? "short" : "2-digit",
    year: "numeric",
  }).format(date)
}

export default function CalendarDateRangePicker({
  className,
}: React.HTMLAttributes<HTMLDivElement>) {
  const isMobile = useIsMobile()
  const today = new Date()
  const twentyEightDaysAgo = startOfDay(subDays(today, 27))

  const [date, setDate] = React.useState<DateRange | undefined>({
    from: twentyEightDaysAgo,
    to: endOfDay(today),
  })
  const [open, setOpen] = React.useState(false)
  const [currentMonth, setCurrentMonth] = React.useState<Date>(new Date())

  const handleQuickSelect = (from: Date, to: Date) => {
    setDate({ from, to })
    setCurrentMonth(from)
  }

  const changeHandle = (type: string) => {
    const now = new Date()

    switch (type) {
      case "today": {
        handleQuickSelect(startOfDay(now), endOfDay(now))
        break
      }

      case "yesterday": {
        const yesterday = subDays(now, 1)
        handleQuickSelect(startOfDay(yesterday), endOfDay(yesterday))
        break
      }

      case "thisWeek": {
        const startOfCurrentWeek = startOfWeek(now)
        handleQuickSelect(startOfDay(startOfCurrentWeek), endOfDay(now))
        break
      }

      case "last7Days": {
        const sevenDaysAgo = subDays(now, 6)
        handleQuickSelect(startOfDay(sevenDaysAgo), endOfDay(now))
        break
      }

      case "last28Days": {
        const last28DaysStart = subDays(now, 27)
        handleQuickSelect(startOfDay(last28DaysStart), endOfDay(now))
        break
      }

      case "thisMonth": {
        handleQuickSelect(startOfMonth(now), endOfDay(now))
        break
      }

      case "lastMonth": {
        const lastMonth = subMonths(now, 1)
        handleQuickSelect(startOfMonth(lastMonth), endOfMonth(lastMonth))
        break
      }

      case "thisYear": {
        const startOfCurrentYear = startOfYear(now)
        handleQuickSelect(startOfDay(startOfCurrentYear), endOfDay(now))
        break
      }

      default:
        break
    }
  }

  const renderDateLabel = () => {
    if (!date?.from) {
      return <span>Select date range</span>
    }

    if (date.to) {
      return (
        <>
          {formatDate(date.from)} - {formatDate(date.to)}
        </>
      )
    }

    return formatDate(date.from)
  }

  return (
    <div className={cn("grid gap-2", className)}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          {isMobile ? (
            <div>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      id="date"
                      variant="outline"
                      className={cn(
                        "justify-start text-left font-normal",
                        !date && "text-muted-foreground"
                      )}
                    >
                      <CalendarIcon />
                    </Button>
                  </TooltipTrigger>

                  <TooltipContent>{renderDateLabel()}</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          ) : (
            <Button
              id="date"
              variant="outline"
              className={cn(
                "justify-start text-left font-normal",
                !date && "text-muted-foreground"
              )}
            >
              <CalendarIcon />
              {renderDateLabel()}
            </Button>
          )}
        </PopoverTrigger>

        <PopoverContent className="w-auto" align="end">
          <div className="flex flex-col lg:flex-row">
            <div className="me-0 lg:me-4">
              <ToggleGroup
                type="single"
                defaultValue="last28Days"
                className="hidden w-28 flex-col lg:block"
              >
                {dateFilterPresets.map((item) => (
                  <ToggleGroupItem
                    key={item.value}
                    className="text-muted-foreground w-full"
                    value={item.value}
                    onClick={() => changeHandle(item.value)}
                    asChild
                  >
                    <Button className="justify-start rounded-md">
                      {item.name}
                    </Button>
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>

              <Select
                defaultValue="last28Days"
                onValueChange={(value) => changeHandle(value)}
              >
                <SelectTrigger
                  className="mb-4 flex w-full lg:hidden"
                  size="sm"
                  aria-label="Select a value"
                >
                  <SelectValue placeholder="Last 28 Days" />
                </SelectTrigger>

                <SelectContent>
                  {dateFilterPresets.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Calendar
              className="border-s-0 py-0! ps-0! pe-0! lg:border-s lg:ps-4!"
              mode="range"
              month={currentMonth}
              selected={date}
              onSelect={(newDate) => {
                setDate(newDate)
                if (newDate?.from) {
                  setCurrentMonth(newDate.from)
                }
              }}
              onMonthChange={setCurrentMonth}
            />
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}