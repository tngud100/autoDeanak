# utils.py

import random
import cv2
import numpy as np
import tkinter as tk
from tkinter import messagebox

# import sys
# import time

def preprocess_image(image):
    """이미지를 전처리하여 대비를 조정하고 노이즈를 제거합니다."""
    # 히스토그램 평활화로 대비 조정
    image = cv2.equalizeHist(image)
    # 가우시안 블러로 노이즈 제거
    image = cv2.GaussianBlur(image, (5, 5), 0)
    # 데이터 타입을 uint8로 변환
    image = image.astype(np.uint8)
    return image

def get_random_point(top_left, bottom_right):
    """탐지된 템플릿의 랜덤 좌표를 반환합니다."""
    center_x = random.randint(top_left[0], bottom_right[0])
    center_y = random.randint(top_left[1], bottom_right[1])
    return center_x, center_y

def show_notification(title, message):
    root = tk.Tk()
    root.withdraw()  # 메인 윈도우 숨기기
    messagebox.showinfo(title, message)
    root.destroy()

class CountdownApp:
    def __init__(self, master, duration):
        self.master = master
        self.duration = duration
        self.remaining = duration
        
        # Label to show the countdown
        self.label = tk.Label(master, text=self.format_time(self.remaining), font=('Helvetica', 48))
        self.label.pack(pady=20)  # Add some padding to the label
        
        # Start countdown
        self.start_countdown()

    def start_countdown(self):
        if self.remaining > 0:
            self.label.config(text=self.format_time(self.remaining))
            self.remaining -= 1
            # Call this method again after 1 second
            self.master.after(1000, self.start_countdown)
        else:
            # Countdown finished, notify the user and close the window
            self.master.after(500, self.master.destroy)  # 0.1초 후에 창 닫기

    def format_time(self, seconds):
        """Helper function to format time in MM:SS format."""
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02}:{seconds:02}"
