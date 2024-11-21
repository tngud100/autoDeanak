from src.service.logic.utils.image_processing import handle_detection
from src.service.logic.utils.image_processing import detect_and_click_template
from src.service.logic.utils.error import handle_error
from src.service.logic.utils.exceptions import NoDetectionError
from src.dao.service_queue_dao import serviceQueueDao
from src.service.logic.utils.keyboard_mouse import exit_main_loop

async def main_detection(db, detection_states, detection_count, screen, ratio_width, ratio_height, templates, deanak_id, worker_id, service):
  # 메인 화면 탐지 및 처리
  if not detection_states["main_screen_passed"] and detection_states["team_select_passed"]:
    try:
      detection_count["main_screen"] += 1
      if detection_count["main_screen"] > 20:
        raise NoDetectionError("메인 화면이 20회 이상 탐지되지 않았습니다.")
      if handle_detection(screen, templates["main_screen"], lambda: None):
        # roi = (0, 0, 1920, 100)
        # if handle_detection(screen, templates["top_class"], lambda: None, roi=roi, use_color=True) and not handle_detection(screen, templates["no_top_class"], lambda: None, roi=roi, use_color=True):
        #     detect_and_click_template(screen, templates["market_btn"], 0.8, ratio_width, ratio_height, "marketBtn")
        #     detection_states["main_screen_passed"] = True
        #     serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '이적시장')
        #     continue
        # elif topClass:
        #     press_exit_key()  # Alt+F4
        #     time.sleep(2)
        #     press_tilde_key()  # `
        #     show_notification("알림", "탑 클래스가 없습니다. 관리자의 확인이 필요합니다.")
        #     break
        # else:
        detection_count["market_btn"] += 1
        if detection_count["market_btn"] > 20:
          raise NoDetectionError("이적 시장 버튼이 20회 이상 탐지되지 않았습니다.")
        if detect_and_click_template(screen, templates["market_btn"], 0.8, ratio_width, ratio_height, "marketBtn"):
          detection_states["main_screen_passed"] = True
          await serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '이적시장')
          return detection_states, detection_count
    except NoDetectionError as e:
      handle_error(e, "메인 화면에서 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
    except Exception as e:
      handle_error(e, "메인 화면에서 예상치 못한 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
  return detection_states, detection_count

