# Design

## Context

- 動機與範圍見 `proposal.md`；行為要求見 `specs/`。完整的原始技術設計在專案根目錄 `design.md`（以下稱「原設計」），本文件不重抄，只記錄實作方式與原設計沒說清楚、需要先定案的部分。
- 專案目前是全新目錄：只有原設計與 `openspec/`，還不是 git repo，也沒有 GitHub remote。
- 兩份 CSV 尚未放進 repo。Bike 資料可從 UCI 直接下載（內容與 Kaggle 版相同）；House 資料只在 Kaggle，下載需要登入或 Kaggle API token。
- 網站是純靜態，內建資料集的分析全部在建置期完成；瀏覽器只負責呈現與自訂 CSV 的統計。

## Goals / Non-Goals

**Goals:**
- 一份 Python 管線同時處理兩個資料集，差異只寫在各自的設定與內容檔。
- 網站、Word 報告、資訊圖表的數值都來自同一次管線輸出。
- 管線決定性可重現；CI 失敗就不部署。

**Non-Goals:**
- 不做 Pyodide、後端 API、使用者帳號。
- 自訂 CSV 不做任何建模或特徵選擇。
- Word 報告與資訊圖表不放進 CI，在本機產生後提交（理由見決策 12）。
- 不做多語系，介面只有繁體中文。

## Decisions

### 1. 管線模組依 CRISP-DM 階段拆分，資料集差異集中在設定
`analysis/pipeline/` 下分成 `understanding.py`、`preparation.py`、`selection.py`、`modeling.py`、`evaluation.py`、`content.py`（佔位符代入）、`export.py`（JSON 與 PNG）。每個資料集的準備規則寫成一個函式（`prepare_bike`、`prepare_house`），回傳處理後的資料與步驟紀錄；其餘階段共用。`run_pipeline.py` 依 `datasets.yaml` 逐一執行。
- 替代方案：每個資料集一支獨立腳本。捨棄原因：特徵選擇、評估、輸出邏輯會重複兩份，數值格式也容易不一致。

### 2. 特徵數的計算口徑
`n_features = 原始欄數 − 目標變數 − ID 欄`，在原始 CSV 上計算。Bike：16 − `cnt` − `instant` = 14；House：21 − `price` − `id` = 19。日期欄（`dteday`、`date`）算在特徵數內，因為它是原始資料的屬性欄。兩者都落在 14–39。準備後實際進模型的特徵數另外顯示，不受此限制。

### 3. Bike 額外移除 `workingday`（原設計未列，新增）
`workingday` 由 `weekday` 與 `holiday` 完全決定（非週末且非假日即為 1）。`weekday` one-hot 後，`workingday` 等於週一到週五的 dummy 加總減去 `holiday`，是完全共線，會讓「全部特徵 MLR」的係數與標準誤失去意義，VIF 也會是無限大。因此在資料準備中移除，並在步驟紀錄寫明原因。
- 替代方案：留給 VIF 處理。捨棄原因：全部特徵的基準模型仍會是奇異矩陣，係數表無法解讀。

### 4. House 額外移除 `yr_built`，`sale_month` 做 one-hot（原設計未列，新增）
- `house_age = sale_year − yr_built`，三者完全共線，所以保留 `house_age` 與 `sale_year`，移除 `yr_built`。
- `sale_month` 對價格的影響不是線性，比照 Bike 的 `mnth`，one-hot 並丟棄 1 月為基準。
- `view`、`condition`、`grade` 是有序等級，以數值處理；`waterfront` 是 0/1。

### 5. House 異常值規則
移除：`bedrooms ≥ 30`（例如 33）、`bedrooms = 0`、`bathrooms = 0`。規則寫在設定中，筆數由管線計算並輸出到步驟紀錄。不依價格移除極端值，因為高價房是真實市場的一部分，log 轉換已經降低它們的影響。

### 6. 特徵選擇的細節
- **相關係數篩選的保留規則**（原設計未定義 `corr_kept`）：與目標的 |r| ≥ 0.1 才保留；若一對特徵彼此 |r| > 0.8，只保留與目標 |r| 較高的那一個。這個方法只做比較用，不影響後續流程。
- **VIF**：對訓練集特徵加上常數項後計算（不含常數本身）；VIF 為無限大時視為最高優先移除；每輪移除一個，直到全部 ≤ 10。
- **逐步回歸**：候選池是 VIF 後的特徵，從空模型（只有常數項）開始；每一步同時評估「加入一個」與「移除一個」，選 AIC 下降最多的動作，沒有任何動作能降低 AIC 就停止。one-hot 的 dummy 個別進出，不強制整組。
- 替代方案：以 VIF 後的完整特徵集為起點做向後消去。捨棄原因：從空模型開始的雙向法會產生較短、較好解讀的過程紀錄，網頁上比較容易說明。

### 7. 評估尺度
- House 的 R²、Adjusted R² 與交叉驗證 R² 在建模尺度（log 價格）計算；RMSE、MAE 在原始價格計算（原設計要求）。網頁與報告的指標表會標註「R² 以 log(price) 計算」。
- 選最佳模型以測試集 R² 為準；Bike 的 AR 與 OLS 同樣以測試期 `cnt` 的 R² 比較。
- Adjusted R² 使用該模型的特徵數；AR 以落後期數 p 作為特徵數。
- Bike 的 SLR 與 MLR 交叉驗證用 `TimeSeriesSplit(n_splits=5)` 套用在訓練集；AR 也在訓練集上用同一組切分，每一折重新以固定 p 擬合並做一步預測。House 用 `KFold(5, shuffle=True, random_state=42)` 套用在訓練集。

### 8. 區間計算
- OLS：`get_prediction(X).summary_frame(alpha=0.05)` 取 `mean_ci_*` 與 `obs_ci_*`。
- AR：`AutoReg` 以 `ar_select_order(maxlag=14, ic="aic")` 選 p，在訓練期擬合；測試期每一點用實際前期值算一步預測，區間為 ± 1.96 × 訓練殘差標準差。
- House：區間在 log 尺度算完再 `exp`，因此上下界相對預測值不對稱。
- SLR 的預測圖需要平滑的回歸線與區間帶：額外在特徵的最小值到最大值之間取 100 個等距點計算區間，存成 `prediction.band`（新增欄位，JSON 契約的延伸）；實際值散佈點仍用測試集。

### 9. JSON 契約的實作
- 以原設計第 6 節為準，前端在 `web/src/types/dataset.ts` 定義對應的 TypeScript 型別。
- 契約延伸：`meta.sampled`、`meta.n_points_total`、`meta.n_points_shown`；`models[].prediction.band`（只有 SLR）；`models[].ar_order`（只有 AR）；`models[].metrics_note`（例如 House 的 R² 尺度說明）；`data_understanding.n_duplicates`、`data_understanding.top_corr_features`；`crisp_dm.data_preparation.before`／`after`（筆數與欄數）。
- 浮點數輸出前統一四捨五入到 6 位有效數字，以控制檔案大小並讓重跑結果逐位元組相同。
- House 抽樣：依預測值排序後以 `numpy.linspace` 取等距索引，覆蓋率等指標用抽樣前的完整測試集計算。

### 10. 決定性
固定 `random_state=42`；JSON 以 `sort_keys=True` 輸出；`meta.generated_at` 是唯一允許每次不同的欄位，重現性檢查會忽略它。matplotlib 使用 `Agg` 後端並移除 PNG 中的時間戳記中繼資料。

### 11. CRISP-DM 內容與佔位符
內容檔 `analysis/content/<id>.zh-TW.yaml` 每個步驟一個 markdown 欄位，佔位符語法為 `{{path.to.value}}` 或 `{{path.to.value|fmt}}`（`fmt` 例如 `.3f`、`,.0f`、`pct`）。佔位符解析的資料來源是管線組好的結果物件，另外提供方便的別名（例如 `best.metrics.r2`）。解析不到就丟出錯誤讓管線失敗。成功標準的目標值（Bike 測試集 R² ≥ 0.70；House 測試集 R²〔log 尺度〕≥ 0.80）屬於業務設定而非結果，可以直接寫在內容檔中，結論文字由模板依實際值判斷是否達標。

### 12. 前端架構
- React 18 + Vite + TypeScript。不引入 router 函式庫，自己用 `hashchange` 實作 `#<dataset>-<step>` 狀態（狀態只有兩個維度，函式庫用不上）。
- 圖表用 `plotly.js-cartesian-dist-min` 搭配 `react-plotly.js/factory`，涵蓋 scatter、bar、histogram、heatmap。Plotly 以 lazy import 載入，避免首屏過大。
- 深淺色：CSS 變數加 `prefers-color-scheme`；圖表 layout 從同一組變數取色。區間帶用同一色相、不同透明度（信賴區間 0.35、預測區間 0.15），並在圖例名稱中寫明。
- RWD：主容器 `max-width` 加 16px 邊距，表格與圖表包在 `overflow-x: auto` 的容器中。
- Vite `base` 由環境變數決定：CI 中從 `GITHUB_REPOSITORY` 取得 repo 名稱設成 `/<repo>/`，本機預設 `/`。資料檔以 `import.meta.env.BASE_URL + "data/<id>.json"` 載入。這樣目前不必先決定 repo 名稱。

### 13. 自訂 CSV
- 流程：驗證網址（`new URL`，只允許 http/https）→ `fetch` → 檢查 `content-type` 與內容開頭是否像 HTML → PapaParse（`header: true`、`dynamicTyping: true`、`skipEmptyLines: "greedy"`）→ 截斷到 50,000 筆 → 型別推斷 → 統計。
- 型別推斷：非空值中 ≥ 95% 是有限數字為數值；≥ 95% 能被解析為日期（ISO 格式或 `YYYY/MM/DD` 類格式，不接受純數字）為日期；其他為類別。
- `fetch` 丟出 `TypeError` 時無法分辨是網路錯誤還是 CORS，訊息會同時說明兩種可能並給出建議。
- 統計純函式放在 `web/src/lib/stats/`（`inferType`、`describe`、`quantile`、`correlationMatrix`、`histogram`、`topCategories`、`countMissing`），Vitest 測試涵蓋空值、單一值、全為缺失、混合型別等邊界情況。
- 上傳檔案使用 PapaParse 直接解析 `File`，之後與 URL 模式走同一條流程。

### 14. 部署
`.github/workflows/deploy.yml`：`on: push: branches: [main]` 加 `workflow_dispatch`；權限 `pages: write`、`id-token: write`；步驟依原設計第 8 節。`web/public/data/` 加入 `.gitignore`。Node 版本用 LTS（`20`），Python 用 `3.11`，兩者都開啟 cache。

### 15. 繳交物在本機產生並提交
- Word 報告：`reports/build_report.py` 用 python-docx，讀內容檔、JSON、PNG。中文字型需同時設定 `w:eastAsia`（否則 Word 會退回預設字型）；標題用 `Heading 1/2/3` 內建樣式；圖表編號由程式累加。
- 資訊圖表：`reports/infographic/template.html` + `build_infographic.py`，以 Jinja 風格的簡單代入把 JSON 數值放進 HTML，預測圖使用管線輸出的簡化 PNG，QR code 用 Python `qrcode` 產生 SVG 內嵌。Playwright（Chromium）匯出 PDF（`format: "A4"`）與 PNG（viewport 794×1123 CSS px、`device_scale_factor ≈ 3.125`，得到 2480×3508）。
- 不放進 CI：Playwright 需要下載瀏覽器、Word 檔不需要隨每次部署更新；最終版在網站部署完成、網址確定後於本機產生並提交到 `reports/output/`。
- `reports/figures/` 由管線產生，與報告輸出一起提交，方便直接檢視。

## Risks / Trade-offs

- [House 資料需要 Kaggle 登入才能下載] → 實作時先嘗試 Kaggle API（使用者提供 token）；若不可行，請使用者手動下載 `kc_house_data.csv` 放入 `analysis/data/raw/`。Bike 可從 UCI 下載，但頁面上仍以 Kaggle 為主要來源標示。
- [授權條款需要實際查閱 Kaggle 頁面] → 實作時開啟頁面確認，結果寫入 `datasets.yaml`；若無法存取，請使用者確認後再填，管線在授權欄位為空時會失敗，避免漏標。
- [建立 GitHub repo、推送、開啟 Pages 是對外操作] → 實作到部署階段時暫停，由使用者確認 repo 名稱與可見性後才執行。
- [Bike 依時間切分，測試期（2012 年下半年）需求量高於訓練期，模型可能低估] → 這是真實的時間外推問題，在 Evaluation 與 Deployment 的限制說明中寫出，不改用隨機切分。
- [House 的 R² 在 log 尺度、RMSE 在價格尺度，讀者可能混淆] → 指標表與說明文字標註尺度。
- [逐步回歸的 p 值有選擇偏誤] → 在限制說明中提及，作為教學用途可接受。
- [浮點運算在不同平台可能有極小差異，影響逐位元組比對] → 輸出前統一四捨五入；重現性檢查在同一環境（同一台機器或同一個 CI runner 映像）進行。
- [Plotly 包體積大] → 使用 cartesian 精簡版並 lazy load。
- [大檔 CSV 在瀏覽器解析可能卡住畫面] → 50,000 筆上限；超過時解析到上限即停止（PapaParse `preview`）。

## Migration Plan

全新專案，沒有遷移。首次部署步驟：
1. `git init`，建立 GitHub repo（使用者確認名稱與可見性）。
2. repo 設定 Pages 的 Source 為 GitHub Actions。
3. 推送 `main`，確認 Actions 成功並取得 Pages 網址。
4. 以實際網址產生 README 連結、報告與資訊圖表 QR code，再提交一次。

回復方式：Pages 會保留上一個成功部署；若新版本有問題，revert commit 後再推送即可。

## Open Questions

- GitHub repo 名稱與可見性：只影響網址與 QR code 內容，`base` 已改為由 CI 自動決定，可以在部署階段再定。
- Word 報告封面的課程名稱與學號欄位：原設計要求姓名欄位留空，其餘欄位可在產生報告時補上，不影響其他工作。
