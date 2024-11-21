import logging
from src.service.logic.utils.error import handle_error
from src.service.logic.utils.image_processing import handle_detection
from src.service.logic.utils.keyboard_mouse import press_esc_key
from src.dao.service_queue_dao import serviceQueueDao
from src.service.logic.utils.exceptions import NoDetectionError
from src.service.logic.utils.keyboard_mouse import exit_main_loop
import time


async def anykey_detection(db, detection_states, detection_count, screen, templates, deanak_id, worker_id, service):
  # anyKey 화면 탐지 및 처리
  if not detection_states["anyKey_passed"]:
    try:
      await press_esc_key()
      detection_count["anyKey"] += 1
      if detection_count["anyKey"] > 20:
        raise NoDetectionError("anyKey 화면이 20회 이상 탐지되지 않았습니다.")
      if handle_detection(screen, templates["password_screen"], lambda: None):
        detection_states["anyKey_passed"] = True
        await serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '대낙 2차 비밀번호 입력')
        await serviceQueueDao.update_start_time(db, deanak_id, worker_id, time.strftime('%Y-%m-%d %H:%M:%S'))
        return detection_states, detection_count
      
    except NoDetectionError as e:
      handle_error(e, "anyKey 화면 탐지 횟수 초과 후 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      # await remoteDao.update_remote_pc_state_by_pc_num(db, pc_num, 'idle')
      logging.info("NoDetectionError 발생 - 최대 허용 횟수 초과로 루프 종료 시도")
      await exit_main_loop(service)
      return detection_states, detection_count
    except Exception as e:
      handle_error(e, "anyKey 화면에서 예상치 못한 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      # await remoteDao.update_remote_pc_state_by_pc_num(db, pc_num, 'idle')
      logging.info("NoDetectionError 발생 - 최대 허용 횟수 초과로 루프 종료 시도")
      await exit_main_loop(service)
      return detection_states, detection_count
    
  return detection_states, detection_count