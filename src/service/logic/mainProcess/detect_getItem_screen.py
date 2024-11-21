from src.service.logic.utils.error import handle_error
from src.service.logic.utils.image_processing import handle_detection, detect_and_click_template
from src.dao.service_queue_dao import serviceQueueDao
from src.service.logic.utils.exceptions import NoDetectionError
from src.service.logic.utils.keyboard_mouse import exit_main_loop

async def get_item_detection(db, detection_states, detection_count, screen, ratio_width, ratio_height, templates, deanak_id, worker_id, service):
  # 아이템 획득 화면 탐지 및 처리
  if not detection_states["get_item_screen_passed"] and detection_states["market_screen_passed"]:
    try:
      detection_count["get_item_screen"] += 1
      if detection_count["get_item_screen"] > 20:
        raise NoDetectionError("아이템 획득 화면이 20회 이상 탐지되지 않았습니다.")
      
      if handle_detection(screen, templates["get_item_screen"], lambda: None):
        detection_count["get_item_btn"] += 1
        if detection_count["get_item_btn"] > 20:
          raise NoDetectionError("아이템 획득 확인 버튼이 20회 이상 탐지되지 않았습니다.")
        if detect_and_click_template(screen, templates["get_item_btn"], 0.8, ratio_width, ratio_height, "getItemBtn"):
          detection_states["get_item_screen_passed"] = True
          await serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '판매 리스트')
          return detection_states, detection_count
    except NoDetectionError as e:
      handle_error(e, "아이템 획득 화면에서 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
    except Exception as e:
      handle_error(e, "아이템 획득 화면에서 예상치 못한 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
  return detection_states, detection_count