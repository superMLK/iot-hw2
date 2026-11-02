import type { ReactNode } from "react";

export interface Column<T> {
  key: string;
  header: ReactNode;
  render: (row: T, i: number) => ReactNode;
  num?: boolean;
  wrap?: boolean;
  cellClass?: (row: T) => string | undefined;
}

interface Props<T> {
  rows: T[];
  columns: Column<T>[];
  caption?: string;
  rowClass?: (row: T) => string | undefined;
  tall?: boolean;
}

export default function Table<T>({ rows, columns, caption, rowClass, tall }: Props<T>) {
  return (
    <div className={`table-wrap${tall ? " tall" : ""}`} tabIndex={0} role="region" aria-label={caption ?? "表格"}>
      <table>
        {caption && <caption className="visually-hidden">{caption}</caption>}
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} className={[c.num ? "num" : "", c.wrap ? "wrap" : ""].join(" ").trim() || undefined} scope="col">
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className={rowClass?.(r)}>
              {columns.map((c) => (
                <td key={c.key} className={[c.num ? "num" : "", c.wrap ? "wrap" : "", c.cellClass?.(r) ?? ""].join(" ").trim() || undefined}>
                  {c.render(r, i)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
