# Proposal

## Why

課程作業要求依 CRISP-DM 流程，用線性回歸（單純、多元、Auto Regression）分析兩個 Kaggle 公開資料集，並以可切換資料集、可輸入任意 CSV URL 的網站呈現，另外繳交 README、Word 報告與 A4 資訊圖表。目前專案只有一份技術設計（專案根目錄 `design.md`），還沒有任何程式碼，需要把設計轉成可驗收的規格與實作步驟。

## What Changes

- 新增 Python 建置期分析管線：對 Bike Sharing（`day.csv`）與 King County 房價（`kc_house_data.csv`）執行資料理解、資料準備、特徵選擇（相關係數、VIF、雙向逐步回歸）、建模（SLR、MLR、AR）、評估（測試集指標、交叉驗證、預測區間覆蓋率、殘差診斷），輸出每個資料集一份 JSON 與一組 PNG 圖檔。
- 新增 CRISP-DM 文字內容的單一來源（每個資料集一份 yaml，數值以佔位符代入），網站與報告共用，任何文件都不手打結果數字。
- 新增 React 靜態網站：資料集下拉選單（Bike、House、自訂 CSV URL）、資料集資訊卡、CRISP-DM 六步驟條、各步驟內容頁、附信賴區間與預測區間的預測圖；網址以 hash 記錄狀態，支援 RWD 與深淺色模式。
- 新增自訂 CSV 檢視：可輸入 URL 或上傳檔案，在瀏覽器中計算並顯示資料基本資訊，含中文錯誤處理；不做建模。
- 新增 GitHub Actions 工作流程：推送到 `main` 時依序執行管線、前端測試、建置並部署到 GitHub Pages。
- 新增繳交物：README、以程式產生的 Word 書面報告、以 HTML 模板匯出的 A4 直式資訊圖表（PDF＋300 dpi PNG）。

## Capabilities

### New Capabilities
- `regression-analysis-pipeline`: 建置期分析管線，涵蓋兩個內建資料集的資料理解、資料準備、特徵選擇、建模、評估、區間計算、CRISP-DM 文字代入，以及 JSON 資料契約與圖檔輸出，並保證結果可重現。
- `dataset-explorer-ui`: 內建資料集的網站介面，包含資料集切換、資訊卡、CRISP-DM 步驟條與各步驟內容、預測圖規格、hash 狀態、RWD 與深淺色模式。
- `custom-csv-explorer`: 自訂 CSV（URL 或上傳）的瀏覽器端資料檢視，包含型別推斷、統計、圖表、資料量限制與錯誤處理。
- `site-deployment`: 推送到 `main` 時自動執行管線、測試、建置並發布到 GitHub Pages 的流程。
- `submission-deliverables`: README、Word 書面報告、A4 資訊圖表三項繳交物的內容、格式，以及與網站數值一致的要求。

### Modified Capabilities
（無，專案目前沒有既有 spec。）

## Impact

- **新增目錄**：`analysis/`（資料、設定、內容、管線）、`web/`（React 專案）、`reports/`（圖檔、報告與資訊圖表產生器、輸出）、`.github/workflows/deploy.yml`、`README.md`。
- **新增相依套件**：Python 3.11（pandas、numpy、statsmodels、scikit-learn、matplotlib、PyYAML、python-docx、playwright、qrcode）；Node LTS（React 18、Vite、TypeScript、Plotly.js cartesian 精簡版、react-plotly.js、PapaParse、Vitest）。版本以 `requirements.txt` 與 `package-lock.json` 鎖定。
- **外部系統**：需要一個 GitHub repo 並開啟 GitHub Pages（Source 設為 GitHub Actions）；兩份資料集需從 Kaggle（或其原始出處）取得並放入 repo。
- **對外操作**：建立 GitHub repo、推送與部署屬於對外動作，實作時需由使用者確認後才執行。
