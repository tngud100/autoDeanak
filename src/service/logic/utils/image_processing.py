# image_processing.py

import os
from typing import Counter
import cv2
import numpy as np
# import os
import time
import cv2
import numpy as np
import pytesseract
import pyautogui
import easyocr

from src.service.logic.utils.utils import preprocess_image, get_random_point
from src.service.logic.utils.keyboard_mouse import move_cursor, move_and_click
from src.service.logic.utils.error import handle_error

# 템플릿 이미지 로드 함수
def load_templates(password_list: list = None):
    try:
        template_paths = {
            "password_screen": 'static/image/2ndPassword.PNG',
            "password_confirm": 'static/image/loginConfirm.PNG',
            "wrong_password": 'static/image/wrongPassword.PNG',
            "notice_screen": 'static/image/notice.PNG',
            "team_select_screen": 'static/image/selectTeam.PNG',
            "team_select_text": 'static/image/selectTeamText.PNG',
            "purchase_before_main_screen": 'static/image/beforeMainPurchases.PNG',
            "purchase_cancel_btn": 'static/image/purchaseCloseBtn.PNG',
            "main_screen": 'static/image/mainScreen.PNG',
            "market_screen": 'static/image/marketScreen.PNG',
            "get_item_screen": 'static/image/getItemScreen.PNG',
            "get_all_screen": 'static/image/getAllScreen.PNG',
            "top_class": 'static/image/topClass.PNG',
            "no_top_class": 'static/image/noTopClass.PNG',
            "market_btn": 'static/image/market.PNG',
            "list_btn": 'static/image/sellList.PNG',
            "get_item_btn": 'static/image/getItemConfirm.PNG',
            "arrange_btn_screen": 'static/image/PriceArrangeScreen.PNG',
            "arrange_btn": 'static/image/priceArrangeBtn.PNG',
            "price_desc": 'static/image/priceDesc.PNG',
            "get_all_btn": 'static/image/getAll.PNG',
            "password_templates": [f'static/image/{i}.PNG' for i in password_list]
        }

        templates = {
            key: check_and_load_template(path)
                if not isinstance(path, list) 
                else [check_and_load_template(p) for p in path]
                for key, path in template_paths.items()
            }

        # 템플릿 로드 여부 확인
        for key, template in templates.items():
            if isinstance(template, list):
                if any(t is None for t in template):
                    raise FileNotFoundError(f"템플릿 리스트 중 로드 되지 못 한 템플릿이 있습니다.")
            elif template is None:
                raise FileNotFoundError(f"템플릿 {key}이 로드 되지 못했습니다.")

        return templates
    
    except FileNotFoundError as e:
        handle_error(e, "템플릿 로드 중 오류 발생", critical=True)
    except Exception as e:
        handle_error(e, "예상치 못 한 오류 발생", critical=True)


def check_and_load_template(path, use_color=False):
    """템플릿 이미지를 로드합니다. 컬러 매칭을 위해 옵션 추가."""
    if use_color:
        template = cv2.imread(path, cv2.IMREAD_COLOR)  # 컬러 이미지로 로드
    else:
        template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)  # 기존 방식 (흑백)

    if template is None:
        raise FileNotFoundError(f"찾지 못 한 템플릿 이미지: {path}")
    
    return template

def check_and_load_text_template(path):
    template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)  # 기존 방식 (흑백)
    
    if template is None:
        raise FileNotFoundError(f"찾지 못 한 템플릿 이미지: {path}")
    
    return template




# 화면 탐지 및 작업 처리 함수
def handle_detection(screen, template, action, *args, threshold=0.8, roi=None):
    try:
        top_left, bottom_right, _ = detect_template(screen, template, threshold, roi=roi)
        if top_left and bottom_right:
            action(*args)
            return True
        return False
    except Exception as e:
        handle_error(e, "예상치 못한 오류 발생", critical=True)
        return False

    
def detect_template(screen, templates, threshold=0.8, roi=None):
    """화면에서 템플릿을 탐지하고, 템플릿의 좌표와 일치도를 반환합니다."""
    if roi is not None:
        # ROI가 설정된 경우, 해당 영역만 탐지 대상으로 자름
        screen = screen[roi[1]:roi[3], roi[0]:roi[2]]

    template_height, template_width = templates.shape[:2]
    found = None

    # templates가 단일 이미지인 경우 리스트로 변환
    if not isinstance(templates, list):
        templates = [templates]

    # 템플릿 리스트를 순차적으로 탐지 시도
    for template in templates:
        template_height, template_width = template.shape[:2]
        found = None

        # 다중 스케일 템플릿 매칭을 위한 루프
        for scale in np.linspace(0.8, 1.0, 10)[::-1]:  # 스케일 범위와 단계 수 조정
            resized_template_width = int(template_width * scale)
            resized_template_height = int(template_height * scale)

            resized = cv2.resize(template, (resized_template_width, resized_template_height))

            r = template_width / float(resized.shape[1])  # 비율 계산

            # 템플릿 크기가 화면을 초과하면 무시
            if resized.shape[0] > screen.shape[0] or resized.shape[1] > screen.shape[1]:
                continue

            result = cv2.matchTemplate(screen, resized, cv2.TM_CCOEFF_NORMED)

            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val >= threshold:
                if found is None or max_val > found[0]:
                    found = (max_val, max_loc, r, resized.shape[1], resized.shape[0])

        # 템플릿 위치 반환 (탐지에 성공한 경우)
        if found:
            max_val, max_loc, r, resized_width, resized_height = found
            start_x = int(max_loc[0] * r)
            start_y = int(max_loc[1] * r)
            end_x = start_x + int(resized_width * r)
            end_y = start_y + int(resized_height * r)

            # ROI가 설정된 경우, 전체 화면의 좌표로 변환
            if roi is not None:
                start_x += roi[0]
                start_y += roi[1]
                end_x += roi[0]
                end_y += roi[1]

            return (start_x, start_y), (end_x, end_y), max_val

    # 모든 템플릿을 탐지했으나 성공하지 못한 경우
    return None, None, None

def detect_and_click_template(screen, template, threshold, ratio_width, ratio_height, roi=None, click=True, mouse_offset=(0, 0), shrink_factor=0.9):
    """주어진 템플릿을 탐지하고 클릭 여부를 선택하며 탐지된 이미지를 저장합니다."""
    if roi is not None:  # ROI(탐지할 영역)가 설정된 경우 해당 영역만 탐지
        screen = screen[roi[1]:roi[3], roi[0]:roi[2]]  # ROI 영역으로 화면 자르기

    top_left, bottom_right, max_val = detect_template(screen, template, threshold)
    print(f"second detecting image: {top_left}, {bottom_right}")
    if top_left and bottom_right:
        # 탐지된 영역을 사각형으로 표시
        # screen_color = cv2.cvtColor(screen, cv2.COLOR_GRAY2BGR)
        # cv2.rectangle(screen_color, top_left, bottom_right, (0, 255, 0), 2)

        # 탐지된 영역을 전체 화면 좌표로 변환
        if roi is not None:
            top_left = (top_left[0] + roi[0], top_left[1] + roi[1])
            bottom_right = (bottom_right[0] + roi[0], bottom_right[1] + roi[1])

        width = bottom_right[0] - top_left[0]
        height = bottom_right[1] - top_left[1]

        shrink_width = int(width * shrink_factor / 2)
        shrink_height = int(height * shrink_factor / 2)
        adjusted_top_left = (top_left[0] + shrink_width, top_left[1] + shrink_height)
        adjusted_bottom_right = (bottom_right[0] - shrink_width, bottom_right[1] - shrink_height)

        # 탐지된 템플릿 중앙 좌표 계산
        center_x, center_y = get_random_point(adjusted_top_left, adjusted_bottom_right)

        # OpenCV 좌표를 pyautogui 좌표로 변환
        mouse_x = int(center_x / ratio_width) + mouse_offset[0]
        mouse_y = int(center_y / ratio_height) + mouse_offset[1]

        # 마우스 이동 및 클릭 수행 (click 옵션에 따라 클릭 여부 결정)
        if click:
            print(f"Moving mouse to center: ({mouse_x}, {mouse_y}) and clicking")
            move_and_click(mouse_x, mouse_y)
        else:
            print(f"Moving mouse to: ({mouse_x}, {mouse_y}) without clicking")
            move_cursor(mouse_x, mouse_y)

        # 스크린샷 저장
        # timestamp = time.strftime("%Y%m%d-%H%M%S")
        # result_path = os.path.join(capture_folder, f"{template_name}_{timestamp}.png")
        # cv2.imwrite(result_path, screen_color)
        # print(f"Captured image saved at: {result_path}")

        time.sleep(0.5)
        return top_left, bottom_right
    return None, None

# 이미지에서 텍스트 추출
async def read_text_from_image(screen, template, threshold=0.8, roi=None):
    """
    이미지에서 텍스트를 추출하는 함수.

    Parameters:
    - screen: 입력 이미지
    - template: 탐지할 템플릿 이미지
    - threshold: 매칭 정확도의 임계값 (기본값 0.8)
    - roi: 관심 영역 (좌측 상단 (x1, y1), 우측 하단 (x2, y2)) (기본값 None)

    Returns:
    - 추출된 텍스트
    """
    # ROI가 설정된 경우, 해당 영역만 탐지 대상으로 자름
    if roi is not None:
        screen = screen[roi[1]:roi[3], roi[0]:roi[2]]

    template_height, template_width = template.shape[:2]
    found = None

    
    # 다중 스케일 템플릿 매칭을 위한 루프
    for scale in np.linspace(0.8, 1.0, 10)[::-1]:  # 스케일 범위와 단계 수 조정
        resized_template_width = int(template_width * scale)
        resized_template_height = int(template_height * scale)

        resized = cv2.resize(template, (resized_template_width, resized_template_height))

        # 템플릿 크기가 화면을 초과하면 무시
        if resized.shape[0] > screen.shape[0] or resized.shape[1] > screen.shape[1]:
            continue

        result = cv2.matchTemplate(screen, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            if found is None or max_val > found[0]:
                found = (max_val, max_loc, resized.shape[1], resized.shape[0])
    
    # 템플릿 위치 반환 (탐지에 성공한 경우)
    if found:
        max_val, max_loc, resized_width, resized_height = found
        start_x = max_loc[0]
        start_y = max_loc[1]
        end_x = start_x + resized_width
        end_y = start_y + resized_height
    
        # 텍스트 추출을 위한 영역 자르기
        detected_region = screen[start_y:end_y, start_x:end_x]

        # EasyOCR 객체 생성
        reader = easyocr.Reader(['en', 'ko'])  # 영어와 한글 지원

        # 이미지를 OCR로 전달 (OpenCV 이미지 입력)
        results = reader.readtext(detected_region)

        for _, text, confidence in results:
            if confidence > 0.8:  # 신뢰도 80% 이상
                print(f"confidence: {confidence}")
                print(f"High confidence text: {text}")
                return text
    
    # 이미지 탐지 실패 시 None 반환
    return None


# Tesseract 실행 경로 설정 (Windows 사용자의 경우)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
async def compare_text_and_click_image(screen, first_template, search_text, second_template, threshold=0.8, roi=None):
    """
    미리 설정한 범위 내에서 이미지를 탐지하고, 텍스트 또는 숫자가 일치하면 
    두 번째 이미지를 탐지하고 클릭하는 함수.

    Parameters:
    - screen: 입력 이미지
    - first_template: 첫 번째 탐지할 템플릿 이미지
    - search_text: 찾고자 하는 텍스트 또는 숫자
    - second_template: 텍스트 탐지 후 클릭해야 할 두 번째 템플릿 이미지
    - threshold: 매칭 정확도의 임계값 (기본값 0.8)
    - roi: 관심 영역 (좌측 상단 (x1, y1), 우측 하단 (x2, y2)) (기본값 None)

    Returns:
    - 클릭 성공 여부 (True/False)
    """
    # ROI가 설정된 경우, 해당 영역만 탐지 대상으로 자름
    if roi is not None:
        screen = screen[roi[1]:roi[3], roi[0]:roi[2]]

    template_height, template_width = first_template.shape[:2]
    found = None

    # 다중 스케일 템플릿 매칭을 위한 루프
    for scale in np.linspace(0.8, 1.0, 10)[::-1]:  # 스케일 범위와 단계 수 조정
        resized_template_width = int(template_width * scale)
        resized_template_height = int(template_height * scale)

        resized = cv2.resize(first_template, (resized_template_width, resized_template_height))

        # 템플릿 크기가 화면을 초과하면 무시
        if resized.shape[0] > screen.shape[0] or resized.shape[1] > screen.shape[1]:
            continue

        result = cv2.matchTemplate(screen, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        print(f"max_loc: {max_loc}, max_val: {max_val}")

        if max_val >= threshold:
            if found is None or max_val > found[0]:
                found = (max_val, max_loc, resized.shape[1], resized.shape[0])
    print(found)
    # 첫 번째 템플릿 위치 반환 (탐지에 성공한 경우)
    if found:
        max_val, max_loc, resized_width, resized_height = found
        start_x = max_loc[0]
        start_y = max_loc[1]
        end_x = start_x + resized_width
        end_y = start_y + resized_height

        # 텍스트 추출을 위한 영역 자르기
        detected_region = screen[start_y:end_y, start_x:end_x]

        # OCR을 사용하여 텍스트 추출
        extracted_text = pytesseract.image_to_string(detected_region, lang='kor').strip()
        print(f"Extracted text: {extracted_text}")

        # 텍스트가 찾고자 하는 텍스트와 일치하는지 확인
        if search_text in extracted_text:
            # 두 번째 템플릿을 화면에서 탐지하고 클릭
            second_template_height, second_template_width = second_template.shape[:2]
            found = None

            # 다중 스케일 템플릿 매칭
            for scale in np.linspace(0.8, 1.0, 10)[::-1]:
                resized_template_width = int(second_template_width * scale)
                resized_template_height = int(second_template_height * scale)

                resized = cv2.resize(second_template, (resized_template_width, resized_template_height))

                if resized.shape[0] > screen.shape[0] or resized.shape[1] > screen.shape[1]:
                    continue

                result = cv2.matchTemplate(screen, resized, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)

                if max_val >= threshold:
                    if found is None or max_val > found[0]:
                        found = (max_val, max_loc, resized.shape[1], resized.shape[0])

            # 두 번째 템플릿 위치 반환 및 클릭 (탐지에 성공한 경우)
            if found:
                max_val, max_loc, resized_width, resized_height = found
                click_x = max_loc[0] + resized_width // 2
                click_y = max_loc[1] + resized_height // 2

                # pyautogui를 사용해 클릭 수행
                pyautogui.click(click_x, click_y)

                return True

    # 이미지 탐지와 클릭 실패 시 False 반환
    return False
