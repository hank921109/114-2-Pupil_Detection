# Pupil Detection

## 專案概述

- 輸出：帶註記的影像（將瞳孔中心與連線標出）、以及回傳的偵測結果（JSON-like 結構顯示臉框、瞳孔座標、距離）。
## 快速開始

1. 建議先建立 conda 環境（你可使用相同名稱 `Pupil_Detection`）：

```bash
conda activate Pupil_Detection
```


```bash
pip install -r Pupil_Detection/requirements.txt
```


```bash
python Pupil_Detection/pupil_detection.py --image Pupil_Detection/test_image/image1.png --output Pupil_Detection/results/image1_annotated_debug.jpg
```

## 檔案結構

- `Pupil_Detection/README.md` : 專案簡要說明。

簡短說明：在單張靜態影像內偵測人臉的瞳孔中心並計算左右瞳孔中心之間的像素距離。此 README 已整理為適合公開上傳的格式，包含快速開始、使用範例、技術清單、處理流程與注意事項。

- 臉部偵測：使用 OpenCV 的 Haar cascade (`haarcascade_frontalface_default.xml`) 偵測臉部 bounding box。
- 鎖定眼區：以 face bbox 比例估算左右眼 ROI（避免直接使用 Haar eye 偵測誤判）。
- 瞳孔定位：在每個眼部 ROI 進行 CLAHE 增強與中值濾波，接著以最暗值為基準做局部二值化與形態學處理，擷取可能的暗色輪廓，使用面積與圓形度選出最佳候選；若候選不足則以反相+Otsu 的質心作為備援。
- 距離計算：若一張臉找到兩瞳孔中心，計算兩者之歐式距離並在影像上標註（像素）。

### 技術清單

- **OpenCV (haarcascade, image ops)**: 臉部偵測、影像前處理、輪廓與繪製。
- **CLAHE (局部對比增強)**: 提升眼區局部對比，對於低對比影像特別有用。
- **Median blur**: 抑制椒鹽雜訊，保留邊緣資訊。
- **Thresholding (min-value / Otsu)**: 分割瞳孔（暗區）與背景；min-value 作為主要策略，Otsu 作為備援。
- **Morphological ops (open/close)**: 移除小雜訊與填補小孔洞，提高輪廓穩定性。
- **Contour analysis (area + circularity)**: 以面積與圓形度評分候選瞳孔輪廓。
- **Moments (質心)**: 當輪廓不足時，以質心作為瞳孔近似中心。
- **歐式距離**: 計算左右瞳孔中心的像素距離。

## 處理流程（流程圖與步驟）

```mermaid
flowchart TD
  A[讀入影像] --> B[臉部偵測 (Haar Cascade)]
  B --> C[估算左右眼 ROI (face bbox 比例)]
  C --> D[眼區前處理 (CLAHE -> MedianBlur)]
  D --> E[局部二值化 (以最暗值閾值)]
  E --> F[形態學處理 (開/閉運算)]
  F --> G[輪廓分析 (面積 + 圓形度)]
  G --> H{找到候選?}
  H -- 是 --> I[計算質心並回傳瞳孔中心]
  H -- 否 --> J[備援: 反相 + Otsu 質心]
  I --> K[若有兩眼則計算距離並標註]
  J --> K
```

步驟簡述：

1. 讀入影像並轉為灰階。
2. 使用 Haar cascade 偵測臉部 bounding box。
3. 根據臉框比例估算左右眼 ROI，限定搜尋區域以降低誤偵測。
4. 在每個眼區進行 CLAHE 與中值濾波增強與去噪。
5. 以最暗值為基準做局部二值化，接著用形態學處理清理雜訊。
6. 使用輪廓分析（面積與圓形度）挑選最可能的瞳孔區，並取質心為中心點；若無候選則以反相+Otsu 質心作為備援。
7. 若在同一臉上取得左右兩瞳孔中心，計算歐式距離並在影像上標註。

## 輸出範例與解釋

- 程式會回傳每個偵測到的臉的結果（`face_box`, `pupil_centers`, `distance_px`）。
- 標記說明：
  - 綠色圓：瞳孔外圍估計
  - 紅色點：瞳孔中心
  - 藍色線：兩瞳孔中心連線
  - 橙色矩形：未找到瞳孔時顯示的眼區

## 測試與評估

- 建議使用多樣化測試集（光照、眼鏡、角度）。
- 評估：檢出率、平均中心誤差、失敗案例統計。

## 限制與注意事項

- Haar face 在極側臉或遮擋下會降低準確性。
- 強烈反光或眼鏡會影響二值化與輪廓方法。
- 輸出的距離為像素，若需實際尺寸請做相機校正或使用已知尺度換算。

## 未來改進方向

- 改用 `mediapipe` 或 `dlib` 的 face landmark，提高眼區定位與遮擋容忍度。
- 加入反光偵測與移除的前處理。
- 提供簡單的 calibration 腳本，把像素距離換算為實際長度（mm）。

## 中間產物（Debug）

當你指定 `--output` 時，程式會在輸出資料夾下建立 `intermediates/<basename>/`，存放每張臉和每隻眼的中間影像：

- `<prefix>_roi_color.png` : 原始眼部彩圖 ROI
- `<prefix>_gray.png` : 眼部灰階圖
- `<prefix>_clahe_median.png` : CLAHE + median 後的影像
- `<prefix>_th.png` : 基於最暗值的二值化結果
- `<prefix>_inv.png` / `<prefix>_inv_th.png` : 反相與 Otsu 二值（fallback）

這些檔案有助於逐步檢視與參數調校。

## 在終端機中執行（使用 conda）

若你已建立且啟動 conda 環境 `Pupil_Detection`：

```bash
conda activate Pupil_Detection
pip install -r Pupil_Detection/requirements.txt
python Pupil_Detection/pupil_detection.py --image Pupil_Detection/test_image/image1.png --output Pupil_Detection/results/image1_annotated_debug.jpg
ls -l Pupil_Detection/results/intermediates/image1_annotated_debug
```

對整個資料夾批次處理：

```bash
mkdir -p Pupil_Detection/results
for f in Pupil_Detection/test_image/*; do
  out="Pupil_Detection/results/$(basename "${f%.*}")_annotated_debug.jpg"
  python Pupil_Detection/pupil_detection.py --image "$f" --output "$out"
done
```

如果你不想 activate 環境，可使用：

```bash
conda run -n Pupil_Detection python Pupil_Detection/pupil_detection.py --image Pupil_Detection/test_image/image1.png --output Pupil_Detection/results/image1_annotated_debug.jpg
```

## 參考與資源

- OpenCV Haar Cascades: https://docs.opencv.org/
- Hough Circle Transform: https://docs.opencv.org/4.x/da/d53/tutorial_py_houghcircles.html

---

如果你要，我可以把 `intermediates` 裡的影像打包成 zip 或把整個資料夾初始化為 Git repository 並進行第一次 commit。
# Pupil Detection 技術文件

> 本文件提供專案簡介、設計與演算法說明、使用教學、範例輸出與限制，方便放入 GitHub 作為技術文件（README 補充或 repo 的 TECHNICAL_DOCUMENTATION）。

## 目錄

- [專案概述](#專案概述)
- [快速開始](#快速開始)
- [檔案結構](#檔案結構)
- [演算法與設計](#演算法與設計)
- [處理流程（詳述）](#處理流程詳述)
- [輸出範例與解釋](#輸出範例與解釋)
- [測試與評估](#測試與評估)
- [限制與注意事項](#限制與注意事項)
- [未來改進方向](#未來改進方向)
- [參考與資源](#參考與資源)

## 專案概述

- 目標：在單張影像中偵測人臉內的瞳孔中心，並計算左右瞳孔中心之間的像素距離。
- 輸入：彩色影像檔（jpg/png）。
- 輸出：帶註記的影像（將瞳孔中心與連線標出）、以及回傳的偵測結果（JSON-like 結構顯示臉框、瞳孔座標、距離）。

## 快速開始

1. 建議先建立虛擬環境並安裝依賴：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r Pupil_Detection/requirements.txt
```

2. 範例執行：

```bash
python Pupil_Detection/pupil_detection.py --image path/to/input.jpg --output path/to/annotated.jpg
```

3. 執行後，`annotated.jpg` 會包含偵測到的臉框、瞳孔標記與兩眼距離（像素）。若沒有指定 `--output`，程式會以視窗顯示結果。

## 檔案結構

- `Pupil_Detection/pupil_detection.py` : 主程式，負責讀圖、偵測、標記與輸出。
- `Pupil_Detection/requirements.txt` : Python 依賴項。
- `Pupil_Detection/TECHNICAL_DOCUMENTATION.md` : 本技術文件。
- `Pupil_Detection/README.md` : 專案簡要說明與安裝步驟。

## 演算法與設計

- 臉／眼位置偵測：採用 OpenCV Haar cascade (`haarcascade_frontalface_default.xml`, `haarcascade_eye.xml`) 進行快速定位。此方法計算量小，適合即時或資源受限的情境。
- 瞳孔中心定位：
  - 前處理：眼睛 ROI 進行直方圖均衡化（`equalizeHist`）與 `GaussianBlur`，提高對比並抑制雜訊。
  - 主要方法：使用 `HoughCircles` 偵測圓形（參數可調），對於規則且對比良好的瞳孔能取得良好結果。
  - 備援方法：若 HoughCircles 失敗，採用 Otsu 閾值二值化（反向）擷取暗部區域，找出最大輪廓並以 `minEnclosingCircle` 計算近似中心與半徑。
- 距離計算：以兩瞳孔中心之歐式距離（像素）輸出；若需換算成實際長度，須進行相機校正或使用已知尺度做換算。

## 處理流程詳述

1. 讀入影像並轉為灰階。
2. 在整張影像上使用 face cascade 偵測臉部 bounding box。
3. 對每個臉部 ROI 使用 eye cascade 偵測眼睛區域。
4. 對每個眼睛 ROI：
   - 進行直方圖均衡與 Gaussian 模糊。
   - 執行 HoughCircles；若成功，取得圓心與半徑；反之，使用 Otsu 二值化 + 找最大輪廓 + minEnclosingCircle。
   - 將 ROI 內的座標轉回原影像座標並在原圖上畫標記。
5. 若同一張臉在左右眼找到兩個瞳孔中心，計算歐式距離並將結果以文字標註於影像中點。

## 輸出範例與解釋

- 程式會在終端列印偵測結果陣列（每個臉的 `face_box`, `pupil_centers`, `distance_px`）。
- 標記顏色說明（預設）：
  - 綠色圓：估計到的瞳孔半徑與外框
  - 紅色點：瞳孔中心
  - 藍色線：兩瞳孔中心連線（若找到兩顆瞳孔）
  - 橙色框：眼睛 ROI（當無法定位瞳孔時顯示）

範例終端輸出（示意）：

```text
Results:
{'face_box': (120, 80, 220, 220), 'pupil_centers': [(160, 150), (240, 152)], 'distance_px': 80.25}
```

在 GitHub 的 README 或技術文件中可加入 sample 資料夾與結果影像，方便 reviewer 或使用者快速檢視成果。

## 測試與評估

- 建議測試集：包含不同光照、戴眼鏡/不戴眼鏡、不同視角（±30°）、不同年齡與人種的樣本。
- 評估指標：
  - 檢出率（瞳孔中心是否被正確偵測）
  - 平均中心誤差（若有標註真實中心）
  - 偵測失敗情境統計（遮擋、反光、極端側臉）

## 限制與注意事項

- Haar cascade 對大角度側臉或遮擋（例如頭髮、手）表現差。
- 眼鏡反光、強烈側光或太暗環境會造成 HoughCircles / 二值化失效。
- 本程式輸出為像素距離，若要取得實際毫米或公分需進行相機內參/外參校正或使用已知尺度。

## 未來改進方向

- 使用深度學習的人臉關鍵點 (facial landmark) 模型（如 dlib、mediapipe、或基於 CNN 的 landmark 檢測）提高對於側臉與遮擋的健壯性。
- 加入亮度/反光偵測與專門的反光移除預處理。
- 加入相機校正流程與標定工具，使像素距離能換算為實際長度。
- 加入單元測試與評估腳本，並提供範例資料與標註檔。

## 參考與資源

- OpenCV Haar Cascades: https://docs.opencv.org/
- Hough Circle Transform: https://docs.opencv.org/4.x/da/d53/tutorial_py_houghcircles.html

---
