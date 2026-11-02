# Spec Delta

## Purpose

在建置階段對兩個內建資料集（Bike Sharing、King County 房價）依 CRISP-DM 完成資料理解、資料準備、特徵選擇、線性回歸建模與評估，並輸出網站與繳交物共用的結構化結果。

## ADDED Requirements

### Requirement: 資料集來源與中繼資料
管線 SHALL 只使用存放在 repo 內的兩份 CSV（Bike：`day.csv`；House：`kc_house_data.csv`），並從資料集中繼資料檔讀取每個資料集的 id、顯示名稱、Kaggle 連結、原始出處連結、授權、檔名與目標變數。授權欄位 MUST 是實際查閱 Kaggle 頁面後的結果，不可留空或填佔位文字。

#### Scenario: 輸出包含來源資訊
- **WHEN** 管線完成 Bike 資料集的處理
- **THEN** 輸出的 `meta` 包含 `id = "bike"`、`target = "cnt"`、`file = "day.csv"`、非空的 `kaggle_url` 與 `license`

#### Scenario: 中繼資料缺漏時中止
- **WHEN** 中繼資料檔中某個資料集缺少 `kaggle_url` 或 `license`
- **THEN** 管線以非零狀態結束，並在錯誤訊息中指出缺少的欄位

### Requirement: 資料理解輸出
對每個資料集，管線 SHALL 根據原始資料輸出：筆數、欄數、特徵數、各欄型別、缺失值數量、唯一值數量、重複列數量、數值欄的敘述統計（count、mean、std、min、q1、median、q3、max）、數值欄的相關係數矩陣、目標變數分布（直方圖的 bins 與 counts）、與目標變數相關性最高的前 5 個特徵，以及前 10 筆資料預覽。特徵數 MUST 以「原始欄數減去目標變數與 ID 欄」計算。

#### Scenario: 特徵數符合作業限制
- **WHEN** 管線計算兩個資料集的特徵數
- **THEN** Bike 與 House 的 `n_features` 都大於 13 且小於 40

#### Scenario: 特徵數超出範圍時中止
- **WHEN** 某個資料集的特徵數小於等於 13 或大於等於 40
- **THEN** 管線以非零狀態結束並說明是哪個資料集不符合

### Requirement: Bike 資料準備規則
Bike 資料準備 SHALL 依序：移除 `casual` 與 `registered`（原因：兩者相加等於 `cnt`，會造成資料洩漏）、移除流水號 `instant`、`dteday` 僅用於排序與繪製時間軸而不作為特徵、對 `season`、`weathersit`、`mnth`、`weekday` 做 one-hot 編碼並丟棄一個基準類別、依時間順序以前 80% 為訓練集與後 20% 為測試集。管線 MUST NOT 對 Bike 做隨機切分。

#### Scenario: 移除資料洩漏欄位並記錄原因
- **WHEN** Bike 資料準備完成
- **THEN** 特徵中不包含 `casual`、`registered`、`instant`、`dteday`，且準備步驟紀錄中有一筆說明 `casual + registered = cnt` 造成資料洩漏

#### Scenario: 依時間切分
- **WHEN** Bike 資料切分完成
- **THEN** 測試集中最早的日期晚於訓練集中最晚的日期，且訓練集筆數為總筆數的 80%（取整）

### Requirement: House 資料準備規則
House 資料準備 SHALL：移除 `id`；將 `date` 轉成 `sale_year` 與 `sale_month`；將 `yr_renovated` 轉成 `is_renovated`（0/1），並新增 `house_age = sale_year − yr_built`；移除 `sqft_above`（與 `sqft_living`、`sqft_basement` 完全共線），並將 `sqft_basement` 轉成 `has_basement`；不使用 `zipcode`，改以 `lat`、`long` 代表位置；依明確規則移除異常值（至少包含 `bedrooms = 33` 這類錯誤資料）；以 `log(price)` 作為建模目標；以 `random_state = 42` 隨機切分 80/20。

#### Scenario: 異常值規則與筆數被記錄
- **WHEN** House 資料準備完成
- **THEN** 準備步驟紀錄中列出每條異常值規則與其移除的筆數，且資料中不再有 `bedrooms = 33` 的列

#### Scenario: 位置以經緯度代表
- **WHEN** House 資料準備完成
- **THEN** 特徵中不含 `zipcode` 與 `sqft_above`，且包含 `lat`、`long`、`has_basement`、`is_renovated`、`house_age`

### Requirement: 資料準備步驟紀錄
每個資料準備步驟 SHALL 以結構化方式記錄步驟名稱、原因與影響（影響的筆數或欄數），並輸出處理前後的筆數與欄數，供網站與報告逐條列出。

#### Scenario: 每個步驟都有原因與影響
- **WHEN** 任一資料集的資料準備完成
- **THEN** 輸出的 `crisp_dm.data_preparation.steps` 中每一筆都有非空的 `name`、`reason`、`affected`

### Requirement: 特徵選擇
特徵選擇 SHALL 只使用訓練集，依序執行三種方法並記錄過程：(1) 相關係數篩選：列出每個特徵與目標變數的 |r|，並列出彼此 |r| 大於 0.8 的特徵對；(2) VIF：每一輪移除 VIF 最高且大於 10 的特徵，記錄每一輪移除的特徵、當下的 VIF 與剩餘特徵，直到所有 VIF 都不大於 10；(3) 雙向逐步回歸：以 VIF 篩選後的特徵為候選，以 AIC 為準則，記錄每一步加入或移除的特徵與 AIC。最終特徵集 MUST 採用逐步回歸的結果，並輸出每個特徵在三種方法中是否被保留的比較表。

#### Scenario: VIF 處理 temp 與 atemp 的共線
- **WHEN** Bike 的 VIF 步驟完成
- **THEN** 最終剩餘特徵中 `temp` 與 `atemp` 不會同時存在，且 `vif_rounds` 記錄了被移除者與其 VIF 值

#### Scenario: 特徵選擇不使用測試集
- **WHEN** 改變測試集的目標值後重跑特徵選擇
- **THEN** 三種方法的結果與最終特徵集不變

#### Scenario: 比較表涵蓋所有候選特徵
- **WHEN** 特徵選擇完成
- **THEN** `comparison` 中每一個準備後的特徵都有一列，標示 `corr_kept`、`vif_kept`、`stepwise_kept`，且 `final_features` 等於 `stepwise_kept = true` 的特徵

### Requirement: 建模
管線 SHALL 為 Bike 建立四個模型：單純線性回歸（訓練集上與 `cnt` 相關係數絕對值最高的單一特徵）、多元線性回歸（全部準備後特徵，作為基準）、多元線性回歸（選擇後特徵，主要模型）、Auto Regression（對 `cnt` 建立 AR(p)，以 AIC 在 1–14 之間選 p，測試期採用實際前期值的一步預測）。管線 SHALL 為 House 建立三個模型：單純線性回歸（`log(price) ~ sqft_living`）、多元線性回歸（全部特徵）、多元線性回歸（選擇後特徵）。每個 OLS 模型 MUST 輸出係數表，含係數、標準誤、t 值、p 值、95% 信賴區間。

#### Scenario: Bike 有四個模型且包含 AR
- **WHEN** Bike 管線完成
- **THEN** `models` 中有 `type` 分別為 `slr`、`mlr`、`mlr`、`ar` 的四個模型，AR 模型記錄所選的 p 且 1 ≤ p ≤ 14

#### Scenario: House 有三個模型
- **WHEN** House 管線完成
- **THEN** `models` 中有一個 `slr`（特徵為 `sqft_living`）與兩個 `mlr`，且沒有 `ar`

#### Scenario: 係數表欄位完整
- **WHEN** 任一 OLS 模型完成
- **THEN** 其 `coefficients` 每一列都有 `name`、`coef`、`std_err`、`t`、`p`、`ci_low`、`ci_high`

### Requirement: 信賴區間與預測區間
每個 OLS 模型的測試集預測 SHALL 同時輸出 95% 信賴區間（平均預測值）與 95% 預測區間（單筆新觀測值）。AR 模型 SHALL 只輸出預測區間，計算方式為一步預測 ± 1.96 × 訓練殘差標準差，其信賴區間欄位為 `null`。House 的預測值與兩種區間 MUST 先在 log 尺度計算，再取 exp 轉回原始價格後輸出。

#### Scenario: OLS 預測點同時有兩種區間
- **WHEN** 任一 OLS 模型輸出預測點
- **THEN** 每個點都有數值型的 `ci_low`、`ci_high`、`pi_low`、`pi_high`，且 `pi_low ≤ ci_low ≤ pred ≤ ci_high ≤ pi_high`

#### Scenario: AR 只有預測區間
- **WHEN** AR 模型輸出預測點
- **THEN** 每個點的 `ci_low` 與 `ci_high` 為 `null`，`pi_low` 與 `pi_high` 為數值

#### Scenario: House 區間以價格顯示
- **WHEN** House 模型輸出預測點
- **THEN** `actual`、`pred` 與區間都是原始價格單位（正數，數量級為萬到百萬美元），且區間相對於預測值可以不對稱

### Requirement: 模型評估
對每個模型，管線 SHALL 輸出測試集的 R²、Adjusted R²、RMSE、MAE、95% 預測區間覆蓋率（測試集實際值落在預測區間內的比例，以完整測試集計算），以及 5-fold 交叉驗證的每折 R² 與平均、標準差。House 的 RMSE 與 MAE MUST 以原始價格單位計算。交叉驗證 SHALL 對 House 使用打亂且固定 seed 42 的 K-fold，對 Bike（含 AR）使用依時間順序的 5 折時間序列切分。管線 SHALL 輸出殘差診斷資料（預測值、殘差、Q-Q 理論分位數與樣本分位數），並在每個資料集中將測試集 R² 最高的模型標為唯一的最佳模型。

#### Scenario: 每個模型都有指標與交叉驗證
- **WHEN** 任一資料集管線完成
- **THEN** 每個模型的 `metrics` 都有 `r2`、`adj_r2`、`rmse`、`mae`、`pi_coverage`，`cv.scores_r2` 有 5 個值，且有 `mean` 與 `std`

#### Scenario: 唯一的最佳模型
- **WHEN** 任一資料集管線完成
- **THEN** `models` 中恰好一個模型 `is_best = true`，且它的測試集 R² 不低於其他模型

### Requirement: CRISP-DM 文字單一來源
CRISP-DM 六個步驟的說明文字 SHALL 來自每個資料集一份的內容檔，文字中的結果數值 MUST 以佔位符（例如 `{{metrics.test.r2}}`）表示並由管線代入實際值。內容檔中的佔位符若無法解析，管線 MUST 失敗，不可輸出未代入的佔位符。Business Understanding SHALL 包含業務問題、分析目標、成功標準與預測結果的使用方式；Evaluation 的結論 SHALL 說明是否達到成功標準。

#### Scenario: 佔位符全部被代入
- **WHEN** 管線輸出 JSON
- **THEN** `crisp_dm` 中所有 `markdown` 欄位都不含 `{{` 或 `}}`

#### Scenario: 無法解析的佔位符導致失敗
- **WHEN** 內容檔含有不存在的佔位符路徑
- **THEN** 管線以非零狀態結束並指出該佔位符

### Requirement: JSON 資料契約與圖檔輸出
管線 SHALL 為每個內建資料集輸出 `web/public/data/<dataset_id>.json`（`dataset_id` 為 `bike` 或 `house`），結構符合根目錄 `design.md` 第 6 節的契約（`meta`、`crisp_dm`、`data_understanding`、`feature_selection`、`models`）。House 的 `prediction.points` 與 `residuals` 在依預測值排序後 SHALL 均勻抽樣至最多 500 點，並在 `meta` 記錄是否抽樣與抽樣前後的點數。每個 JSON 檔 MUST 小於 2 MB。管線 SHALL 同時把報告與資訊圖表需要的圖輸出成 PNG 到 `reports/figures/`。

#### Scenario: 檔案大小與抽樣
- **WHEN** 管線完成兩個資料集
- **THEN** `bike.json` 與 `house.json` 都小於 2 MB，House 每個模型的 `prediction.points` 不超過 500 點且 `meta` 標示已抽樣

#### Scenario: 圖檔存在
- **WHEN** 管線完成
- **THEN** `reports/figures/` 中有兩個資料集的預測圖（含區間帶）、殘差圖與相關係數熱圖 PNG

### Requirement: 結果可重現
管線 SHALL 是決定性的：所有隨機操作使用固定 seed。對同一份輸入重複執行兩次，除了 `meta.generated_at` 以外，輸出 JSON 的所有內容 MUST 完全相同。任何步驟失敗時，管線 MUST 以非零狀態結束。

#### Scenario: 重跑兩次結果相同
- **WHEN** 在同一環境連續執行管線兩次
- **THEN** 兩次輸出的 JSON 在忽略 `meta.generated_at` 後逐位元組相同
