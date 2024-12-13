import logging
from src.service.logic.utils.image_processing import detect_template, handle_detection
from src.service.logic.utils.image_processing import detect_and_click_template
from src.service.logic.utils.error import handle_error
from src.service.logic.utils.exceptions import NoDetectionError, SkipPurchaseException
from src.dao.service_queue_dao import serviceQueueDao
from src.service.logic.utils.keyboard_mouse import exit_main_loop

async def purchase_detection(db, detection_states, detection_count, screen, ratio_width, ratio_height, templates, deanak_id, worker_id, service):
  # 메인 화면 탐지 및 처리
  if not detection_states["purchase_before_main_screen_passed"] and detection_states["team_select_passed"]:
    try:
      if detection_count["purchase_before_main_screen"] > 5:
        raise SkipPurchaseException("메인 화면 전 구매 화면을 스킵합니다")
      
      top_left, bottom_right, _ = detect_template(screen, templates["purchase_before_main_screen"], 0.8)
      if top_left == None or bottom_right == None:
        detection_count["purchase_before_main_screen"] += 1
      
      if top_left and bottom_right:
        detection_count["purchase_cancel_btn"] += 1
        if detection_count["purchase_cancel_btn"] > 20:
          raise NoDetectionError("구매 화면 나가기 버튼이 20회 이상 탐지되지 않았습니다.")
        
        roi = top_left[0], top_left[1], bottom_right[0], bottom_right[1]

        if handle_detection(screen, templates["purchase_cancel_btn"], lambda: detect_and_click_template(screen, templates["purchase_cancel_btn"], 0.8, ratio_width, ratio_height, roi=roi), roi=roi):
          await serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '메인 화면 전 구매 화면')
          detection_states["purchase_before_main_screen_passed"] = True
          return detection_states, detection_count
    
    except SkipPurchaseException as e:
      logging.info("메인 화면 전 구매 화면 스킵")
      detection_states["purchase_before_main_screen_passed"] = True
      return detection_states, detection_count
    except NoDetectionError as e:
      handle_error(e, "구매화면 나가기 버튼 찾기에서 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
    except Exception as e:
      handle_error(e, "메인 화면 전 구매 화면에서 못한 오류 발생", True)
      await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
      await exit_main_loop(service)
      return detection_states, detection_count
  return detection_states, detection_count
