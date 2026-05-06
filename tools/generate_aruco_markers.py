#!/usr/bin/env python3
"""ArUco 마커 생성 스크립트

DICT_4X4_50, ID 0~3, 30mm 크기의 마커를 생성.
A4 용지에 인쇄할 수 있도록 한 장에 4개 배치.

Usage:
  python3 tools/generate_aruco_markers.py
  # → aruco_markers.png 생성 (A4 크기, 4개 마커)
"""

import cv2
import numpy as np


def generate_markers():
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

    marker_size_px = 400  # 400px (인쇄 시 30mm가 되도록 DPI 조정)
    margin = 80
    label_h = 60

    # 개별 마커 저장
    for i in range(4):
        img = cv2.aruco.drawMarker(aruco_dict, i, marker_size_px)
        cv2.imwrite(f"aruco_{i}.png", img)
        print(f"Saved aruco_{i}.png ({marker_size_px}x{marker_size_px})")

    # A4 시트 (2x2 배치)
    cell_w = marker_size_px + margin * 2
    cell_h = marker_size_px + margin * 2 + label_h
    sheet_w = cell_w * 2
    sheet_h = cell_h * 2
    sheet = np.ones((sheet_h, sheet_w), dtype=np.uint8) * 255

    for i in range(4):
        row, col = divmod(i, 2)
        img = cv2.aruco.drawMarker(aruco_dict, i, marker_size_px)

        y0 = row * cell_h + margin
        x0 = col * cell_w + margin
        sheet[y0:y0 + marker_size_px, x0:x0 + marker_size_px] = img

        # Label
        label = f"ID: {i}  (DICT_4X4_50, 30mm)"
        cv2.putText(
            sheet, label,
            (x0, y0 + marker_size_px + 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, 0, 2,
        )

    cv2.imwrite("aruco_markers_sheet.png", sheet)
    print(f"\nSaved aruco_markers_sheet.png ({sheet_w}x{sheet_h})")
    print("인쇄 시 마커 크기가 정확히 30mm가 되도록 스케일 조정하세요.")
    print("DPI 340 기준으로 400px ≈ 30mm")


if __name__ == "__main__":
    generate_markers()
