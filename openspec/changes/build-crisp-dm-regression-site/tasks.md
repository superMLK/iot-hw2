# Tasks

## 1. 專案骨架與資料

- [x] 1.1 建立目錄結構（`analysis/data/raw`、`analysis/content`、`analysis/pipeline`、`analysis/tests`、`web`、`reports/figures`、`reports/infographic`、`reports/output`、`.github/workflows`）與 `.gitignore`（含 `web/public/data/`、`node_modules`、`__pycache__`、`.venv`）；以 `find . -type d` 確認目錄都在
- [x] 1.2 建立 `requirements.txt`（pandas、numpy、statsmodels、scikit-learn、matplotlib、PyYAML、python-docx、playwright、qrcode、pytest，全部固定版本），在 Python 3.11 虛擬環境中 `pip install -r requirements.txt` 成功
- [x] 1.3 取得 `day.csv`（UCI 或 Kaggle）放入 `analysis/data/raw/`；以 pandas 讀取確認為 731 列、16 欄且欄名與原設計 3.1 一致
- [x] 1.4 取得 `kc_house_data.csv` 放入 `analysis/data/raw/`（Kaggle API 不可用時請使用者手動下載）；確認約 21,613 列、21 欄且欄名與原設計 3.2 一致
- [x] 1.5 開啟兩個 Kaggle 頁面查閱授權，建立 `analysis/datasets.yaml`（id、名稱、kaggle_url、origin_url、license、file、target、id 欄、切分方式）；確認兩筆的 `license` 都是查閱到的實際條款

## 2. 分析管線：共用框架與 Bike

- [x] 2.1 實作 `run_pipeline.py` 與設定載入：讀 `datasets.yaml`、驗證必要欄位（缺 `kaggle_url` 或 `license` 時以非零狀態結束）；以 pytest 驗證缺欄位會失敗
- [x] 2.2 實作資料理解模組（筆數、欄數、特徵數與 13–40 檢核、型別、缺失、唯一值、重複列、敘述統計、相關矩陣、目標分布、前 5 相關特徵、前 10 筆預覽）；pytest 驗證 Bike 的 `n_features = 14`，且特徵數超出範圍時會失敗
- [x] 2.3 實作 `prepare_bike`（移除 casual/registered/instant/workingday、dteday 只用於排序、四個類別 one-hot 丟基準、依時間 80/20 切分）並輸出步驟紀錄與前後筆數欄數；pytest 驗證洩漏欄位不在特徵中、有資料洩漏步驟紀錄、測試集最早日期晚於訓練集最晚日期
- [x] 2.4 實作特徵選擇模組（相關係數篩選含 |r|>0.8 配對與保留規則、VIF 迭代含無限大處理、從空模型開始的雙向 AIC 逐步回歸、比較表、final_features）；pytest 驗證 temp/atemp 不同時留在 VIF 結果中、`final_features` 等於 `stepwise_kept`，以及改動測試集目標值後結果不變
- [x] 2.5 實作 OLS 建模（SLR 自動選訓練集 |r| 最高特徵、MLR 全部特徵、MLR 選擇後特徵）與係數表輸出；pytest 驗證三個模型存在且係數表欄位完整
- [x] 2.6 實作 Bike AR（`ar_select_order` maxlag 14、AIC、訓練期擬合、測試期一步預測、± 1.96 × 殘差標準差預測區間、`ar_order`）；pytest 驗證 1 ≤ p ≤ 14 且 `ci_low`/`ci_high` 為 null
- [x] 2.7 實作評估模組（R²、Adj R²、RMSE、MAE、PI 覆蓋率、TimeSeriesSplit 5 折 CV 含 AR、殘差與 Q-Q 資料、唯一最佳模型）；pytest 驗證每個模型的 metrics 欄位齊全、`cv.scores_r2` 有 5 個值、恰好一個 `is_best`
- [x] 2.8 實作 JSON 輸出（契約欄位與 design 決策 9 的延伸欄位、6 位有效數字、`sort_keys`）與 PNG 輸出（預測圖含區間帶、殘差圖、相關熱圖，Agg 後端、無時間戳記）；執行 `python analysis/run_pipeline.py` 產生 `web/public/data/bike.json` 與 `reports/figures/bike_*.png`，確認 JSON < 2 MB 且 OLS 預測點符合 `pi_low ≤ ci_low ≤ pred ≤ ci_high ≤ pi_high`

## 3. 分析管線：House

- [x] 3.1 實作 `prepare_house`（移除 id/sqft_above/yr_built/zipcode、date → sale_year 與 sale_month one-hot、is_renovated、house_age、has_basement、異常值規則並記錄筆數、log(price)、random_state=42 隨機 80/20）；pytest 驗證特徵清單、無 `bedrooms = 33`、每條異常值規則都有筆數，且 `n_features = 19`
- [x] 3.2 讓建模與評估支援 log 目標：區間在 log 尺度計算後 exp 還原、RMSE/MAE 用價格、R² 用 log 尺度並寫入 `metrics_note`、KFold(5, shuffle, 42)；pytest 驗證 House 預測值與區間為正的價格且 SLR 特徵為 `sqft_living`、沒有 AR 模型
- [x] 3.3 實作 House 預測點與殘差的抽樣（依預測值排序、等距取最多 500 點、`meta.sampled` 與點數），覆蓋率用完整測試集；執行管線確認 `house.json` < 2 MB 且每個模型 `prediction.points` ≤ 500
- [x] 3.4 加入重現性測試：連續跑兩次管線，忽略 `meta.generated_at` 後兩次 JSON 逐位元組相同；pytest 通過

## 4. CRISP-DM 內容

- [x] 4.1 實作佔位符代入（`{{path}}`、`{{path|fmt}}`、別名如 `best.metrics.r2`，解析失敗即丟錯）；pytest 驗證正常代入、格式化與不存在路徑會讓管線失敗
- [x] 4.2 撰寫 `analysis/content/bike.zh-TW.yaml` 六個步驟（業務問題、目標、成功標準 R² ≥ 0.70、資料洩漏說明、時間切分、AR 只有預測區間、達標判斷結論、部署與限制），所有結果數值都用佔位符；跑管線後確認 `bike.json` 的 `crisp_dm` 中沒有 `{{`
- [x] 4.3 撰寫 `analysis/content/house.zh-TW.yaml` 六個步驟（含 zipcode 取捨、異常值說明、log 轉換與區間不對稱說明、R² 尺度說明、成功標準 R² ≥ 0.80），全部結果數值用佔位符；跑管線後確認 `house.json` 的 `crisp_dm` 中沒有 `{{`，並人工檢查兩份文字以台灣用語撰寫且沒有手打數字

## 5. 前端：內建資料集

- [x] 5.1 以 Vite 建立 React 18 + TypeScript 專案於 `web/`，安裝 plotly.js-cartesian-dist-min、react-plotly.js、papaparse、vitest（`package-lock.json` 固定版本），`vite.config.ts` 依 `GITHUB_REPOSITORY` 設定 `base`；`npm run build` 與 `npm run test` 都成功
- [x] 5.2 定義 `web/src/types/dataset.ts` 對應 JSON 契約，實作資料載入 hook（`BASE_URL` 路徑、載入中與中文錯誤狀態）；以 `bike.json` 執行 `tsc --noEmit` 無型別錯誤
- [x] 5.3 實作 hash 狀態（`#<dataset>-<step>`、`#custom`、無效 hash 回到 Bike 業務理解、切換資料集保留步驟）為純函式並寫 Vitest 測試；測試涵蓋解析、序列化、無效值與保留步驟
- [x] 5.4 實作版面：標題、三選項下拉選單、資料集資訊卡（名稱、Kaggle 與原始連結、授權、筆數、特徵數、目標）、六步驟條、內容區；CSS 變數深淺色、16px 邊距；`npm run dev` 中確認預設顯示 Bike 且切換到房價時資訊卡更新
- [x] 5.5 實作共用 Plotly 元件（lazy load、依深淺色取色、響應式寬度、容器內捲動）與表格元件（容器內橫向捲動）
- [x] 5.6 實作業務理解、資料理解（欄位表、敘述統計、熱圖、目標分布、預覽、特徵數）、資料準備（步驟表、前後筆數欄數、Bike 資料洩漏醒目提示）三個步驟頁；在瀏覽器確認兩個資料集的特徵數分別顯示 14 與 19，Bike 資料準備頁看得到洩漏說明
- [x] 5.7 實作建模頁（相關係數表與高相關配對、VIF 各輪、逐步回歸各步、三方法比較表、最終特徵、模型清單、係數表 p < 0.05 標示）；在瀏覽器確認兩個資料集都看得到三種方法的過程與比較表
- [x] 5.8 實作預測圖元件（模型切換；SLR 用 `band` 畫回歸線與兩種區間帶；MLR 依預測值排序圖加實際對預測散佈圖與 y = x；AR 日期軸、訓練期與測試期、只有預測區間並加註；信賴區間透明度 0.35、預測區間 0.15；圖例文字；圖下說明；House 不對稱說明）；在瀏覽器逐一切換所有模型確認區間帶與圖例正確
- [x] 5.9 實作評估頁（模型比較表標示最佳、預測圖、殘差對預測值、Q-Q、殘差直方圖、CV 每折與平均 ± 標準差、PI 覆蓋率、結論）與部署頁；在瀏覽器確認每個模型都有測試集指標與 CV 結果
- [x] 5.10 RWD 與深色模式檢查：以 375px 寬瀏覽每個步驟頁確認沒有整頁橫向捲動，切換系統深色模式確認文字與圖表可讀；以 `#house-modeling` 直接開啟確認顯示正確

## 6. 前端：自訂 CSV

- [x] 6.1 在 `web/src/lib/stats/` 實作 `inferType`、`countMissing`、`describe`（含 quantile）、`correlationMatrix`、`histogram`、`topCategories` 純函式，並寫 Vitest 測試涵蓋空值、全缺失、單一值、混合型別、日期判斷、前 10 名截斷；`npm run test` 通過
- [x] 6.2 實作載入流程（URL 驗證、fetch、HTML 偵測、PapaParse 設定、50,000 筆截斷與提示、上傳檔案共用流程）與錯誤分類（格式錯誤、網路／CORS、非 CSV、空檔案，皆為中文訊息與建議），錯誤分類寫成純函式並以 Vitest 測試
- [x] 6.3 實作自訂模式畫面（輸入框預填範例網址、上傳按鈕、筆數欄數、欄位型別與缺失、敘述統計、熱圖前 50 個數值欄與提示、各欄分布、預覽），且不顯示步驟條與建模區塊；在瀏覽器以範例網址確認顯示 50 筆 5 欄，上傳同一份檔案結果相同
- [x] 6.4 錯誤情境檢查：在瀏覽器輸入 `abc`、一個會被 CORS 擋下的網址、回傳 HTML 的網址，並上傳空檔案，確認都顯示中文訊息且頁面可繼續操作

## 7. 部署

- [x] 7.1 撰寫 `.github/workflows/deploy.yml`（push main 與 workflow_dispatch、pages/id-token 權限、Python 3.11 安裝與管線、Node 20 `npm ci`/`npm run test`/`npm run build`、upload-pages-artifact 與 deploy-pages）；本機依同樣順序執行全部指令都成功
- [x] 7.2 【需使用者確認】`git init`、建立 GitHub repo（名稱與可見性由使用者決定）、設定 Pages Source 為 GitHub Actions、推送 `main`；確認 Actions 全部步驟成功
- [x] 7.3 開啟 Pages 網址與 `#house-evaluation` 子路徑網址，確認資源與 JSON 都正常載入，並在手機寬度與深色模式下快速檢查一次

## 8. README

- [x] 8.1 撰寫 `README.md`（簡介與網站連結、資料集來源與授權、架構圖、本機執行、部署方式、CRISP-DM 六步驟摘要、主要結果表、目錄結構）；結果表以小腳本從 JSON 產生後貼入，並在乾淨 clone 中照 README 指令執行成功

## 9. Word 報告

- [x] 9.1 實作 `reports/build_report.py`：讀內容檔、JSON、PNG，產生封面、摘要、資料集介紹、CRISP-DM 六章（兩資料集各一小節）、結論與限制、參考資料；中文字型設定 `w:eastAsia`、標題用內建樣式、圖表自動編號；執行後確認 `reports/output/report.docx` 存在
- [x] 9.2 檢查報告：用 python-docx 讀回確認 11 個章節順序、第 4–9 章各有兩個小節、「圖 N」「表 N」從 1 連續編號；在 Word 中插入目錄確認標題被列入，並比對最佳模型 R²、RMSE 與網站相同

## 10. A4 資訊圖表

- [x] 10.1 建立 `reports/infographic/template.html`（A4 直式、標題、六步驟流程條、兩資料集卡片、最佳模型 R² 與 RMSE 大字、簡化預測圖含區間帶、特徵選擇「N → M」、網址與 QR code、內文 ≥ 11 pt）
- [x] 10.2 實作 `build_infographic.py`：從 JSON 代入數值、產生 QR code、以 Playwright 匯出 PDF 與 PNG；確認 PDF 為單頁 A4、PNG 為 2480 × 3508，用手機掃 QR code 開啟網站

## 11. 整體驗收

- [x] 11.1 依原設計第 10 節 14 條驗收條件逐條檢查並記錄結果（網站部分用瀏覽器實測、管線重現性用 3.4 的測試、三份繳交物數值逐一比對），全部通過才算完成
