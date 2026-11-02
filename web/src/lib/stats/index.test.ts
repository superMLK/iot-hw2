import { describe as group, expect, test } from "vitest";
import { correlationMatrix, countMissing, describe, histogram, inferType, isMissing, pearson, quantile, topCategories, toNumber, uniqueCount } from ".";

group("isMissing / countMissing", () => {
  test("空字串、空白、null、NaN、NA 都算缺失", () => {
    expect([null, undefined, "", "  ", NaN, "NA", "n/a", "null"].every(isMissing)).toBe(true);
    expect([0, "0", "abc", false].some(isMissing)).toBe(false);
    expect(countMissing([1, "", null, " ", 2])).toBe(3);
  });
});

group("toNumber", () => {
  test("數字與數字字串", () => {
    expect(toNumber(3.5)).toBe(3.5);
    expect(toNumber(" 1,234.5 ")).toBe(1234.5);
    expect(toNumber("1e3")).toBe(1000);
    expect(toNumber("abc")).toBeNull();
    expect(toNumber("2020-01-01")).toBeNull();
    expect(toNumber(Infinity)).toBeNull();
  });
});

group("inferType", () => {
  test("數值欄（含缺失值）", () => expect(inferType([1, 2, "", 3.5, null])).toBe("numeric"));
  test("類別欄", () => expect(inferType(["New York", "California", "Florida"])).toBe("categorical"));
  test("日期欄", () => expect(inferType(["2020-01-01", "2020/02/15", "2021-12-31 10:00"])).toBe("date"));
  test("純數字不當日期", () => expect(inferType([20200101, 20200102])).toBe("numeric"));
  test("全部缺失視為類別", () => expect(inferType([null, "", undefined])).toBe("categorical"));
  test("混合型別多數為文字時為類別", () => expect(inferType([1, 2, "a", "b"])).toBe("categorical"));
  test("95% 門檻：20 個中 1 個例外仍為數值", () => {
    expect(inferType([...Array(19).fill(1), "x"])).toBe("numeric");
    expect(inferType([...Array(18).fill(1), "x", "y"])).toBe("categorical");
  });
});

group("describe / quantile", () => {
  test("與 pandas 一致的四分位數與樣本標準差", () => {
    const d = describe([1, 2, 3, 4]);
    expect(d).toMatchObject({ count: 4, mean: 2.5, min: 1, q1: 1.75, median: 2.5, q3: 3.25, max: 4 });
    expect(d.std).toBeCloseTo(1.2909944, 6);
  });
  test("單一值：標準差為 NaN", () => {
    const d = describe([5]);
    expect(d.count).toBe(1);
    expect(d.median).toBe(5);
    expect(Number.isNaN(d.std)).toBe(true);
  });
  test("空陣列", () => expect(describe([]).count).toBe(0));
  test("quantile", () => expect(quantile([10, 20, 30], 0.5)).toBe(20));
});

group("相關係數", () => {
  test("完全正相關、負相關", () => {
    expect(pearson([1, 2, 3], [2, 4, 6])).toBeCloseTo(1);
    expect(pearson([1, 2, 3], [3, 2, 1])).toBeCloseTo(-1);
  });
  test("成對缺失值會被略過", () => expect(pearson([1, 2, null, 4], [2, 4, 100, 8])).toBeCloseTo(1));
  test("變異為 0 回傳 null", () => expect(pearson([1, 1, 1], [1, 2, 3])).toBeNull());
  test("矩陣對稱且對角為 1", () => {
    const m = correlationMatrix([[1, 2, 3], [1, 3, 2], [5, 5, 5]]);
    expect(m[0][0]).toBe(1);
    expect(m[0][1]).toBe(m[1][0]);
    expect(m[2][2]).toBeNull();
  });
});

group("histogram", () => {
  test("筆數總和等於資料筆數，最大值落在最後一格", () => {
    const h = histogram([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5);
    expect(h.counts.reduce((a, b) => a + b, 0)).toBe(11);
    expect(h.bins).toHaveLength(6);
    expect(h.counts[4]).toBe(3);
  });
  test("單一值", () => expect(histogram([3, 3, 3]).counts).toEqual([3]));
  test("空陣列", () => expect(histogram([]).counts).toEqual([]));
});

group("topCategories / uniqueCount", () => {
  test("只取前 10 名，依次數排序", () => {
    const vals = Array.from({ length: 15 }, (_, i) => Array(i + 1).fill(`c${i}`)).flat();
    const top = topCategories(vals);
    expect(top).toHaveLength(10);
    expect(top[0]).toEqual({ value: "c14", count: 15 });
    expect(top[9].value).toBe("c5");
  });
  test("忽略缺失值", () => {
    expect(topCategories(["a", "", null, "a", "b"])).toEqual([{ value: "a", count: 2 }, { value: "b", count: 1 }]);
    expect(uniqueCount(["a", "a ", "", "b"])).toBe(2);
  });
});
