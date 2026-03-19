"use client";

import { cn } from "@/lib/utils";
import React from "react";

export type CodeBlockProps = {
  children?: React.ReactNode;
  className?: string;
} & React.HTMLProps<HTMLDivElement>;

function CodeBlock({ children, className, ...props }: CodeBlockProps) {
  return (
    <div
      className={cn(
        "not-prose flex w-full flex-col overflow-clip rounded-xl border",
        "border-border bg-card text-card-foreground",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export type CodeBlockCodeProps = {
  code: string;
  language?: string;
  theme?: string;
  className?: string;
} & React.HTMLProps<HTMLDivElement>;

function CodeBlockCode({
  code,
  language = "tsx",
  className,
  ...props
}: CodeBlockCodeProps) {
  const classNames = cn(
    "w-full overflow-x-auto text-[13px]",
    "[&>pre]:min-w-full [&>pre]:px-4 [&>pre]:py-4",
    className
  );

  return (
    <div className={classNames} {...props}>
      <pre className="bg-transparent">
        <code className={cn("font-mono", language ? `language-${language}` : "")}>
          {code}
        </code>
      </pre>
    </div>
  );
}

export type CodeBlockGroupProps = React.HTMLAttributes<HTMLDivElement>;

function CodeBlockGroup({ children, className, ...props }: CodeBlockGroupProps) {
  return (
    <div className={cn("flex items-center justify-between", className)} {...props}>
      {children}
    </div>
  );
}

export { CodeBlockGroup, CodeBlockCode, CodeBlock };