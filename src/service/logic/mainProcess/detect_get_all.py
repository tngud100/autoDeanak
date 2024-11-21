from src.service.logic.utils.error import handle_error
from src.service.logic.utils.image_processing import detect_template, handle_detection, detect_and_click_template
from src.dao.service_queue_dao import serviceQueueDao
from src.service.logic.utils.exceptions import NoDetectionError
from src.service.logic.utils.keyboard_mouse import exit_main_loop
import time

async def finish_get_all_item_detection(db, detection_states, detection_count, screen, ratio_width, ratio_height, templates, deanak_id, worker_id, service): 
  # 모든 아이템 획득 확인 화면 탐지 및 처리
  if not detection_states["finish_get_all_item"] and detection_states["get_item_screen_passed"]:
    try:
      detection_count["finish_get_all_item"] += 1
      if detection_count["finish_get_all_item"] > 20:
          raise NoDetectionError("모두 받기 리스트 화면이 20회 이상 탐지되지 않았습니다.")
      if handle_detection(screen, templates["get_all_screen"], lambda: None):
        if detection_states["arrange_btn_screen"] == False:
          detection_count["arrange_btn"] += 1
          if detection_count["arrange_btn"] > 20:
            raise NoDetectionError("정렬 버튼이 20회 이상 탐지되지 않았습니다.")
          top_left, bottom_right, _ = detect_template(screen, templates["arrange_btn_screen"], 0.8)
          if top_left and bottom_right:
            roi = top_left[0], top_left[1], bottom_right[0], bottom_right[1]
            if handle_detection(screen, templates["arrange_btn_screen"], lambda: detect_and_click_template(screen, templates["arrange_btn"], 0.8, ratio_width, ratio_height, "priceArrangeBtn", roi=roi), roi=roi):
                await serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '아이템 가격별 정렬 확인')
                detection_states["arrange_btn_screen"] = True
        else:
          detection_count["get_all_btn"] += 1
          if detection_count["get_all_btn"] > 20:
            raise NoDetectionError("모두 받기 버튼이 20회 이상 탐지되지 않았습니다.")
          if detect_and_click_template(screen, templates["get_all_btn"], 0.8, ratio_width, ratio_height, "getAllBtn"):
            detection_states["finish_get_all_item"] = True
            await serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '아이템 모두 받기')
            time.sleep(1)
            return detection_states, detection_count
    except NoDetectionError as e:
      handle_error(e, "모든 아이템 획득 확인 화면에서 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
    except Exception as e:
      handle_error(e, "모든 아이템 획득 확인 화면에서 예상치 못한 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
  return detection_states, detection_count