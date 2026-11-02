# Spec Delta

## Purpose

在推送到 `main` 時自動重跑分析管線、執行前端測試、建置靜態網站並發布到 GitHub Pages，讓更新資料或程式後網站自動反映最新結果。

## ADDED Requirements

### Requirement: 自動建置與部署
推送到 `main` 時 SHALL 自動依序執行：取出程式碼、安裝固定版本的 Python 相依套件、執行分析管線、安裝固定版本的前端相依套件、執行前端單元測試、建置前端、發布到 GitHub Pages。任一步驟失敗時 MUST 中止，不可發布。

#### Scenario: 推送後自動部署
- **WHEN** 開發者推送一個 commit 到 `main`
- **THEN** 工作流程依序完成管線、測試、建置與部署，GitHub Pages 網址顯示最新版本的網站

#### Scenario: 管線失敗時不部署
- **WHEN** 分析管線以非零狀態結束
- **THEN** 工作流程失敗，GitHub Pages 維持上一個成功版本

#### Scenario: 測試失敗時不部署
- **WHEN** 前端單元測試有任一失敗
- **THEN** 工作流程失敗且不發布

### Requirement: 管線輸出不進版控
網站所需的 JSON SHALL 在建置時由管線產生，MUST NOT 提交進版控。

#### Scenario: 乾淨環境可完整建置
- **WHEN** 在剛取出的 repo（沒有任何管線輸出）執行工作流程
- **THEN** 網站仍能完整建置並顯示兩個內建資料集

### Requirement: 子路徑可正常運作
部署後的網站 SHALL 在 GitHub Pages 的 repo 子路徑（`https://<user>.github.io/<repo>/`）下正常載入所有資源與資料檔，包含以 hash 網址直接開啟的情況。

#### Scenario: 子路徑載入資源
- **WHEN** 使用者開啟 `https://<user>.github.io/<repo>/#house-evaluation`
- **THEN** 頁面、樣式、腳本與 `house.json` 都成功載入，畫面顯示房價資料的評估步驟
