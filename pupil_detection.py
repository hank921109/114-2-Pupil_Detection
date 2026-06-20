import argparse
import os
import math
import cv2
import numpy as np

def detect_pupils(image_path, out_path=None, debug=False):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 載入人臉與眼睛的 Cascade 模型
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))

    results = []

    for (x, y, w, h) in faces:
        # 只取臉部上半段 (60%) 尋找眼睛，避免將鼻孔或嘴巴誤判為眼睛
        roi_gray_face = gray[y:int(y + h * 0.6), x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray_face, scaleFactor=1.1, minNeighbors=5, minSize=(int(w*0.15), int(h*0.15)))

        pupil_centers = []

        # 確保是由左到右排序，並且最多只取兩個眼睛特徵
        eyes = sorted(eyes, key=lambda e: e[0])[:2]

        for (ex, ey, ew, eh) in eyes:
            # 關鍵優化：稍微往內裁切眼睛 ROI，避開上方眉毛與下方眼袋的暗部陰影
            crop_top = int(eh * 0.2)
            crop_bottom = int(eh * 0.1)
            crop_side = int(ew * 0.15)

            eye_roi = roi_gray_face[ey + crop_top : ey + eh - crop_bottom, 
                                    ex + crop_side : ex + ew - crop_side]
            
            if eye_roi.size == 0: 
                continue

            # 使用高斯模糊去除微小雜訊
            blurred = cv2.GaussianBlur(eye_roi, (7, 7), 0)

            # 尋找瞳孔：找出影像中最暗的像素值 (min_val)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(blurred)
            
            # 設定閾值：只保留接近最暗點的像素 (容許值 +15)
            threshold_value = min_val + 15 
            _, thresh = cv2.threshold(blurred, threshold_value, 255, cv2.THRESH_BINARY_INV)

            # 形態學處理：去除細小雜訊並連接破洞
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

            # 尋找輪廓
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            center = None
            radius = 0

            if contours:
                valid_contours = []
                for c in contours:
                    area = cv2.contourArea(c)
                    if area > 10: # 濾除極小雜訊
                        # 計算圓形度 (Circularity)
                        perimeter = cv2.arcLength(c, True)
                        if perimeter > 0:
                            circularity = 4 * math.pi * (area / (perimeter * perimeter))
                            valid_contours.append((c, area, circularity))

                if valid_contours:
                    # 選擇「面積與圓形度」乘積最大的輪廓作為瞳孔
                    best_contour = max(valid_contours, key=lambda item: item[1] * item[2])[0]

                    # 使用影像矩 (Moments) 計算質心
                    M = cv2.moments(best_contour)
                    if M['m00'] != 0:
                        cx = int(M['m10'] / M['m00'])
                        cy = int(M['m01'] / M['m00'])

                        # 換算回整張大圖的絕對座標
                        abs_x = x + ex + crop_side + cx
                        abs_y = y + ey + crop_top + cy
                        center = (abs_x, abs_y)

                        # 估算繪圖用的半徑
                        _, radius_float = cv2.minEnclosingCircle(best_contour)
                        radius = int(radius_float)

            if center is not None:
                pupil_centers.append(center)
                # 畫出瞳孔範圍 (綠圈) 與中心點 (紅點)
                cv2.circle(img, center, max(radius, 4), (0, 255, 0), 2)
                cv2.circle(img, center, 2, (0, 0, 255), -1)
            else:
                # 找不到瞳孔時，畫出橘色框以供 Debug
                cv2.rectangle(img, (x+ex, y+ey), (x+ex+ew, y+ey+eh), (0, 165, 255), 1)

        # 計算雙眼距離
        distance = None
        if len(pupil_centers) == 2:
            (x1, y1), (x2, y2) = pupil_centers
            # 計算歐式距離
            distance = math.hypot(x2 - x1, y2 - y1)
            
            # 畫出連線與標示距離
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
            mid = (int((x1 + x2) / 2), int((y1 + y2) / 2))
            cv2.putText(img, f"d={distance:.1f}px", (mid[0]-30, mid[1]-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        results.append({
            'face_box': (int(x), int(y), int(w), int(h)),
            'pupil_centers': pupil_centers,
            'distance_px': distance,
        })

    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        cv2.imwrite(out_path, img)

    return results, img

def main():
    parser = argparse.ArgumentParser(description='瞳孔偵測')
    parser.add_argument('--image', '-i', required=True, help='Input image path')
    parser.add_argument('--output', '-o', required=False, help='Output annotated image path')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    results, img = detect_pupils(args.image, args.output, debug=args.debug)

    for r in results:
        print(f"Face ROI: {r['face_box']}, Distance: {r['distance_px']}")

    if not args.output:
        cv2.imshow('Pupil Detection', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()