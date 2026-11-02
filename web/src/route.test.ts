import { describe, expect, test } from "vitest";
import { DEFAULT_ROUTE, parseHash, switchStep, switchView, toHash } from "./route";

describe("parseHash", () => {
  test("有效的資料集與步驟", () => {
    expect(parseHash("#house-modeling")).toEqual({ view: "house", step: "modeling" });
    expect(parseHash("#bike-evaluation")).toEqual({ view: "bike", step: "evaluation" });
  });
  test("沒有 hash 時預設 Bike 業務理解", () => {
    expect(parseHash("")).toEqual(DEFAULT_ROUTE);
    expect(parseHash("#")).toEqual(DEFAULT_ROUTE);
  });
  test("無效的 hash 回到預設", () => {
    for (const h of ["#foo", "#bike-xyz", "#cars-modeling", "#house-modeling-1", "#<script>"]) {
      expect(parseHash(h)).toEqual(DEFAULT_ROUTE);
    }
  });
  test("只有資料集名稱時從業務理解開始", () => {
    expect(parseHash("#house")).toEqual({ view: "house", step: "business" });
  });
  test("自訂 CSV 記住上一個步驟", () => {
    expect(parseHash("#custom", "evaluation")).toEqual({ view: "custom", step: "evaluation" });
  });
  test("大小寫不敏感", () => {
    expect(parseHash("#HOUSE-Modeling")).toEqual({ view: "house", step: "modeling" });
  });
});

describe("toHash", () => {
  test("序列化", () => {
    expect(toHash({ view: "house", step: "evaluation" })).toBe("#house-evaluation");
    expect(toHash({ view: "custom", step: "modeling" })).toBe("#custom");
  });
  test("與 parseHash 互為反函式", () => {
    const r = { view: "bike", step: "preparation" } as const;
    expect(parseHash(toHash(r))).toEqual(r);
  });
});

describe("切換", () => {
  test("切換資料集保留步驟", () => {
    const r = switchView({ view: "bike", step: "evaluation" }, "house");
    expect(toHash(r)).toBe("#house-evaluation");
  });
  test("切到自訂再切回來，步驟仍保留", () => {
    const c = switchView({ view: "house", step: "modeling" }, "custom");
    expect(toHash(c)).toBe("#custom");
    expect(switchView(c, "bike")).toEqual({ view: "bike", step: "modeling" });
  });
  test("切換步驟", () => {
    expect(switchStep({ view: "bike", step: "business" }, "data")).toEqual({ view: "bike", step: "data" });
    expect(switchStep({ view: "custom", step: "data" }, "modeling")).toEqual({ view: "custom", step: "data" });
  });
});
