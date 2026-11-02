import { useEffect, useState } from "react";
import type { DatasetId, DatasetResult } from "./types/dataset";

export type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: DatasetResult };

const cache = new Map<DatasetId, DatasetResult>();

export function datasetUrl(id: DatasetId): string {
  return `${import.meta.env.BASE_URL}data/${id}.json`;
}

export function useDataset(id: DatasetId | null): LoadState {
  const [state, setState] = useState<LoadState>(() =>
    id && cache.has(id) ? { status: "ready", data: cache.get(id)! } : { status: "loading" },
  );

  useEffect(() => {
    if (!id) return;
    const hit = cache.get(id);
    if (hit) {
      setState({ status: "ready", data: hit });
      return;
    }
    let alive = true;
    setState({ status: "loading" });
    fetch(datasetUrl(id))
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<DatasetResult>;
      })
      .then((data) => {
        cache.set(id, data);
        if (alive) setState({ status: "ready", data });
      })
      .catch((err: unknown) => {
        if (alive)
          setState({
            status: "error",
            message: `無法載入資料集（${err instanceof Error ? err.message : String(err)}）。請重新整理頁面，或確認分析管線已產生 data/${id}.json。`,
          });
      });
    return () => {
      alive = false;
    };
  }, [id]);

  return state;
}
