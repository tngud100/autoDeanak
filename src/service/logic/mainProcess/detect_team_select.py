
import asyncio
from src.service.logic.utils.error import handle_error
from src.service.logic.utils.image_processing import detect_template, detect_and_click_template
from src.service.logic.utils.keyboard_mouse import press_tilde_key, exit_main_loop
from src.service.logic.utils.exceptions import NoDetectionError
from src.service.logic.utils.image_processing import handle_detection
from src.service.logic.utils.keyboard_mouse import press_tilde_key
from src.service.logic.utils.keyboard_mouse import press_tilde_key
from src.dao.service_queue_dao import serviceQueueDao
from src.dao.ten_min_timer_dao import tenMinTimerDao
from src.dao.remote_pcs_dao import remoteDao
import time

async def detect_team_select_for_10min(db, detection_states, detection_count, deanak_id, worker_id, queue_id, pc_num, service, service_list):
  # 10분 접속 처리
  if not detection_states["team_select_passed"] and detection_states["notice_passed"] and service == service_list[1]:
    try:
      detection_count["team_select"] += 1
      if detection_count["team_select"] > 20:
          raise NoDetectionError("10분 접속 서비스 중 팀 선택 화면이 20회 이상 탐지되지 않았습니다.")
      await asyncio.sleep(1)
      detection_states["team_select_passed"] = True
      await serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '10분 접속')
      await serviceQueueDao.update_queue_state(db, deanak_id, worker_id, 2)
      await tenMinTimerDao.insert_timer(db, queue_id, pc_num)
      await remoteDao.update_remote_pc_process_by_worker_id(db, worker_id, 'idle')
      await press_tilde_key()  # `
      return detection_states, detection_count
    except Exception as e:
      handle_error(e, "10분 접속 대기 중 예상치 못한 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
  return detection_states, detection_count

async def team_select_detection(db, detection_states, detection_count, screen, templates, ratio_width, ratio_height, deanak_id, worker_id, service, service_list):
  # 팀 선택 화면 탐지 및 처리
  if not detection_states["team_select_passed"] and detection_states["notice_passed"]  and service == service_list[0]:
    try:
      detection_count["team_select"] += 1
      if detection_count["team_select"] > 20:
        raise NoDetectionError("일반 대낙 중 팀 선택 화면이 20회 이상 탐지되지 않았습니다.")
      if handle_detection(screen, templates["team_select_screen"], lambda: None):
        top_left, bottom_right, _ = detect_template(screen, templates["team_select_text"], 0.8)
        if top_left is not None and bottom_right is not None:
          offset_y = 6 * (bottom_right[1] - top_left[1])
        else:
          offset_y = 530

        detection_count["team_select_text"] += 1
        if detection_count["team_select_text"] > 20:
          raise NoDetectionError("팀 선택 텍스트가 20회 이상 탐지되지 않았습니다.")
        if detect_and_click_template(screen, templates["team_select_text"], 0.8, ratio_width, ratio_height, mouse_offset=(0, offset_y)):
          detection_states["team_select_passed"] = True
          await serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '메인화면')
          return detection_states, detection_count
        
    except NoDetectionError as e:
      handle_error(e, "팀 선택 화면에서 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
    except Exception as e:
      handle_error(e, "팀 선택 화면에서 예상치 못한 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
  return detection_states, detection_count