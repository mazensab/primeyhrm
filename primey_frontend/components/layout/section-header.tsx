import React from "react";
import { cn } from "@/lib/utils";

interface Props {
  title: string | React.ReactNode;
  subTitle?: string;
  description?: string | React.ReactNode;
  className?: string;
}

export default function SectionHeader({
  className,
  title,
  subTitle,
  description,
}: Props) {
  return (
    <header
      className={cn(
        "mx-auto mb-8 flex max-w-3xl flex-col items-center text-center lg:mb-12",
        className
      )}
    >
      {subTitle ? (
        <div className="mb-5 inline-flex items-center rounded-full border bg-background/80 px-4 py-2 text-sm font-medium tracking-normal text-foreground shadow-sm backdrop-blur-sm">
          {subTitle}
        </div>
      ) : null}

      <h2 className="max-w-4xl text-3xl font-bold leading-tight tracking-tight text-foreground sm:text-4xl md:text-5xl lg:text-6xl">
        {title}
      </h2>

      {description ? (
        <p className="text-muted-foreground mt-5 max-w-2xl text-base leading-8 sm:text-lg md:mt-6">
          {description}
        </p>
      ) : null}
    </header>
  );
}