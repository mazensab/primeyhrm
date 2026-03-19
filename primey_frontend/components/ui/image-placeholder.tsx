"use client";
/* eslint-disable */
// @ts-nocheck

import {
  type CommandProps,
  Node,
  type NodeViewProps,
  NodeViewWrapper,
  ReactNodeViewRenderer,
  mergeAttributes,
} from "@tiptap/react";
import { ImageIcon, Link, Upload, Loader2, X } from "lucide-react";
import { type FormEvent, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

import { useImageUpload } from "./hooks/use-image-upload";
import { NODE_HANDLES_SELECTED_STYLE_CLASSNAME, isValidUrl } from "./utils";

export interface ImagePlaceholderOptions {
  HTMLAttributes: Record<string, any>;
  onUpload?: (url: string) => void;
  onError?: (error: string) => void;
}

declare module "@tiptap/core" {
  interface Commands<ReturnType> {
    imagePlaceholder: {
      insertImagePlaceholder: () => ReturnType;
    };
  }
}

export const ImagePlaceholder = Node.create<ImagePlaceholderOptions>({
  name: "image-placeholder",

  addOptions() {
    return {
      HTMLAttributes: {},
      onUpload: () => {},
      onError: () => {},
    };
  },

  group: "block",

  parseHTML() {
    return [{ tag: `div[data-type="${this.name}"]` }];
  },

  renderHTML({ HTMLAttributes }) {
    return ["div", mergeAttributes(HTMLAttributes)];
  },

  addNodeView() {
    return ReactNodeViewRenderer(ImagePlaceholderComponent, {
      className: NODE_HANDLES_SELECTED_STYLE_CLASSNAME,
    });
  },

  addCommands() {
    return {
      insertImagePlaceholder:
        () =>
        (props: CommandProps) => {
          return props.commands.insertContent({
            type: "image-placeholder",
          });
        },
    };
  },
});

function ImagePlaceholderComponent(props: NodeViewProps) {
  const { editor, selected } = props;

  const [isExpanded, setIsExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<"upload" | "url">("upload");
  const [url, setUrl] = useState("");
  const [altText, setAltText] = useState("");
  const [urlError, setUrlError] = useState(false);
  const [isDragActive, setIsDragActive] = useState(false);

  const { previewUrl, fileInputRef, handleFileChange, handleRemove, uploading, error } =
    useImageUpload({
      onUpload: (imageUrl) => {
        editor
          .chain()
          .focus()
          .setImage({
            src: imageUrl,
            alt: altText || fileInputRef.current?.files?.[0]?.name || "Uploaded image",
          })
          .run();

        handleRemove();
        setIsExpanded(false);
      },
    });

  const handleDragEnter = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    const input = fileInputRef.current;
    if (!input) return;

    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    input.files = dataTransfer.files;
    handleFileChange({ target: input } as any);
  };

  const handleInsertEmbed = (e: FormEvent) => {
    e.preventDefault();

    const valid = isValidUrl(url);
    if (!valid) {
      setUrlError(true);
      return;
    }

    editor
      .chain()
      .focus()
      .setImage({
        src: url,
        alt: altText || "Image",
      })
      .run();

    setIsExpanded(false);
    setUrl("");
    setAltText("");
    setUrlError(false);
  };

  return (
    <NodeViewWrapper className="w-full">
      <div className="relative">
        {!isExpanded ? (
          <div
            onClick={() => setIsExpanded(true)}
            className={cn(
              "group hover:bg-accent relative flex cursor-pointer flex-col items-center gap-4 rounded-lg border-2 border-dashed p-8 transition-all",
              selected && "border-primary bg-primary/5",
              isDragActive && "border-primary bg-primary/5",
              error && "border-destructive bg-destructive/5"
            )}
          >
            <div className="bg-background group-hover:bg-accent rounded-full p-4 shadow-sm transition-colors">
              <ImageIcon className="h-6 w-6" aria-hidden="true" />
            </div>

            <div className="text-center">
              <p className="text-sm font-medium">Click to upload or drag and drop</p>
              <p className="text-muted-foreground text-xs">SVG, PNG, JPG or GIF</p>
            </div>
          </div>
        ) : (
          <div className="bg-card rounded-lg border p-4 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Add Image</h3>
              <Button variant="ghost" size="icon" type="button" onClick={() => setIsExpanded(false)}>
                <X className="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>

            <Tabs
              value={activeTab}
              onValueChange={(v: string) => setActiveTab(v as "upload" | "url")}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="upload">
                  <Upload className="mr-2 h-4 w-4" aria-hidden="true" />
                  Upload
                </TabsTrigger>
                <TabsTrigger value="url">
                  <Link className="mr-2 h-4 w-4" aria-hidden="true" />
                  URL
                </TabsTrigger>
              </TabsList>

              <TabsContent value="upload">
                <div
                  onDragEnter={handleDragEnter}
                  onDragLeave={handleDragLeave}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                  className={cn(
                    "my-4 rounded-lg border-2 border-dashed p-8 text-center transition-colors",
                    isDragActive && "border-primary bg-primary/10",
                    error && "border-destructive bg-destructive/10"
                  )}
                >
                  {previewUrl ? (
                    <div className="space-y-4">
                      <img
                        src={previewUrl}
                        alt={altText || "Preview"}
                        className="mx-auto max-h-[200px] rounded-lg object-cover"
                      />

                      <div className="space-y-2">
                        <Input
                          value={altText}
                          onChange={(e) => setAltText(e.target.value)}
                          placeholder="Alt text (optional)"
                        />

                        <div className="flex justify-end gap-2">
                          <Button variant="outline" type="button" onClick={handleRemove} disabled={uploading}>
                            Remove
                          </Button>

                          <Button type="button" disabled={uploading}>
                            {uploading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
                            Upload
                          </Button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="hidden"
                        id="image-upload"
                      />

                      <label htmlFor="image-upload" className="flex cursor-pointer flex-col items-center gap-4">
                        <Upload className="text-muted-foreground h-8 w-8" aria-hidden="true" />
                        <div>
                          <p className="text-sm font-medium">Click to upload or drag and drop</p>
                          <p className="text-muted-foreground text-xs">SVG, PNG, JPG or GIF</p>
                        </div>
                      </label>
                    </>
                  )}

                  {error && <p className="text-destructive mt-2 text-sm">{error}</p>}
                </div>
              </TabsContent>

              <TabsContent value="url">
                <form onSubmit={handleInsertEmbed} className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Input
                      value={url}
                      onChange={(e) => {
                        setUrl(e.target.value);
                        if (urlError) setUrlError(false);
                      }}
                      placeholder="Enter image URL..."
                    />
                    {urlError && <p className="text-destructive text-xs">Please enter a valid URL</p>}
                  </div>

                  <div className="space-y-2">
                    <Input
                      value={altText}
                      onChange={(e) => setAltText(e.target.value)}
                      placeholder="Alt text (optional)"
                    />
                  </div>

                  <Button type="submit" className="w-full" disabled={!url}>
                    Add Image
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </div>
        )}
      </div>
    </NodeViewWrapper>
  );
}