# capture.py

import pyautogui
import cv2
import numpy as np

def screen_capture(use_color=False):
    """화면을 캡처하여 컬러 또는 흑백 이미지로 반환합니다."""
    screenshot = pyautogui.screenshot()
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) # OpenCV 형식으로 변환
    
    if not use_color:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 흑백으로 변환
        
    return frame
