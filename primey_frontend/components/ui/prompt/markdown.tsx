import { cn } from "@/lib/utils";
import { marked } from "marked";
import { memo, useId, useMemo } from "react";
import { CodeBlock, CodeBlockCode } from "./code-block";

export type MarkdownComponentMap = {
  h1?: React.ComponentType<React.HTMLAttributes<HTMLHeadingElement>>;
  h2?: React.ComponentType<React.HTMLAttributes<HTMLHeadingElement>>;
  h3?: React.ComponentType<React.HTMLAttributes<HTMLHeadingElement>>;
  h4?: React.ComponentType<React.HTMLAttributes<HTMLHeadingElement>>;
  h5?: React.ComponentType<React.HTMLAttributes<HTMLHeadingElement>>;
  h6?: React.ComponentType<React.HTMLAttributes<HTMLHeadingElement>>;
  p?: React.ComponentType<React.HTMLAttributes<HTMLParagraphElement>>;
  ul?: React.ComponentType<React.HTMLAttributes<HTMLUListElement>>;
  ol?: React.ComponentType<React.OlHTMLAttributes<HTMLOListElement>>;
  li?: React.ComponentType<React.LiHTMLAttributes<HTMLLIElement>>;
  blockquote?: React.ComponentType<React.HTMLAttributes<HTMLQuoteElement>>;
  a?: React.ComponentType<React.AnchorHTMLAttributes<HTMLAnchorElement>>;
  hr?: React.ComponentType<React.HTMLAttributes<HTMLHRElement>>;
  strong?: React.ComponentType<React.HTMLAttributes<HTMLElement>>;
  em?: React.ComponentType<React.HTMLAttributes<HTMLElement>>;
  code?: React.ComponentType<React.HTMLAttributes<HTMLElement>>;
};

export type MarkdownProps = {
  children: string;
  id?: string;
  className?: string;
  components?: Partial<MarkdownComponentMap>;
};

type Token = ReturnType<typeof marked.lexer>[number];

function parseMarkdownIntoBlocks(markdown: string): Token[] {
  return marked.lexer(markdown);
}

function extractFenceLanguage(token: Token): string {
  if (token.type !== "code") return "plaintext";
  return token.lang || "plaintext";
}

const defaultComponents: Partial<MarkdownComponentMap> = {
  h1: (props) => <h1 className="scroll-m-20 text-3xl font-bold tracking-tight" {...props} />,
  h2: (props) => <h2 className="scroll-m-20 text-2xl font-semibold tracking-tight" {...props} />,
  h3: (props) => <h3 className="scroll-m-20 text-xl font-semibold tracking-tight" {...props} />,
  h4: (props) => <h4 className="scroll-m-20 text-lg font-semibold tracking-tight" {...props} />,
  h5: (props) => <h5 className="text-base font-semibold" {...props} />,
  h6: (props) => <h6 className="text-sm font-semibold" {...props} />,
  p: (props) => <p className="leading-7 [&:not(:first-child)]:mt-4" {...props} />,
  ul: (props) => <ul className="my-4 ml-6 list-disc" {...props} />,
  ol: (props) => <ol className="my-4 ml-6 list-decimal" {...props} />,
  li: (props) => <li className="mt-1" {...props} />,
  blockquote: (props) => (
    <blockquote className="mt-4 border-s-2 ps-4 italic text-muted-foreground" {...props} />
  ),
  a: (props) => (
    <a
      className="text-primary underline underline-offset-4"
      target="_blank"
      rel="noreferrer"
      {...props}
    />
  ),
  hr: (props) => <hr className="my-6 border-border" {...props} />,
  strong: (props) => <strong className="font-semibold" {...props} />,
  em: (props) => <em className="italic" {...props} />,
  code: (props) => (
    <code className="bg-background rounded-sm px-1 py-0.5 font-mono text-sm" {...props} />
  ),
};

function renderInlineTokens(
  tokens: Token[] | undefined,
  components: Partial<MarkdownComponentMap>,
  keyPrefix: string
): React.ReactNode {
  if (!tokens?.length) return null;

  return tokens.map((token, index) => renderInlineToken(token, components, `${keyPrefix}-${index}`));
}

function renderInlineToken(
  token: Token,
  components: Partial<MarkdownComponentMap>,
  key: string
): React.ReactNode {
  switch (token.type) {
    case "text": {
      const textToken = token as Token & { text?: string; tokens?: Token[] };
      if (textToken.tokens?.length) {
        return <span key={key}>{renderInlineTokens(textToken.tokens, components, key)}</span>;
      }
      return textToken.text || "";
    }

    case "strong": {
      const Comp = components.strong || defaultComponents.strong!;
      const strongToken = token as Token & { tokens?: Token[] };
      return <Comp key={key}>{renderInlineTokens(strongToken.tokens, components, key)}</Comp>;
    }

    case "em": {
      const Comp = components.em || defaultComponents.em!;
      const emToken = token as Token & { tokens?: Token[] };
      return <Comp key={key}>{renderInlineTokens(emToken.tokens, components, key)}</Comp>;
    }

    case "codespan": {
      const Comp = components.code || defaultComponents.code!;
      const codeToken = token as Token & { text?: string };
      return <Comp key={key}>{codeToken.text || ""}</Comp>;
    }

    case "br":
      return <br key={key} />;

    case "link": {
      const Comp = components.a || defaultComponents.a!;
      const linkToken = token as Token & { href?: string; title?: string; tokens?: Token[] };
      return (
        <Comp key={key} href={linkToken.href} title={linkToken.title}>
          {renderInlineTokens(linkToken.tokens, components, key)}
        </Comp>
      );
    }

    default: {
      const fallback = token as Token & { raw?: string; text?: string };
      return fallback.text || fallback.raw || null;
    }
  }
}

function renderBlockToken(
  token: Token,
  index: number,
  components: Partial<MarkdownComponentMap>
): React.ReactNode {
  switch (token.type) {
    case "space":
      return null;

    case "paragraph": {
      const Comp = components.p || defaultComponents.p!;
      const paragraphToken = token as Token & { tokens?: Token[] };
      return (
        <Comp key={`p-${index}`}>
          {renderInlineTokens(paragraphToken.tokens, components, `p-${index}`)}
        </Comp>
      );
    }

    case "heading": {
      const headingToken = token as Token & { depth?: number; tokens?: Token[] };
      const depth = headingToken.depth || 1;

      const map = {
        1: components.h1 || defaultComponents.h1!,
        2: components.h2 || defaultComponents.h2!,
        3: components.h3 || defaultComponents.h3!,
        4: components.h4 || defaultComponents.h4!,
        5: components.h5 || defaultComponents.h5!,
        6: components.h6 || defaultComponents.h6!,
      } as const;

      const Comp = map[Math.min(Math.max(depth, 1), 6) as 1 | 2 | 3 | 4 | 5 | 6];

      return (
        <Comp key={`h-${index}`}>
          {renderInlineTokens(headingToken.tokens, components, `h-${index}`)}
        </Comp>
      );
    }

    case "code": {
      const codeToken = token as Token & { text?: string };
      return (
        <CodeBlock key={`code-${index}`}>
          <CodeBlockCode
            code={codeToken.text || ""}
            language={extractFenceLanguage(token)}
          />
        </CodeBlock>
      );
    }

    case "blockquote": {
      const Comp = components.blockquote || defaultComponents.blockquote!;
      const quoteToken = token as Token & { tokens?: Token[] };
      return (
        <Comp key={`blockquote-${index}`}>
          {quoteToken.tokens?.map((child, childIndex) =>
            renderBlockToken(child, childIndex, components)
          )}
        </Comp>
      );
    }

    case "list": {
      const listToken = token as Token & {
        ordered?: boolean;
        items?: Array<{ tokens?: Token[] }>;
      };

      const ListComp = listToken.ordered
        ? components.ol || defaultComponents.ol!
        : components.ul || defaultComponents.ul!;
      const ItemComp = components.li || defaultComponents.li!;

      return (
        <ListComp key={`list-${index}`}>
          {listToken.items?.map((item, itemIndex) => (
            <ItemComp key={`list-item-${index}-${itemIndex}`}>
              {item.tokens?.map((child, childIndex) =>
                renderBlockToken(child, childIndex, components)
              )}
            </ItemComp>
          ))}
        </ListComp>
      );
    }

    case "hr": {
      const Comp = components.hr || defaultComponents.hr!;
      return <Comp key={`hr-${index}`} />;
    }

    case "html": {
      const htmlToken = token as Token & { text?: string; raw?: string };
      return (
        <div
          key={`html-${index}`}
          dangerouslySetInnerHTML={{ __html: htmlToken.text || htmlToken.raw || "" }}
        />
      );
    }

    case "text": {
      const textToken = token as Token & { text?: string; tokens?: Token[] };
      if (textToken.tokens?.length) {
        const Comp = components.p || defaultComponents.p!;
        return (
          <Comp key={`text-${index}`}>
            {renderInlineTokens(textToken.tokens, components, `text-${index}`)}
          </Comp>
        );
      }
      return textToken.text ? (
        <p key={`text-${index}`} className="leading-7">
          {textToken.text}
        </p>
      ) : null;
    }

    default:
      return null;
  }
}

const MemoizedMarkdownBlock = memo(
  function MarkdownBlock({
    token,
    index,
    components,
  }: {
    token: Token;
    index: number;
    components: Partial<MarkdownComponentMap>;
  }) {
    return <>{renderBlockToken(token, index, components)}</>;
  },
  function propsAreEqual(prevProps, nextProps) {
    return prevProps.token.raw === nextProps.token.raw;
  }
);

MemoizedMarkdownBlock.displayName = "MemoizedMarkdownBlock";

function MarkdownComponent({
  children,
  id,
  className,
  components,
}: MarkdownProps) {
  const generatedId = useId();
  const blockId = id ?? generatedId;
  const blocks = useMemo(() => parseMarkdownIntoBlocks(children), [children]);
  const mergedComponents = useMemo(
    () => ({
      ...defaultComponents,
      ...components,
    }),
    [components]
  );

  return (
    <div className={cn("space-y-4", className)}>
      {blocks.map((token, index) => (
        <MemoizedMarkdownBlock
          key={`${blockId}-block-${index}`}
          token={token}
          index={index}
          components={mergedComponents}
        />
      ))}
    </div>
  );
}

const Markdown = memo(MarkdownComponent);
Markdown.displayName = "Markdown";

export { Markdown };