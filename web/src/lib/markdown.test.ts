import { describe, expect, test } from "vitest";
import { joinLines, parseInline, parseMarkdown } from "./markdown";

describe("joinLines", () => {
  test("中文接行不加空白", () => {
    expect(joinLines(["第一句。", "第二句"])).toBe("第一句。第二句");
  });
  test("英文接行補空白", () => {
    expect(joinLines(["hello", "world"])).toBe("hello world");
  });
  test("中英交界不加空白", () => {
    expect(joinLines(["平均 R²", "為 0.7"])).toBe("平均 R²為 0.7");
  });
});

describe("parseInline", () => {
  test("粗體、程式碼、連結", () => {
    expect(parseInline("a **b** `c` [d](https://x.y)")).toEqual([
      { t: "text", v: "a " },
      { t: "strong", c: [{ t: "text", v: "b" }] },
      { t: "text", v: " " },
      { t: "code", v: "c" },
      { t: "text", v: " " },
      { t: "link", href: "https://x.y", c: [{ t: "text", v: "d" }] },
    ]);
  });
});

describe("parseMarkdown", () => {
  test("標題、段落、清單、引言", () => {
    const b = parseMarkdown("### 標題\n第一行\n第二行\n\n- 甲\n  續行\n- 乙\n\n1. 一\n2. 二\n\n> **注意**：\n> 內容");
    expect(b.map((x) => x.t)).toEqual(["h", "p", "ul", "ol", "quote"]);
    expect(b[1]).toEqual({ t: "p", c: [{ t: "text", v: "第一行第二行" }] });
    expect(b[2]).toMatchObject({ t: "ul", items: [[{ t: "text", v: "甲續行" }], [{ t: "text", v: "乙" }]] });
    expect(b[3]).toMatchObject({ t: "ol" });
    expect(b[4]).toMatchObject({ t: "quote", blocks: [{ t: "p" }] });
  });
  test("段落後直接接清單", () => {
    expect(parseMarkdown("說明：\n- 一\n- 二").map((x) => x.t)).toEqual(["p", "ul"]);
  });
});
