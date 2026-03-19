"use client";

import * as React from "react";

import { CalendarIcon } from "@radix-ui/react-icons";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";

type Props = {
  date: Date | undefined;
  setDate: (value: Date | undefined) => void;
};

// ============================================================
// 🕒 تنسيق التاريخ والوقت بدون date-fns
// ============================================================
function formatDateTime(value: Date): string {
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  const year = value.getFullYear();

  let hours = value.getHours();
  const minutes = String(value.getMinutes()).padStart(2, "0");
  const ampm = hours >= 12 ? "PM" : "AM";

  hours = hours % 12;
  hours = hours === 0 ? 12 : hours;

  return `${month}/${day}/${year} ${String(hours).padStart(2, "0")}:${minutes} ${ampm}`;
}

// ============================================================
// 🕒 مساعدات التعامل مع الوقت
// ============================================================
function to12Hour(hour24: number): number {
  const hour = hour24 % 12;
  return hour === 0 ? 12 : hour;
}

function isPM(hour24: number): boolean {
  return hour24 >= 12;
}

export function DateTimePicker({ date, setDate }: Props) {
  const [isOpen, setIsOpen] = React.useState(false);

  const hours = React.useMemo(() => Array.from({ length: 12 }, (_, i) => i + 1).reverse(), []);

  const handleDateSelect = (selectedDate: Date | undefined) => {
    if (!selectedDate) return;

    if (!date) {
      setDate(selectedDate);
      return;
    }

    const mergedDate = new Date(selectedDate);
    mergedDate.setHours(date.getHours(), date.getMinutes(), 0, 0);
    setDate(mergedDate);
  };

  const handleTimeChange = (type: "hour" | "minute" | "ampm", value: string) => {
    const baseDate = date ? new Date(date) : new Date();

    if (type === "hour") {
      const selectedHour12 = Number.parseInt(value, 10);
      if (Number.isNaN(selectedHour12)) return;

      const currentIsPM = isPM(baseDate.getHours());
      let nextHour24 = selectedHour12 % 12;

      if (currentIsPM) {
        nextHour24 += 12;
      }

      baseDate.setHours(nextHour24);
    }

    if (type === "minute") {
      const selectedMinute = Number.parseInt(value, 10);
      if (Number.isNaN(selectedMinute)) return;

      baseDate.setMinutes(selectedMinute);
    }

    if (type === "ampm") {
      const currentHour = baseDate.getHours();

      if (value === "AM" && currentHour >= 12) {
        baseDate.setHours(currentHour - 12);
      }

      if (value === "PM" && currentHour < 12) {
        baseDate.setHours(currentHour + 12);
      }
    }

    baseDate.setSeconds(0, 0);
    setDate(baseDate);
  };

  const selectedHour12 = date ? to12Hour(date.getHours()) : undefined;
  const selectedMinute = date ? date.getMinutes() : undefined;
  const selectedIsPM = date ? isPM(date.getHours()) : false;

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen} modal>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "w-full justify-start text-left font-normal",
            !date && "text-muted-foreground"
          )}
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {date ? <span>{formatDateTime(date)}</span> : <span>MM/DD/YYYY hh:mm aa</span>}
        </Button>
      </PopoverTrigger>

      <PopoverContent className="w-auto p-0">
        <div className="sm:flex">
          <Calendar mode="single" selected={date} onSelect={handleDateSelect} initialFocus />

          <div className="flex h-[300px] flex-col divide-y border-s sm:flex-row sm:divide-x sm:divide-y-0">
            {/* الساعات */}
            <ScrollArea className="w-64 sm:w-auto">
              <div className="flex p-2 sm:flex-col">
                {hours.map((hour) => (
                  <Button
                    key={hour}
                    size="icon"
                    variant={selectedHour12 === hour ? "default" : "ghost"}
                    className="aspect-square shrink-0 sm:w-full"
                    onClick={() => handleTimeChange("hour", hour.toString())}
                    type="button"
                  >
                    {hour}
                  </Button>
                ))}
              </div>
              <ScrollBar orientation="horizontal" className="sm:hidden" />
            </ScrollArea>

            {/* الدقائق */}
            <ScrollArea className="w-64 sm:w-auto">
              <div className="flex p-2 sm:flex-col">
                {Array.from({ length: 12 }, (_, i) => i * 5).map((minute) => (
                  <Button
                    key={minute}
                    size="icon"
                    variant={selectedMinute === minute ? "default" : "ghost"}
                    className="aspect-square shrink-0 sm:w-full"
                    onClick={() => handleTimeChange("minute", minute.toString())}
                    type="button"
                  >
                    {String(minute).padStart(2, "0")}
                  </Button>
                ))}
              </div>
              <ScrollBar orientation="horizontal" className="sm:hidden" />
            </ScrollArea>

            {/* AM / PM */}
            <ScrollArea>
              <div className="flex p-2 sm:flex-col">
                {["AM", "PM"].map((ampm) => {
                  const active =
                    date !== undefined &&
                    ((ampm === "AM" && !selectedIsPM) || (ampm === "PM" && selectedIsPM));

                  return (
                    <Button
                      key={ampm}
                      size="icon"
                      variant={active ? "default" : "ghost"}
                      className="aspect-square shrink-0 sm:w-full"
                      onClick={() => handleTimeChange("ampm", ampm)}
                      type="button"
                    >
                      {ampm}
                    </Button>
                  );
                })}
              </div>
            </ScrollArea>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}