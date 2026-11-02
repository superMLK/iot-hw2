// 精簡 Markdown 解析器（與 Word 報告產生器支援相同子集）：
// ### 標題、段落、- 清單、1. 編號清單、> 引言、**粗體**、`程式碼`、[連結](網址)
// 中文段落的換行接續時不插入空白。

export type Inline =
  | { t: "text"; v: string }
  | { t: "strong"; c: Inline[] }
  | { t: "code"; v: string }
  | { t: "link"; href: string; c: Inline[] };

export type Block =
  | { t: "h"; level: number; c: Inline[] }
  | { t: "p"; c: Inline[] }
  | { t: "ul" | "ol"; items: Inline[][] }
  | { t: "quote"; blocks: Block[] };

const CJK = /[⺀-鿿豈-﫿＀-￯　-〿]/;

/** 接續兩行：任一側是中日韓字元或全形標點時直接相連，否則補一個空白 */
export function joinLines(lines: string[]): string {
  let out = "";
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    if (!out) {
      out = line;
      continue;
    }
    const prev = out[out.length - 1];
    const next = line[0];
    out += CJK.test(prev) || CJK.test(next) ? line : ` ${line}`;
  }
  return out;
}

export function parseInline(src: string): Inline[] {
  const out: Inline[] = [];
  const re = /\*\*(.+?)\*\*|`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(src))) {
    if (m.index > last) out.push({ t: "text", v: src.slice(last, m.index) });
    if (m[1] !== undefined) out.push({ t: "strong", c: parseInline(m[1]) });
    else if (m[2] !== undefined) out.push({ t: "code", v: m[2] });
    else out.push({ t: "link", href: m[4], c: parseInline(m[3]) });
    last = re.lastIndex;
  }
  if (last < src.length) out.push({ t: "text", v: src.slice(last) });
  return out;
}

const UL = /^\s*[-*]\s+(.*)$/;
const OL = /^\s*\d+[.)]\s+(.*)$/;
const H = /^(#{1,6})\s+(.*)$/;

export function parseMarkdown(src: string): Block[] {
  const lines = src.replace(/\r\n?/g, "\n").split("\n");
  const blocks: Block[] = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i++;
      continue;
    }
    const h = H.exec(line.trim());
    if (h) {
      blocks.push({ t: "h", level: h[1].length, c: parseInline(h[2].trim()) });
      i++;
      continue;
    }
    if (/^\s*>/.test(line)) {
      const inner: string[] = [];
      while (i < lines.length && /^\s*>/.test(lines[i])) inner.push(lines[i++].replace(/^\s*>\s?/, ""));
      blocks.push({ t: "quote", blocks: parseMarkdown(inner.join("\n")) });
      continue;
    }
    const listKind = UL.test(line) ? "ul" : OL.test(line) ? "ol" : null;
    if (listKind) {
      const re = listKind === "ul" ? UL : OL;
      const items: string[][] = [];
      while (i < lines.length && lines[i].trim()) {
        const m = re.exec(lines[i]);
        if (m) items.push([m[1]]);
        else if (/^\s+\S/.test(lines[i]) && items.length) items[items.length - 1].push(lines[i]);
        else break;
        i++;
      }
      blocks.push({ t: listKind, items: items.map((it) => parseInline(joinLines(it))) });
      continue;
    }
    const para: string[] = [];
    while (i < lines.length && lines[i].trim() && !H.test(lines[i].trim()) && !/^\s*>/.test(lines[i]) && !UL.test(lines[i]) && !OL.test(lines[i])) {
      para.push(lines[i++]);
    }
    blocks.push({ t: "p", c: parseInline(joinLines(para)) });
  }
  return blocks;
}
