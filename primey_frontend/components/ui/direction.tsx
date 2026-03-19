"use client"

import * as React from "react"
import * as DirectionPrimitive from "@radix-ui/react-direction"

function DirectionProvider({
  dir,
  direction,
  children,
}: React.ComponentProps<typeof DirectionPrimitive.Provider> & {
  direction?: React.ComponentProps<typeof DirectionPrimitive.Provider>["dir"]
}) {
  return (
    <DirectionPrimitive.Provider dir={direction ?? dir}>
      {children}
    </DirectionPrimitive.Provider>
  )
}

export { DirectionProvider }