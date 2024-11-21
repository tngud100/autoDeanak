from src.service.logic.utils.error import handle_error
from src.service.logic.utils.image_processing import handle_detection, detect_and_click_template
from src.dao.service_queue_dao import serviceQueueDao
from src.service.logic.utils.keyboard_mouse import exit_main_loop
from src.service.logic.utils.exceptions import NoDetectionError

async def market_detection(db, detection_states, detection_count, screen, ratio_width, ratio_height, templates, deanak_id, worker_id, service):
  # 이적 시장 화면 탐지 및 처리
  if not detection_states["market_screen_passed"] and detection_states["main_screen_passed"]:
    try:
      detection_count["market_screen"] += 1
      if detection_count["market_screen"] > 20:
        raise NoDetectionError("이적 시장 화면이 20회 이상 탐지되지 않았습니다.")
      if handle_detection(screen, templates["market_screen"], lambda: None):
        detection_count["list_btn"] += 1
        if detection_count["list_btn"] > 20:
          raise NoDetectionError("판매 선수 리스트 버튼이 20회 이상 탐지되지 않았습니다.")
        if detect_and_click_template(screen, templates["list_btn"], 0.8, ratio_width, ratio_height, "listBtn"):
          detection_states["market_screen_passed"] = True
          await serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '상세 이적시장')
          return detection_states, detection_count
    except NoDetectionError as e:
      handle_error(e, "이적 시장 화면에서 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
    except Exception as e:
      handle_error(e, "이적 시장 화면에서 예상치 못한 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
  return detection_states, detection_count