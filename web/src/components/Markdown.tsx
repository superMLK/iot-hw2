import type { ReactNode } from "react";
import { parseMarkdown, type Block, type Inline } from "../lib/markdown";

function inline(nodes: Inline[]): ReactNode[] {
  return nodes.map((n, i) => {
    switch (n.t) {
      case "text":
        return n.v;
      case "strong":
        return <strong key={i}>{inline(n.c)}</strong>;
      case "code":
        return <code key={i}>{n.v}</code>;
      case "link":
        return /^https?:\/\//.test(n.href) ? (
          <a key={i} href={n.href} target="_blank" rel="noreferrer">
            {inline(n.c)}
          </a>
        ) : (
          inline(n.c)
        );
    }
  });
}

function block(b: Block, i: number): ReactNode {
  switch (b.t) {
    case "h": {
      const level = Math.min(Math.max(b.level, 3), 4);
      return level === 3 ? <h3 key={i}>{inline(b.c)}</h3> : <h4 key={i}>{inline(b.c)}</h4>;
    }
    case "p":
      return <p key={i}>{inline(b.c)}</p>;
    case "ul":
      return (
        <ul key={i}>
          {b.items.map((it, j) => (
            <li key={j}>{inline(it)}</li>
          ))}
        </ul>
      );
    case "ol":
      return (
        <ol key={i}>
          {b.items.map((it, j) => (
            <li key={j}>{inline(it)}</li>
          ))}
        </ol>
      );
    case "quote":
      return <blockquote key={i}>{b.blocks.map(block)}</blockquote>;
  }
}

export default function Markdown({ text }: { text: string }) {
  return <div className="md">{parseMarkdown(text).map(block)}</div>;
}
