# Spec Delta

## Purpose

讓使用者輸入任意 CSV 網址或上傳本機 CSV，在瀏覽器中即時檢視該資料集的基本資訊（欄位、型別、缺失值、統計、分布、相關係數），不需要後端伺服器。

## ADDED Requirements

### Requirement: 輸入方式
選擇 `自訂 CSV URL` 後，網站 SHALL 提供網址輸入框與「上傳 CSV 檔」兩種輸入方式。輸入框 SHALL 預先填入範例網址 `https://raw.githubusercontent.com/Avik-Jain/100-Days-Of-ML-Code/master/datasets/50_Startups.csv`。資料 MUST 只在瀏覽器中處理，不傳送到任何伺服器（取得 URL 內容的請求除外）。

#### Scenario: 範例網址
- **WHEN** 使用者以預設的範例網址載入資料
- **THEN** 顯示筆數 50、欄數 5 的資料資訊

#### Scenario: 上傳檔案與 URL 結果相同
- **WHEN** 使用者上傳與範例網址內容相同的本機 CSV
- **THEN** 顯示的資料資訊與以 URL 載入時相同

### Requirement: 型別推斷與資料資訊
網站 SHALL 解析 CSV（自動轉換數值、略過空白列），將每一欄推斷為數值、類別或日期，並顯示：筆數、欄數、各欄型別、各欄缺失值數量、數值欄的敘述統計（count、mean、std、min、q1、median、q3、max）、數值欄的相關係數熱圖、各欄分布（數值欄用直方圖，類別欄用前 10 名長條圖）、資料預覽。這些統計計算 MUST 以可單獨測試的純函式實作並附單元測試。

#### Scenario: 混合型別的欄位
- **WHEN** 載入的 CSV 有數值欄、文字欄與日期欄
- **THEN** 欄位表分別標示為數值、類別、日期，只有數值欄出現在敘述統計與相關係數熱圖中

#### Scenario: 類別欄分布
- **WHEN** 某個類別欄有超過 10 個不同值
- **THEN** 該欄的長條圖只顯示出現次數最多的前 10 個值

#### Scenario: 缺失值計算
- **WHEN** 某欄有空字串或空白儲存格
- **THEN** 這些儲存格被計入該欄的缺失值數量，且不影響該欄的敘述統計

### Requirement: 不受特徵數限制
自訂 CSV 模式 MUST NOT 套用 13–40 的特徵數限制，任意欄數的 CSV 都 SHALL 能正常顯示。

#### Scenario: 欄數很少的 CSV
- **WHEN** 載入只有 2 欄的 CSV
- **THEN** 正常顯示資料資訊，沒有特徵數不符的警告或錯誤

### Requirement: 資料量限制
當資料超過 50,000 筆時，網站 SHALL 只處理前 50,000 筆並明確提示使用者。當數值欄超過 50 欄時，相關係數熱圖 SHALL 只顯示前 50 個數值欄並提示。

#### Scenario: 超過 50,000 筆
- **WHEN** 載入 60,000 筆的 CSV
- **THEN** 顯示的筆數為 50,000，並出現「只取前 50,000 筆」的提示

#### Scenario: 超過 50 個數值欄
- **WHEN** 載入有 80 個數值欄的 CSV
- **THEN** 熱圖只包含前 50 個數值欄，並有提示說明

### Requirement: 錯誤處理
發生錯誤時網站 SHALL 顯示中文錯誤訊息且頁面不可崩潰，至少涵蓋：網址格式錯誤、網路錯誤或 CORS 被拒（MUST 說明可能原因，並建議改用 raw 檔案網址或上傳檔案）、內容不是 CSV 或解析失敗、空檔案。錯誤後使用者 SHALL 可以直接重新輸入或上傳。

#### Scenario: 網址格式錯誤
- **WHEN** 使用者輸入 `abc` 並送出
- **THEN** 顯示網址格式錯誤的中文訊息，不發出網路請求

#### Scenario: CORS 被阻擋
- **WHEN** 使用者輸入一個不允許跨來源讀取的網址
- **THEN** 顯示中文訊息說明可能是網路或 CORS 問題，並建議改用 raw 網址或上傳檔案

#### Scenario: 空檔案
- **WHEN** 使用者上傳 0 位元組或只有空白的檔案
- **THEN** 顯示「檔案是空的」之類的中文訊息

#### Scenario: 非 CSV 內容
- **WHEN** 網址回傳的是 HTML 網頁
- **THEN** 顯示內容不是有效 CSV 的中文訊息

### Requirement: 自訂模式只顯示資料資訊
自訂 CSV 模式 SHALL 只顯示資料資訊區，MUST NOT 顯示 CRISP-DM 步驟條、特徵選擇、建模、預測圖或評估相關區塊。

#### Scenario: 不顯示建模區塊
- **WHEN** 使用者在自訂模式成功載入資料
- **THEN** 頁面上沒有 CRISP-DM 步驟條，也沒有任何模型、特徵選擇或預測圖
