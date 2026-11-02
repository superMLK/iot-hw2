# Spec Delta

## Purpose

在網站完成並部署後，產出 README、Word 書面報告與 A4 直式資訊圖表三項繳交物，所有數值與圖片都取自分析管線的輸出，確保與網站一致。

## ADDED Requirements

### Requirement: 數值一致
README、Word 報告與資訊圖表中的所有結果數值與圖片 MUST 取自分析管線的輸出（JSON 與 `reports/figures/` 的 PNG），不可手動輸入；同一指標在網站、報告與資訊圖表中 SHALL 以相同的值與小數位數呈現。

#### Scenario: 三者指標一致
- **WHEN** 比對網站、Word 報告與資訊圖表中同一資料集最佳模型的測試集 R² 與 RMSE
- **THEN** 三者的數值完全相同

#### Scenario: 管線重跑後繳交物更新
- **WHEN** 管線輸出改變後重新產生報告與資訊圖表
- **THEN** 報告與資訊圖表中的數值隨之更新，不需要手動修改

### Requirement: README
`README.md` SHALL 包含：專案簡介與網站連結、兩個資料集的來源連結與授權、架構圖、本機執行方式（管線與前端）、部署方式、CRISP-DM 六步驟摘要（每步 2–3 句）、主要結果表、目錄結構。README 中寫出的本機執行指令 MUST 能照抄執行成功。

#### Scenario: README 指令可執行
- **WHEN** 在乾淨的 clone 中依 README 的本機執行步驟操作
- **THEN** 管線與前端開發伺服器都能成功啟動

#### Scenario: README 標示資料來源
- **WHEN** 閱讀 README
- **THEN** 看得到兩個資料集的 Kaggle 連結與授權

### Requirement: Word 書面報告
報告 SHALL 以程式產生到 `reports/output/report.docx`，可重複產生。章節依序為：封面（標題、姓名欄位留空、日期）、摘要、資料集介紹與來源、Business Understanding、Data Understanding、Data Preparation、Modeling（含特徵選擇）、Evaluation（含預測圖與模型比較）、Deployment、結論與限制、參考資料；第 4–9 章中兩個資料集各自成小節。圖與表 SHALL 各自連續編號並附標題（例如「圖 3：Bike Sharing 多元線性回歸預測圖」）。中文字型 SHALL 使用標楷體或微軟正黑體，標題 SHALL 使用 Word 內建標題樣式以便自動產生目錄。

#### Scenario: 章節完整
- **WHEN** 開啟產生的 `report.docx`
- **THEN** 依序看到上述 11 個章節，且第 4–9 章各有 Bike 與 House 兩個小節

#### Scenario: 圖表編號
- **WHEN** 檢查報告中的圖與表
- **THEN** 每張圖都有「圖 N：...」標題，每個表都有「表 N：...」標題，編號從 1 開始連續

#### Scenario: 可自動產生目錄
- **WHEN** 在 Word 中插入目錄
- **THEN** 章節標題能被辨識並列入目錄

### Requirement: A4 資訊圖表
資訊圖表 SHALL 輸出 `reports/output/infographic.pdf`（210 × 297 mm，直式，單頁）與 `reports/output/infographic.png`（300 dpi，即 2480 × 3508 像素）。版面由上到下 SHALL 包含：標題、CRISP-DM 六步驟流程條、兩個資料集卡片（來源、筆數、特徵數、目標變數）、每個資料集的最佳模型與關鍵指標（R²、RMSE）並附一張含區間帶的簡化預測圖、特徵選擇重點（例如「N → M 個特徵」，數字取自管線）、網站網址與可掃描的 QR code。內文字級 MUST 不小於 11 pt，數字指標以大字突顯。文字 SHALL 使用繁體中文。

#### Scenario: 尺寸正確
- **WHEN** 檢查輸出的 PDF 與 PNG
- **THEN** PDF 為單頁 A4 直式，PNG 為 2480 × 3508 像素

#### Scenario: QR code 可用
- **WHEN** 用手機掃描資訊圖表上的 QR code
- **THEN** 開啟的是網站的 GitHub Pages 網址
