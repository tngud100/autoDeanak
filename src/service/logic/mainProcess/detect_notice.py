from src.service.logic.utils.error import handle_error
from src.service.logic.utils.image_processing import handle_detection
from src.service.logic.utils.keyboard_mouse import press_esc_key
from src.dao.service_queue_dao import serviceQueueDao
from src.service.logic.utils.exceptions import NoDetectionError
from src.service.logic.utils.keyboard_mouse import exit_main_loop

async def notice_detection(db, detection_states, detection_count, screen, templates, deanak_id, worker_id, service):
  # 공지사항 화면 탐지 및 처리
  if not detection_states["notice_passed"] and detection_states["password_passed"]:
    try:
      await press_esc_key()
      detection_count["notice"] += 1
      if detection_count["notice"] > 20:
        raise NoDetectionError("공지사항 화면이 20회 이상 탐지되지 않았습니다.")
      if handle_detection(screen, templates["team_select_screen"], lambda: None):
        detection_states["notice_passed"] = True
        await serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '팀선택')
        return detection_states, detection_count
    except NoDetectionError as e:
      handle_error(e, "공지사항 화면에서 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
    except Exception as e:
      handle_error(e, "공지사항 화면에서 예상치 못한 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
  return detection_states, detection_count