import { describe as group, expect, test } from "vitest";
import { CsvError, errorMessage, looksLikeHtml, MAX_HEATMAP_COLS, MAX_ROWS, parseCsvText, summarize, validateUrl } from "./loader";

const kind = (fn: () => unknown) => {
  try {
    fn();
  } catch (e) {
    return (e as CsvError).kind;
  }
  return "ok";
};

const STARTUPS = `R&D Spend,Administration,Marketing Spend,State,Profit
165349.2,136897.8,471784.1,New York,192261.83
162597.7,151377.59,443898.53,California,191792.06
153441.51,101145.55,407934.54,Florida,191050.39
`;

group("validateUrl", () => {
  test("有效網址", () => expect(validateUrl(" https://example.com/a.csv ").hostname).toBe("example.com"));
  test("格式錯誤", () => {
    for (const s of ["abc", "", "ftp://x.com/a.csv", "javascript:alert(1)", "https://nodot"]) expect(kind(() => validateUrl(s))).toBe("invalid_url");
  });
});

group("parseCsvText", () => {
  test("一般 CSV", () => {
    const p = parseCsvText(STARTUPS);
    expect(p.fields).toEqual(["R&D Spend", "Administration", "Marketing Spend", "State", "Profit"]);
    expect(p.rows).toHaveLength(3);
    expect(p.rows[0]["Profit"]).toBe(192261.83);
  });
  test("空檔案與只有空白", () => {
    expect(kind(() => parseCsvText(""))).toBe("empty");
    expect(kind(() => parseCsvText("  \n\n "))).toBe("empty");
  });
  test("只有標題列", () => expect(kind(() => parseCsvText("a,b,c\n"))).toBe("empty"));
  test("HTML 網頁", () => {
    expect(kind(() => parseCsvText("<!DOCTYPE html><html><body>hi</body></html>"))).toBe("not_csv");
    expect(kind(() => parseCsvText("a,b\n1,2", "text/html; charset=utf-8"))).toBe("not_csv");
  });
  test("二進位內容", () => expect(kind(() => parseCsvText("PK\u0003\u0004\u0000\u0000binary"))).toBe("not_csv"));
  test("BOM 與空白標題", () => {
    const p = parseCsvText("﻿a,,c\n1,2,3");
    expect(p.fields).toEqual(["a", "（未命名欄 2）", "c"]);
  });
  test("超過 50,000 筆只取前 50,000 筆", () => {
    const text = "x\n" + Array.from({ length: MAX_ROWS + 10 }, (_, i) => i).join("\n");
    const p = parseCsvText(text);
    expect(p.rows).toHaveLength(MAX_ROWS);
    expect(p.truncated).toBe(true);
  });
});

group("summarize", () => {
  test("範例資料：型別、敘述統計、分布", () => {
    const s = summarize(parseCsvText(STARTUPS));
    expect(s.nRows).toBe(3);
    expect(s.nCols).toBe(5);
    expect(s.columns.find((c) => c.name === "State")?.type).toBe("categorical");
    expect(s.describe.map((d) => d.name)).toEqual(["R&D Spend", "Administration", "Marketing Spend", "Profit"]);
    expect(s.corr.labels).toHaveLength(4);
    expect(s.distributions.find((d) => d.name === "State")?.kind).toBe("top");
  });
  test("欄數很少（2 欄）也能處理，沒有特徵數限制", () => {
    const s = summarize(parseCsvText("a,b\n1,x\n2,y"));
    expect(s.nCols).toBe(2);
    expect(s.corr.labels).toEqual(["a"]);
  });
  test("數值欄超過 50 欄時熱圖只取前 50 欄", () => {
    const head = Array.from({ length: 80 }, (_, i) => `c${i}`).join(",");
    const rows = Array.from({ length: 5 }, (_, r) => Array.from({ length: 80 }, (_, i) => r * i + (i % 3)).join(","));
    const s = summarize(parseCsvText([head, ...rows].join("\n")));
    expect(s.corr.labels).toHaveLength(MAX_HEATMAP_COLS);
    expect(s.corr.limited).toBe(true);
    expect(s.corr.nNumeric).toBe(80);
  });
  test("缺失值計入且不影響統計", () => {
    const s = summarize(parseCsvText("a,b\n1,x\n,y\n3, \n"));
    expect(s.columns.find((c) => c.name === "a")?.missing).toBe(1);
    expect(s.columns.find((c) => c.name === "b")?.missing).toBe(1);
    expect(s.describe[0]).toMatchObject({ count: 2, mean: 2 });
  });
});

group("errorMessage", () => {
  test("每種錯誤都有中文標題與建議", () => {
    for (const k of ["invalid_url", "network", "http", "not_csv", "empty"] as const) {
      const m = errorMessage(new CsvError(k, k === "http" ? "HTTP 404" : ""));
      expect(m.title).toMatch(/[一-鿿]/);
      expect(m.hint).toBeTruthy();
    }
  });
  test("網路錯誤說明 CORS 並建議 raw 網址或上傳", () => {
    const m = errorMessage(new TypeError("Failed to fetch"));
    expect(m.body).toContain("CORS");
    expect(m.hint).toMatch(/raw|上傳/);
  });
  test("looksLikeHtml", () => expect(looksLikeHtml("  <html><head>")).toBe(true));
});
