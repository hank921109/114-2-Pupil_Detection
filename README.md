# Pupil Detection 瞳孔辨識

## 專案概述

- 輸出：帶註記的影像（將瞳孔中心與連線標出）、以及回傳的偵測結果（JSON-like 結構顯示臉框、瞳孔座標、距離）。

## 快速開始

\*\*\* Begin Clean README

# Pupil Detection

在單張靜態影像中偵測人臉的瞳孔中心，並計算左右瞳孔中心之間的像素距離。

此 README 已清理重複內容，包含快速開始、檔案說明、技術清單、處理流程、使用範例、限制與成果連結。

---

## 快速開始

在專案根目錄下：

```bash
conda create -n Pupil_Detection python=3.10 -y
conda activate Pupil_Detection
pip install -r requirements.txt
```

測試單張圖片：

```bash
mkdir -p results
python pupil_detection.py --image test_image/image1.png --output results/image1_annotated.jpg
```

批次處理 `test_image`：

```bash
mkdir -p results
for f in test_image/*; do
  python pupil_detection.py --image "$f" --output "results/$(basename "${f%.*}")_annotated.jpg"
done
```

---

## 檔案說明

- `pupil_detection.py` : 主程式，負責偵測、人臉與瞳孔標記、輸出註記影像。
- `requirements.txt` : Python 相依。
- `test_image/` : 範例輸入影像。
- `results/` : 偵測輸出（註記影像）。
- `TECHNICAL_DOCUMENTATION.md` : 詳細技術說明（包含流程圖與參數）。

---

## 技術清單（概要）

- OpenCV（Haar cascade、影像處理、輪廓、繪製）
- CLAHE（局部對比增強）
- 中值濾波（去噪）
- 閾值分割（min-value / Otsu）
- 形態學操作（開/閉）
- 輪廓分析（面積、圓形度）
- 質心 (moments) 作為備援中心

---

## 處理流程（概覽）

1. 讀入影像 → 轉灰階
2. 人臉偵測（Haar cascade）
3. 根據臉框估算左右眼 ROI
4. 眼區前處理：CLAHE → 中值濾波
5. 局部二值化（以暗值為基準）→ 形態學處理
6. 輪廓分析（面積 + 圓形度）選出瞳孔候選，取質心或 minEnclosingCircle
7. 若獲得左右兩瞳孔中心，計算歐式距離並標註

詳細參數與說明見 `TECHNICAL_DOCUMENTATION.md`。

---

## 使用說明與輸出標示

- 執行後終端會輸出每張臉的 `face_box`, `pupil_centers`, `distance_px`。
- 註記圖示說明：綠圓=瞳孔外框，紅點=瞳孔中心，藍線=兩眼連線，橙框=未找到瞳孔的眼區。

---

## 成果 (Results)

註：下列連結與圖片指向已推至你的 GitHub repository。

- image1_annotated.jpg

  ![image1](https://raw.githubusercontent.com/hank921109/114-2-Pupil_Detection/main/results/image1_annotated.jpg)

  https://github.com/hank921109/114-2-Pupil_Detection/blob/main/results/image1_annotated.jpg

- image2_annotated.jpg

  ![image2](https://raw.githubusercontent.com/hank921109/114-2-Pupil_Detection/main/results/image2_annotated.jpg)

  https://github.com/hank921109/114-2-Pupil_Detection/blob/main/results/image2_annotated.jpg

---

## 限制與注意事項

- Haar cascade 在側臉、遮擋或強反光（例如鏡片）情況下表現有限。
- 輸出為像素距離；若需實際長度，請做相機校正或使用已知尺度換算。

---

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
