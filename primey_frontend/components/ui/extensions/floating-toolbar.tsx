"use client";

import type { Editor } from "@tiptap/react";
import { BubbleMenu } from "@tiptap/react/menus";
import React, { useEffect, useState } from "react";

import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { TooltipProvider } from "@/components/ui/tooltip";

import { AlignmentTooolbar } from "../toolbars/alignment";
import { BlockquoteToolbar } from "../toolbars/blockquote";
import { BoldToolbar } from "../toolbars/bold";
import { BulletListToolbar } from "../toolbars/bullet-list";
import { ColorHighlightToolbar } from "../toolbars/color-and-highlight";
import { HeadingsToolbar } from "../toolbars/headings";
import { ImagePlaceholderToolbar } from "../toolbars/image-placeholder-toolbar";
import { ItalicToolbar } from "../toolbars/italic";
import { LinkToolbar } from "../toolbars/link";
import { OrderedListToolbar } from "../toolbars/ordered-list";
import { ToolbarProvider } from "../toolbars/toolbar-provider";
import { UnderlineToolbar } from "../toolbars/underline";

function useMediaQuery(query: string): boolean {
  const getMatches = () => {
    if (typeof window === "undefined") return false;
    return window.matchMedia(query).matches;
  };

  const [matches, setMatches] = useState<boolean>(getMatches);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const mediaQueryList = window.matchMedia(query);

    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    setMatches(mediaQueryList.matches);

    if (typeof mediaQueryList.addEventListener === "function") {
      mediaQueryList.addEventListener("change", handleChange);
      return () => {
        mediaQueryList.removeEventListener("change", handleChange);
      };
    }

    mediaQueryList.addListener(handleChange);
    return () => {
      mediaQueryList.removeListener(handleChange);
    };
  }, [query]);

  return matches;
}

export function FloatingToolbar({ editor }: { editor: Editor | null }) {
  const isMobile = useMediaQuery("(max-width: 640px)");

  useEffect(() => {
    if (!editor?.view?.dom || !isMobile) return;

    const handleContextMenu = (e: Event) => {
      e.preventDefault();
    };

    const el = editor.view.dom;
    el.addEventListener("contextmenu", handleContextMenu);

    return () => {
      el.removeEventListener("contextmenu", handleContextMenu);
    };
  }, [editor, isMobile]);

  if (!editor) return null;

  if (isMobile) {
    return (
      <TooltipProvider>
        <BubbleMenu
          editor={editor}
          options={{
            placement: "bottom",
          }}
          shouldShow={() => {
            return editor.isEditable && editor.isFocused;
          }}
          className="bg-background mx-0 w-full min-w-full rounded-sm border shadow-sm"
        >
          <ToolbarProvider editor={editor}>
            <ScrollArea className="h-fit w-full py-0.5">
              <div className="flex items-center gap-0.5 px-2">
                <div className="flex items-center gap-0.5 p-1">
                  <BoldToolbar />
                  <ItalicToolbar />
                  <UnderlineToolbar />
                  <Separator orientation="vertical" className="mx-1 h-6" />

                  <HeadingsToolbar />
                  <BulletListToolbar />
                  <OrderedListToolbar />
                  <Separator orientation="vertical" className="mx-1 h-6" />

                  <ColorHighlightToolbar />
                  <LinkToolbar />
                  <ImagePlaceholderToolbar />
                  <Separator orientation="vertical" className="mx-1 h-6" />

                  <AlignmentTooolbar />
                  <BlockquoteToolbar />
                </div>
              </div>
              <ScrollBar className="h-0.5" orientation="horizontal" />
            </ScrollArea>
          </ToolbarProvider>
        </BubbleMenu>
      </TooltipProvider>
    );
  }

  return null;
}