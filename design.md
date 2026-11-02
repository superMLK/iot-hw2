# CRISP-DM 線性回歸分析網站：設計文件

> 本文件是實作的唯一需求來源。請依本文件產生 OpenSpec 的 proposal、specs、design、tasks，再依 tasks 實作。
> 介面、報告、資訊圖表一律使用**繁體中文（台灣用語）**。

---

## 1. 目標

建立一個靜態網站。網站依 CRISP-DM 流程，對兩個 Kaggle 公開資料集完成資料理解、資料準備、建模到評估的全過程，模型使用線性回歸。網站另外提供「自訂 CSV URL」功能，可以即時檢視任意資料集的基本資訊。

網站完成後，接著產出以下繳交物：README、Word 書面報告、A4 直式資訊圖表。

### 作業硬性要求（驗收時逐條檢查）

1. 使用兩個 Kaggle 公開資料集，每個的特徵數都大於 13、小於 40，並明確標示來源與連結。
2. 使用線性回歸模型預測，涵蓋單純線性回歸、多元線性回歸、Auto Regression。
3. 必須執行特徵選擇（Feature Selection）與模型評估（Model Evaluation）。
4. 預測圖必須附上信賴區間或預測區間。
5. 依 CRISP-DM 六個步驟說明：Business Understanding、Data Understanding、Data Preparation、Modeling、Evaluation、Deployment。
6. 下拉選單可以切換兩個資料集，切換後呈現該資料集的相關資訊。
7. 可以輸入任意 CSV URL，並呈現該資料集的相關資訊。

---

## 2. 範圍

### 範圍內
- 兩個內建資料集：在建置階段以 Python 完成全部分析，前端只負責呈現結果。
- 自訂 URL：在瀏覽器以 JavaScript 計算並顯示資料資訊。
- 以 GitHub Actions 自動部署到 GitHub Pages。
- README、Word 報告、A4 資訊圖表。

### 範圍外（不實作，介面上也不顯示）
- 自訂 URL 的建模、特徵選擇、預測圖。
- 任何後端伺服器、Pyodide、使用者帳號、資料上傳到伺服器。

---

## 3. 資料集

兩份 CSV 都存放在 repo 中（`analysis/data/raw/`），網站頁面與報告都要標示 Kaggle 連結與授權。
實作時需開啟 Kaggle 頁面確認授權條款，並將確認結果寫進 `datasets.yaml`。

### 3.1 資料集 A：Bike Sharing（每日租借量）

| 項目 | 內容 |
|---|---|
| Kaggle 連結 | https://www.kaggle.com/datasets/lakshmi25npathi/bike-sharing-dataset |
| 原始出處 | UCI Machine Learning Repository：https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset |
| 使用檔案 | `day.csv`（731 筆，2011–2012 每日資料） |
| 欄位（16 欄） | instant, dteday, season, yr, mnth, holiday, weekday, workingday, weathersit, temp, atemp, hum, windspeed, casual, registered, cnt |
| 目標變數 | `cnt`（每日總租借量） |
| 業務問題 | 預測每日租借需求，作為車輛調度與維修排程的依據 |

**資料準備的必要處理**
- `casual + registered = cnt`，這兩欄會造成**資料洩漏**，必須移除，並在 Data Preparation 中明確說明原因。
- `instant` 是流水號，移除。
- `dteday` 不作為特徵，只用來排序和繪製時間軸。
- `season`、`weathersit`、`mnth`、`weekday` 是類別變數，做 one-hot 編碼並丟棄一個基準類別。
- `temp` 與 `atemp` 高度共線，交由 VIF 步驟處理，結果需要在網頁上呈現。
- **資料切分依時間順序**：前 80% 為訓練集，後 20% 為測試集，不可隨機切分。

### 3.2 資料集 B：House Sales in King County, USA

| 項目 | 內容 |
|---|---|
| Kaggle 連結 | https://www.kaggle.com/datasets/harlfoxem/housesalesprediction |
| 使用檔案 | `kc_house_data.csv`（約 21,613 筆） |
| 欄位（21 欄） | id, date, price, bedrooms, bathrooms, sqft_living, sqft_lot, floors, waterfront, view, condition, grade, sqft_above, sqft_basement, yr_built, yr_renovated, zipcode, lat, long, sqft_living15, sqft_lot15 |
| 目標變數 | `price` |
| 業務問題 | 依房屋條件估算合理成交價，協助買賣雙方判斷價格 |

**資料準備的必要處理**
- `id` 移除。
- `date` 轉成 `sale_year`、`sale_month`。
- `yr_renovated` 轉成 `is_renovated`（0/1）和 `house_age`（售出年 − 建造年）。
- `sqft_living = sqft_above + sqft_basement` 是完全共線，移除 `sqft_above`，`sqft_basement` 轉成 `has_basement`。
- `zipcode` 有 70 個類別，不做 one-hot，以 `lat`、`long` 代表位置，並在文件中說明這個取捨。
- 異常值：`bedrooms = 33` 這類明顯的錯誤資料要移除，並在網頁上列出移除的規則與筆數。
- 目標變數取 `log(price)` 建模。預測值與區間都要反轉換回原始價格再顯示，並說明反轉換後的區間不對稱是正常現象。
- 資料切分：隨機 80/20，`random_state = 42`。

---

## 4. 系統架構

```
┌────────────────────────── GitHub Actions ──────────────────────────┐
│ 1. Python 分析管線  →  web/public/data/*.json  ＋  reports/figures/*.png │
│ 2. Vite 建置 React  →  dist/                                        │
│ 3. 發布 dist/ 到 GitHub Pages                                      │
└────────────────────────────────────────────────────────────────────┘

瀏覽器
├─ 內建資料集：讀取 data/<dataset_id>.json，只負責繪圖與呈現
└─ 自訂 URL：fetch → PapaParse → JS 計算統計 → 繪圖
```

### 4.1 技術選擇

| 項目 | 選擇 | 理由 |
|---|---|---|
| 分析 | Python 3.11、pandas、numpy、statsmodels、scikit-learn、matplotlib | statsmodels 可以直接輸出信賴區間（mean_ci）與預測區間（obs_ci） |
| 前端 | React 18 + Vite + TypeScript | 靜態建置，適合 GitHub Pages |
| 圖表 | Plotly.js（cartesian 精簡版）+ react-plotly.js | 一個函式庫就涵蓋帶狀區間、熱圖、Q-Q 圖、直方圖 |
| CSV 解析 | PapaParse | 處理自訂 URL 與上傳檔案 |
| 部署 | GitHub Actions + GitHub Pages | Vite `base` 設為 `/<repo-name>/` |
| 套件版本 | `requirements.txt` 與 `package-lock.json` 固定版本 | 確保管線結果可重現 |

### 4.2 目錄結構

```
/
├─ analysis/
│  ├─ data/raw/                 # day.csv、kc_house_data.csv
│  ├─ datasets.yaml             # 資料集中繼資料（名稱、連結、授權、目標變數）
│  ├─ content/                  # CRISP-DM 文字內容（網站與報告共用）
│  │  ├─ bike.zh-TW.yaml
│  │  └─ house.zh-TW.yaml
│  ├─ pipeline/                 # 依 CRISP-DM 階段拆分的模組
│  └─ run_pipeline.py           # 進入點：輸出 JSON 與 PNG
├─ web/                         # React 專案
│  └─ public/data/              # 管線輸出，由 CI 產生，不提交進版控
├─ reports/
│  ├─ figures/                  # 管線輸出的 PNG
│  ├─ build_report.py           # 產生 Word 報告
│  ├─ infographic/              # A4 資訊圖表模板與輸出
│  └─ output/                   # report.docx、infographic.pdf、infographic.png
├─ .github/workflows/deploy.yml
└─ README.md
```

### 4.3 文字內容單一來源

CRISP-DM 各步驟的說明文字寫在 `analysis/content/*.yaml`，可以使用 `{{metrics.test.r2}}` 這類佔位符，由管線代入實際數值。
網站與 Word 報告都從同一份內容產生，以確保數字一致。**任何文件中都不可以手打結果數字。**

---

## 5. 分析管線（依 CRISP-DM 階段）

兩個資料集共用同一套流程，差異只寫在各自的設定裡。

### 5.1 Business Understanding
從 content yaml 讀取：業務問題、分析目標、成功標準（例如測試集 R² 的目標值）、預測結果的使用方式。

### 5.2 Data Understanding
輸出以下資訊：
- 筆數、欄數、各欄型別、缺失值數量、重複列數量
- 數值欄的敘述統計（count、mean、std、min、四分位數、max）
- 相關係數矩陣
- 目標變數分布
- 與目標變數相關性最高的前 5 個特徵
- 特徵數量的檢核結果（必須大於 13、小於 40；計算時排除目標變數與 ID 欄）

### 5.3 Data Preparation
依第 3 節的規則處理。每一個處理步驟都要以結構化的方式記錄（步驟名稱、原因、影響筆數或欄數），供網頁和報告列出。

### 5.4 Feature Selection
三種方法都只在**訓練集**上執行：

1. **相關係數篩選**：列出每個特徵與目標變數的 |r|，並標示彼此相關度大於 0.8 的特徵對。
2. **VIF**：迭代移除 VIF 最高且大於 10 的特徵，記錄每一輪移除的特徵與當下的 VIF 值。
3. **逐步回歸**：以 VIF 篩選後的特徵為起點，執行雙向逐步選擇（以 AIC 為準則），記錄每一步加入或移除的特徵與 AIC。

最終特徵集採用逐步回歸的結果。網頁上需要用表格呈現三種方法的比較，標示每個特徵在各方法中是否被保留。

### 5.5 Modeling

| 資料集 | 模型 | 說明 |
|---|---|---|
| Bike | 單純線性回歸 | `cnt ~ 相關係數最高的單一特徵`（預期是 temp 或 atemp，以實際計算結果為準） |
| Bike | 多元線性回歸（全部特徵） | 作為比較基準 |
| Bike | 多元線性回歸（選擇後的特徵） | 主要模型 |
| Bike | Auto Regression | 對 `cnt` 建立 AR(p)，以 AIC 選擇 p（上限 14）；測試期採**一步預測**（使用實際的前期值），附預測區間 |
| House | 單純線性回歸 | `log(price) ~ sqft_living` |
| House | 多元線性回歸（全部特徵） | 作為比較基準 |
| House | 多元線性回歸（選擇後的特徵） | 主要模型 |

OLS 模型都使用 statsmodels 的 `OLS`，並輸出係數表：係數、標準誤、t 值、p 值、95% 信賴區間。

### 5.6 Evaluation
- 測試集指標：R²、Adjusted R²、RMSE、MAE。House 的 RMSE 與 MAE 要以**原始價格單位**計算。
- 5-fold 交叉驗證：House 使用 `KFold(shuffle=True, random_state=42)`；Bike 使用 `TimeSeriesSplit(n_splits=5)`。輸出每一折的分數與平均 ± 標準差。
- 預測區間覆蓋率：測試集實際值落在 95% 預測區間內的比例，理想值應接近 95%。
- 殘差診斷：殘差對預測值散佈圖、Q-Q 圖、殘差直方圖。
- 模型比較表：所有模型並列，標示最佳模型。
- 結論文字：由 content yaml 的模板產生，說明是否達到 Business Understanding 設定的成功標準。

### 5.7 預測區間的計算
- OLS：`get_prediction(X_test).summary_frame(alpha=0.05)`
  - 信賴區間：`mean_ci_lower`、`mean_ci_upper`
  - 預測區間：`obs_ci_lower`、`obs_ci_upper`
- AR：只提供預測區間，計算方式為一步預測 ± 1.96 × 殘差標準差。網頁上要註明 AR 只顯示預測區間。
- House：上述區間在 log 尺度計算後，再取 exp 轉回價格。

### 5.8 Deployment
說明本網站的部署方式：建置流程、GitHub Pages 網址、模型如何重新訓練（更新 CSV 後推送即會自動重跑管線）、模型的限制與後續改進方向。

---

## 6. JSON 資料契約

每個內建資料集輸出一個檔案：`web/public/data/<dataset_id>.json`，`dataset_id` 為 `bike` 或 `house`。

```jsonc
{
  "meta": {
    "id": "bike",
    "name": "Bike Sharing（每日租借量）",
    "kaggle_url": "...",
    "origin_url": "...",
    "license": "...",
    "file": "day.csv",
    "target": "cnt",
    "generated_at": "ISO 8601 時間"
  },
  "crisp_dm": {
    "business_understanding": { "markdown": "..." },
    "data_understanding":     { "markdown": "...", "stats_ref": "data_understanding" },
    "data_preparation":       { "markdown": "...", "steps": [ { "name": "", "reason": "", "affected": "" } ] },
    "modeling":               { "markdown": "..." },
    "evaluation":             { "markdown": "..." },
    "deployment":             { "markdown": "..." }
  },
  "data_understanding": {
    "n_rows": 0, "n_cols": 0, "n_features": 0,
    "columns": [ { "name": "", "dtype": "", "missing": 0, "unique": 0 } ],
    "describe": { "<col>": { "mean": 0, "std": 0, "min": 0, "q1": 0, "median": 0, "q3": 0, "max": 0 } },
    "correlation": { "labels": [], "matrix": [[]] },
    "target_distribution": { "bins": [], "counts": [] },
    "preview": [ {} ]
  },
  "feature_selection": {
    "correlation": [ { "feature": "", "abs_r": 0 } ],
    "high_corr_pairs": [ { "a": "", "b": "", "r": 0 } ],
    "vif_rounds": [ { "round": 1, "removed": "", "vif": 0, "remaining": [] } ],
    "stepwise_steps": [ { "step": 1, "action": "add|remove", "feature": "", "aic": 0 } ],
    "comparison": [ { "feature": "", "corr_kept": true, "vif_kept": true, "stepwise_kept": true } ],
    "final_features": []
  },
  "models": [
    {
      "id": "mlr_selected",
      "label": "多元線性回歸（選擇後特徵）",
      "type": "slr|mlr|ar",
      "is_best": true,
      "features": [],
      "coefficients": [ { "name": "", "coef": 0, "std_err": 0, "t": 0, "p": 0, "ci_low": 0, "ci_high": 0 } ],
      "metrics": { "r2": 0, "adj_r2": 0, "rmse": 0, "mae": 0, "pi_coverage": 0 },
      "cv": { "scores_r2": [], "mean": 0, "std": 0 },
      "prediction": {
        "x_kind": "index|date|feature",
        "x_label": "",
        "points": [ { "x": 0, "actual": 0, "pred": 0, "ci_low": null, "ci_high": null, "pi_low": 0, "pi_high": 0 } ]
      },
      "residuals": { "fitted": [], "resid": [], "qq_theoretical": [], "qq_sample": [] }
    }
  ]
}
```

**資料量控制**：House 的測試集約 4,300 筆，`prediction.points` 與 `residuals` 依預測值排序後均勻抽樣至最多 500 點，並在 meta 記錄是否有抽樣。每個 JSON 檔需小於 2 MB。

---

## 7. 前端規格

### 7.1 版面
```
┌─────────────────────────────────────────────┐
│ 網站標題 │ 資料集：[ 下拉選單 ▾ ]            │
├─────────────────────────────────────────────┤
│ 資料集資訊卡：名稱、來源連結、授權、筆數、特徵數、目標變數 │
├─────────────────────────────────────────────┤
│ CRISP-DM 步驟條：①業務理解 ②資料理解 ③資料準備 ④建模 ⑤評估 ⑥部署 │
├─────────────────────────────────────────────┤
│ 目前步驟的內容區                              │
└─────────────────────────────────────────────┘
```
- 下拉選單有三個選項：`Bike Sharing（每日租借量）`、`King County 房價`、`自訂 CSV URL`。
- 切換資料集時保留目前所在的 CRISP-DM 步驟。
- 網址使用 hash 記錄狀態（例如 `#bike-modeling`），方便直接分享特定頁面。
- 支援 RWD 與深淺色模式。

### 7.2 各步驟的內容（內建資料集）

| 步驟 | 內容 |
|---|---|
| ① Business Understanding | 業務問題、目標、成功標準 |
| ② Data Understanding | 欄位表、缺失值、敘述統計、相關係數熱圖、目標變數分布、資料預覽（前 10 筆） |
| ③ Data Preparation | 處理步驟表（步驟、原因、影響）、處理前後的欄數與筆數；Bike 必須凸顯資料洩漏的說明 |
| ④ Modeling | 特徵選擇：三種方法的過程與比較表、最終特徵；模型清單與係數表（p 值小於 0.05 標示） |
| ⑤ Evaluation | 模型比較表、**預測圖**、殘差圖、Q-Q 圖、交叉驗證結果、預測區間覆蓋率、結論 |
| ⑥ Deployment | 部署架構、重新訓練方式、限制與改進方向 |

### 7.3 預測圖規格（作業核心）
- 可以切換要顯示的模型。
- **單純線性回歸**：X 軸為特徵，散佈點為實際值，加上回歸線、信賴區間帶（較深色）、預測區間帶（較淺色）。
- **多元線性回歸**：X 軸為依預測值排序的樣本序號，畫出實際值點、預測值線、信賴區間帶、預測區間帶；另外提供一張「實際值 vs 預測值」散佈圖，附 y = x 參考線。
- **AR**：X 軸為日期，畫出訓練期的實際值、測試期的實際值與一步預測、預測區間帶。
- 圖例清楚區分「95% 信賴區間」與「95% 預測區間」。區間帶的顏色不能只靠色相區分，還要以透明度深淺區別。
- 圖下方附一行說明：信賴區間代表平均預測值的不確定性，預測區間代表單筆新觀測值的範圍。

### 7.4 自訂 CSV URL
- 輸入框預設顯示範例網址：`https://raw.githubusercontent.com/Avik-Jain/100-Days-Of-ML-Code/master/datasets/50_Startups.csv`
- 另外提供「上傳 CSV 檔」作為替代方式。
- 處理流程：fetch → PapaParse（`dynamicTyping`、`skipEmptyLines`）→ 型別推斷（數值、類別、日期）→ 計算統計 → 繪圖。
- 顯示內容：筆數、欄數、各欄型別、缺失值、數值欄的敘述統計、相關係數熱圖、各欄分布（數值欄用直方圖、類別欄用前 10 名長條圖）、資料預覽。
- **不受特徵數 13–40 的限制**，任意欄數都要能正常顯示。
- 限制：超過 50,000 筆時只取前 50,000 筆，並提示使用者；欄數超過 50 時，熱圖只顯示數值欄的前 50 欄。
- 錯誤處理（顯示中文訊息，不可讓頁面崩潰）：
  - 網址格式錯誤
  - 網路錯誤或 CORS 被拒：說明原因，並建議改用 raw 檔案網址或上傳檔案
  - 不是 CSV 或解析失敗
  - 空檔案
- 自訂 URL 模式**只顯示資料資訊區**，CRISP-DM 步驟條與建模相關區塊不顯示。
- 統計計算放在 `web/src/lib/stats/`，以純函式撰寫並附單元測試（Vitest）。

---

## 8. 部署

`.github/workflows/deploy.yml` 在推送到 `main` 時觸發，依序執行：
1. checkout
2. 設定 Python 3.11，安裝 `requirements.txt`
3. 執行 `python analysis/run_pipeline.py`；失敗時中止部署
4. 設定 Node（LTS），在 `web/` 執行 `npm ci`、`npm run test`、`npm run build`
5. 以 `actions/upload-pages-artifact` 與 `actions/deploy-pages` 發布

管線必須是決定性的（固定 random seed），重複執行要產生相同的數值。

---

## 9. 網站完成後的繳交物

以下三項都在網站完成並部署之後製作，所有數值與圖片一律取自管線輸出。

### 9.1 README.md
內容包含：
- 專案簡介與網站連結
- 資料集來源、連結與授權
- 架構圖
- 本機執行方式（管線、前端）
- 部署方式
- CRISP-DM 六步驟摘要（每步 2–3 句）
- 主要結果表
- 目錄結構

### 9.2 Word 書面報告（`reports/output/report.docx`）
- 以 `python-docx` 撰寫 `reports/build_report.py` 產生報告，讓結果可以重現。
- 文字取自 `analysis/content/*.yaml`，數值取自 JSON，圖片取自 `reports/figures/`。
- 章節：
  1. 封面（標題、姓名欄位留空、日期）
  2. 摘要
  3. 資料集介紹與來源
  4. Business Understanding
  5. Data Understanding
  6. Data Preparation
  7. Modeling（含特徵選擇）
  8. Evaluation（含預測圖、模型比較）
  9. Deployment
  10. 結論與限制
  11. 參考資料
- 兩個資料集在第 4–9 章各自成小節。
- 圖表要有編號與標題（例如「圖 3：Bike Sharing 多元線性回歸預測圖」），表格同樣編號。
- 沒有頁數限制。字型使用標楷體或微軟正黑體，標題層級使用 Word 內建樣式，以便自動產生目錄。

### 9.3 A4 直式資訊圖表（`reports/output/infographic.pdf` 與 `.png`）
- 尺寸 210 × 297 mm。PNG 為 300 dpi。
- 製作方式：在 `reports/infographic/` 建立 HTML/CSS 模板，以 JSON 帶入數值，再用 Playwright 匯出 PDF 與 PNG。
- 版面由上到下：
  1. 標題
  2. CRISP-DM 六步驟流程條
  3. 兩個資料集卡片（來源、筆數、特徵數、目標變數）
  4. 每個資料集的最佳模型與關鍵指標（R²、RMSE），附一張簡化的預測圖（含區間帶）
  5. 特徵選擇的重點（例如「16 → 9 個特徵」）
  6. 網站網址與 QR code
- 文字精簡、字級要大：內文不小於 11 pt，數字指標以大字突顯。

---

## 10. 驗收條件

| # | 情境 | 預期結果 |
|---|---|---|
| 1 | 開啟網站 | 預設顯示 Bike Sharing，資訊卡上看得到 Kaggle 連結 |
| 2 | 下拉選單切換到 King County 房價 | 資訊卡、所有步驟內容與圖表都換成房價資料 |
| 3 | 兩個資料集的 Data Understanding | 顯示的特徵數都介於 14 到 39 |
| 4 | Bike 的 Data Preparation | 看得到移除 casual、registered 的步驟與資料洩漏的說明 |
| 5 | Modeling 頁 | 看得到三種特徵選擇方法的過程與比較表 |
| 6 | Evaluation 頁 | 每個模型都有測試集指標與交叉驗證結果 |
| 7 | 預測圖 | 單純與多元線性回歸都有信賴區間帶與預測區間帶；AR 有預測區間帶；圖例可以清楚區分 |
| 8 | 自訂 URL 輸入範例網址 | 顯示 50 筆、5 欄的資料資訊，不顯示建模區塊 |
| 9 | 自訂 URL 輸入無效或被 CORS 阻擋的網址 | 顯示中文錯誤訊息與替代建議，頁面不崩潰 |
| 10 | 上傳本機 CSV | 結果與 URL 模式相同 |
| 11 | 手機寬度（375px） | 版面不出現橫向捲動，圖表可以在容器內捲動 |
| 12 | 推送到 main | Actions 自動跑管線、測試、建置並部署成功 |
| 13 | 重跑管線兩次 | 輸出的數值完全相同 |
| 14 | 比對網站、報告、資訊圖表 | 三者的指標數字一致 |

---

## 11. 實作階段（供 tasks.md 拆分）

1. **專案骨架**：建立目錄結構、放入兩份 CSV、`datasets.yaml`、確認並記錄授權
2. **分析管線（Bike）**：Data Understanding → Preparation → 特徵選擇 → 建模（SLR、MLR、AR）→ 評估 → 輸出 JSON 與 PNG
3. **分析管線（House）**：同上（SLR、MLR）
4. **CRISP-DM 內容**：撰寫兩份 content yaml，以佔位符代入數值
5. **前端：內建資料集**：版面、下拉選單、步驟條、各步驟頁面、預測圖
6. **前端：自訂 URL**：統計函式與單元測試、URL 與上傳、錯誤處理
7. **部署**：GitHub Actions、確認 Pages 網址可以正常使用
8. **README**
9. **Word 報告**
10. **A4 資訊圖表**

每個階段完成後，先對照第 10 節中相關的驗收條件確認，再進入下一階段。
