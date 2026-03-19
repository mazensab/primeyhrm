"use client";

import { Slot } from "@radix-ui/react-slot";
import * as React from "react";

import { useComposedRefs } from "@/lib/compose-refs";
import { cn } from "@/lib/utils";

const ROOT_NAME = "Kanban";
const BOARD_NAME = "KanbanBoard";
const COLUMN_NAME = "KanbanColumn";
const COLUMN_HANDLE_NAME = "KanbanColumnHandle";
const ITEM_NAME = "KanbanItem";
const ITEM_HANDLE_NAME = "KanbanItemHandle";
const OVERLAY_NAME = "KanbanOverlay";

type UniqueIdentifier = string | number;

type MinimalDragEvent = {
  active: { id: UniqueIdentifier };
  over: { id: UniqueIdentifier } | null;
  activeIndex: number;
  overIndex: number;
};

interface KanbanContextValue<T> {
  id: string;
  items: Record<UniqueIdentifier, T[]>;
  orientation: "horizontal" | "vertical";
  activeId: UniqueIdentifier | null;
  setActiveId: (id: UniqueIdentifier | null) => void;
  getItemValue: (item: T) => UniqueIdentifier;
  flatCursor: boolean;
}

const KanbanContext = React.createContext<KanbanContextValue<unknown> | null>(null);
KanbanContext.displayName = ROOT_NAME;

function useKanbanContext(consumerName: string) {
  const context = React.useContext(KanbanContext);
  if (!context) {
    throw new Error(`\`${consumerName}\` must be used within \`${ROOT_NAME}\``);
  }
  return context;
}

interface GetItemValue<T> {
  getItemValue: (item: T) => UniqueIdentifier;
}

type KanbanRootProps<T> = React.ComponentPropsWithoutRef<"div"> &
  GetItemValue<T> & {
    value: Record<UniqueIdentifier, T[]>;
    onValueChange?: (columns: Record<UniqueIdentifier, T[]>) => void;
    onMove?: (event: MinimalDragEvent) => void;
    strategy?: unknown;
    orientation?: "horizontal" | "vertical";
    flatCursor?: boolean;
    modifiers?: unknown;
    accessibility?: unknown;
    onDragStart?: (...args: unknown[]) => void;
    onDragOver?: (...args: unknown[]) => void;
    onDragEnd?: (...args: unknown[]) => void;
    onDragCancel?: (...args: unknown[]) => void;
  };

function KanbanRoot<T>(props: KanbanRootProps<T>) {
  const {
    value,
    getItemValue,
    orientation = "horizontal",
    flatCursor = false,
    children,
    className,
    ...rootProps
  } = props;

  const id = React.useId();
  const [activeId, setActiveId] = React.useState<UniqueIdentifier | null>(null);

  const contextValue = React.useMemo<KanbanContextValue<T>>(
    () => ({
      id,
      items: value,
      orientation,
      activeId,
      setActiveId,
      getItemValue,
      flatCursor,
    }),
    [id, value, orientation, activeId, getItemValue, flatCursor]
  );

  return (
    <KanbanContext.Provider value={contextValue as KanbanContextValue<unknown>}>
      <div
        data-slot="kanban-root"
        className={cn("size-full", className)}
        {...rootProps}
      >
        {children}
      </div>
    </KanbanContext.Provider>
  );
}

const KanbanBoardContext = React.createContext<boolean>(false);
KanbanBoardContext.displayName = BOARD_NAME;

interface KanbanBoardProps extends React.ComponentPropsWithoutRef<"div"> {
  children: React.ReactNode;
  asChild?: boolean;
}

const KanbanBoard = React.forwardRef<HTMLDivElement, KanbanBoardProps>((props, forwardedRef) => {
  const { asChild, className, ...boardProps } = props;

  const context = useKanbanContext(BOARD_NAME);
  const BoardPrimitive = asChild ? Slot : "div";

  return (
    <KanbanBoardContext.Provider value={true}>
      <BoardPrimitive
        aria-orientation={context.orientation}
        data-orientation={context.orientation}
        data-slot="kanban-board"
        {...boardProps}
        ref={forwardedRef}
        className={cn(
          "flex size-full gap-4",
          context.orientation === "horizontal" ? "flex-row" : "flex-col",
          className
        )}
      />
    </KanbanBoardContext.Provider>
  );
});
KanbanBoard.displayName = BOARD_NAME;

interface KanbanColumnContextValue {
  id: string;
  isDragging?: boolean;
  disabled?: boolean;
  attributes?: Record<string, never>;
  listeners?: Record<string, never>;
  setActivatorNodeRef: (node: HTMLElement | null) => void;
}

const KanbanColumnContext = React.createContext<KanbanColumnContextValue | null>(null);
KanbanColumnContext.displayName = COLUMN_NAME;

function useKanbanColumnContext(consumerName: string) {
  const context = React.useContext(KanbanColumnContext);
  if (!context) {
    throw new Error(`\`${consumerName}\` must be used within \`${COLUMN_NAME}\``);
  }
  return context;
}

interface KanbanColumnProps extends React.ComponentPropsWithoutRef<"div"> {
  value: UniqueIdentifier;
  children: React.ReactNode;
  asChild?: boolean;
  asHandle?: boolean;
  disabled?: boolean;
}

const KanbanColumn = React.forwardRef<HTMLDivElement, KanbanColumnProps>((props, forwardedRef) => {
  const { value, asChild, asHandle, disabled, className, style, ...columnProps } = props;

  const id = React.useId();
  const context = useKanbanContext(COLUMN_NAME);
  const inBoard = React.useContext(KanbanBoardContext);
  const inOverlay = React.useContext(KanbanOverlayContext);

  if (!inBoard && !inOverlay) {
    throw new Error(
      `\`${COLUMN_NAME}\` must be used within \`${BOARD_NAME}\` or \`${OVERLAY_NAME}\``
    );
  }

  if (value === "") {
    throw new Error(`\`${COLUMN_NAME}\` value cannot be an empty string`);
  }

  const activatorRef = React.useRef<HTMLElement | null>(null);

  const composedRef = useComposedRefs(forwardedRef, (_node) => {
    return;
  });

  const columnContext = React.useMemo<KanbanColumnContextValue>(
    () => ({
      id,
      attributes: {},
      listeners: {},
      setActivatorNodeRef: (node) => {
        activatorRef.current = node;
      },
      isDragging: false,
      disabled,
    }),
    [id, disabled]
  );

  const ColumnPrimitive = asChild ? Slot : "div";

  return (
    <KanbanColumnContext.Provider value={columnContext}>
      <ColumnPrimitive
        id={id}
        data-disabled={disabled}
        data-dragging={undefined}
        data-slot="kanban-column"
        {...columnProps}
        ref={composedRef}
        style={style}
        className={cn(
          "bg-muted flex size-full flex-col gap-2 rounded-lg p-2.5 aria-disabled:pointer-events-none aria-disabled:opacity-50",
          {
            "touch-none select-none": asHandle,
            "cursor-default": context.flatCursor || !asHandle,
            "cursor-grab": asHandle && !disabled && !context.flatCursor,
            "pointer-events-none opacity-50": disabled,
          },
          className
        )}
      />
    </KanbanColumnContext.Provider>
  );
});
KanbanColumn.displayName = COLUMN_NAME;

interface KanbanColumnHandleProps extends React.ComponentPropsWithoutRef<"button"> {
  asChild?: boolean;
}

const KanbanColumnHandle = React.forwardRef<HTMLButtonElement, KanbanColumnHandleProps>(
  (props, forwardedRef) => {
    const { asChild, disabled, className, ...columnHandleProps } = props;

    const context = useKanbanContext(COLUMN_HANDLE_NAME);
    const columnContext = useKanbanColumnContext(COLUMN_HANDLE_NAME);

    const isDisabled = disabled ?? columnContext.disabled;
    const HandlePrimitive = asChild ? Slot : "button";

    const composedRef = useComposedRefs(forwardedRef, (node) => {
      if (isDisabled) return;
      columnContext.setActivatorNodeRef(node as HTMLElement | null);
    });

    return (
      <HandlePrimitive
        type="button"
        aria-controls={columnContext.id}
        data-disabled={isDisabled}
        data-dragging={undefined}
        data-slot="kanban-column-handle"
        {...columnHandleProps}
        ref={composedRef}
        className={cn(
          "select-none disabled:pointer-events-none disabled:opacity-50",
          context.flatCursor ? "cursor-default" : "cursor-grab",
          className
        )}
        disabled={isDisabled}
      />
    );
  }
);
KanbanColumnHandle.displayName = COLUMN_HANDLE_NAME;

interface KanbanItemContextValue {
  id: string;
  isDragging?: boolean;
  disabled?: boolean;
  attributes?: Record<string, never>;
  listeners?: Record<string, never>;
  setActivatorNodeRef: (node: HTMLElement | null) => void;
}

const KanbanItemContext = React.createContext<KanbanItemContextValue | null>(null);
KanbanItemContext.displayName = ITEM_NAME;

function useKanbanItemContext(consumerName: string) {
  const context = React.useContext(KanbanItemContext);
  if (!context) {
    throw new Error(`\`${consumerName}\` must be used within \`${ITEM_NAME}\``);
  }
  return context;
}

interface KanbanItemProps extends React.ComponentPropsWithoutRef<"div"> {
  value: UniqueIdentifier;
  asHandle?: boolean;
  asChild?: boolean;
  disabled?: boolean;
}

const KanbanItem = React.forwardRef<HTMLDivElement, KanbanItemProps>((props, forwardedRef) => {
  const { value, style, asHandle, asChild, disabled, className, ...itemProps } = props;

  const id = React.useId();
  const context = useKanbanContext(ITEM_NAME);
  const inBoard = React.useContext(KanbanBoardContext);
  const inOverlay = React.useContext(KanbanOverlayContext);

  if (!inBoard && !inOverlay) {
    throw new Error(`\`${ITEM_NAME}\` must be used within \`${BOARD_NAME}\``);
  }

  if (value === "") {
    throw new Error(`\`${ITEM_NAME}\` value cannot be an empty string`);
  }

  const activatorRef = React.useRef<HTMLElement | null>(null);

  const composedRef = useComposedRefs(forwardedRef, (_node) => {
    return;
  });

  const itemContext = React.useMemo<KanbanItemContextValue>(
    () => ({
      id,
      attributes: {},
      listeners: {},
      setActivatorNodeRef: (node) => {
        activatorRef.current = node;
      },
      isDragging: false,
      disabled,
    }),
    [id, disabled]
  );

  const ItemPrimitive = asChild ? Slot : "div";

  return (
    <KanbanItemContext.Provider value={itemContext}>
      <ItemPrimitive
        id={id}
        data-disabled={disabled}
        data-dragging={undefined}
        data-slot="kanban-item"
        {...itemProps}
        ref={composedRef}
        style={style}
        className={cn(
          "focus-visible:ring-ring focus-visible:ring-1 focus-visible:ring-offset-1 focus-visible:outline-hidden",
          {
            "touch-none select-none": asHandle,
            "cursor-default": context.flatCursor || !asHandle,
            "cursor-grab": asHandle && !disabled && !context.flatCursor,
            "pointer-events-none opacity-50": disabled,
          },
          className
        )}
      />
    </KanbanItemContext.Provider>
  );
});
KanbanItem.displayName = ITEM_NAME;

interface KanbanItemHandleProps extends React.ComponentPropsWithoutRef<"button"> {
  asChild?: boolean;
}

const KanbanItemHandle = React.forwardRef<HTMLButtonElement, KanbanItemHandleProps>(
  (props, forwardedRef) => {
    const { asChild, disabled, className, ...itemHandleProps } = props;

    const context = useKanbanContext(ITEM_HANDLE_NAME);
    const itemContext = useKanbanItemContext(ITEM_HANDLE_NAME);

    const isDisabled = disabled ?? itemContext.disabled;
    const HandlePrimitive = asChild ? Slot : "button";

    const composedRef = useComposedRefs(forwardedRef, (node) => {
      if (isDisabled) return;
      itemContext.setActivatorNodeRef(node as HTMLElement | null);
    });

    return (
      <HandlePrimitive
        type="button"
        aria-controls={itemContext.id}
        data-disabled={isDisabled}
        data-dragging={undefined}
        data-slot="kanban-item-handle"
        {...itemHandleProps}
        ref={composedRef}
        className={cn(
          "select-none disabled:pointer-events-none disabled:opacity-50",
          context.flatCursor ? "cursor-default" : "cursor-grab",
          className
        )}
        disabled={isDisabled}
      />
    );
  }
);
KanbanItemHandle.displayName = ITEM_HANDLE_NAME;

const KanbanOverlayContext = React.createContext(false);
KanbanOverlayContext.displayName = OVERLAY_NAME;

type KanbanOverlayProps = Omit<React.ComponentPropsWithoutRef<"div">, "children"> & {
  container?: Element | DocumentFragment | null;
  children?:
    | React.ReactNode
    | ((params: {
        value: UniqueIdentifier;
        variant: "column" | "item";
      }) => React.ReactNode);
};

function KanbanOverlay(props: KanbanOverlayProps) {
  const { children } = props;
  const context = useKanbanContext(OVERLAY_NAME);

  if (!context.activeId || !children) return null;

  const variant = context.activeId in context.items ? "column" : "item";

  return (
    <KanbanOverlayContext.Provider value={true}>
      {typeof children === "function"
        ? children({
            value: context.activeId,
            variant,
          })
        : children}
    </KanbanOverlayContext.Provider>
  );
}

export {
  KanbanRoot as Kanban,
  KanbanBoard,
  KanbanColumn,
  KanbanColumnHandle,
  KanbanItem,
  KanbanItemHandle,
  KanbanOverlay,
  //
  KanbanRoot as Root,
  KanbanBoard as Board,
  KanbanColumn as Column,
  KanbanColumnHandle as ColumnHandle,
  KanbanItem as Item,
  KanbanItemHandle as ItemHandle,
  KanbanOverlay as Overlay,
};