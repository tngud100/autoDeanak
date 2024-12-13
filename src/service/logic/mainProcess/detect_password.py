import logging
from src.service.logic.utils.error import handle_error
from src.service.logic.utils.image_processing import handle_detection, detect_and_click_template
from src.dao.service_queue_dao import serviceQueueDao
from src.service.logic.utils.exceptions import NoDetectionError, WrongPasswordError
from src.service.logic.utils.keyboard_mouse import exit_main_loop
from src.service.logic.utils.capture import screen_capture

async def password_detection(db, detection_states, detection_count, screen, screen_width, screen_height, ratio_width, ratio_height, templates, deanak_id, worker_id, service):
    # 비밀번호 화면 탐지 및 처i리
    if not detection_states["password_passed"] and detection_states["anyKey_passed"]:
        try:
            if handle_detection(screen, templates["password_screen"], lambda: None):
                detection_count["password"] += 1
                if detection_count["password"] > 20:
                    raise NoDetectionError("비밀번호 화면이 20회 이상 탐지되지 않았습니다.")
                roi = (0, 0, screen_width, screen_height)
                for idx, template in enumerate(templates["password_templates"]):
                    detect_and_click_template(screen, template, 0.8, ratio_width, ratio_height, roi=roi)

                if handle_detection(screen, templates["password_confirm"], lambda: detect_and_click_template(screen, templates["password_confirm"], 0.8, ratio_width, ratio_height, roi=roi), roi=roi):
                    screen = screen_capture()
                    if handle_detection(screen, templates["wrong_password"], lambda: None, roi=roi):
                        raise WrongPasswordError("비밀번호가 틀렸습니다.")
                    detection_states["password_passed"] = True
                    await serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '공지사항')
                    return detection_states, detection_count

        except (NoDetectionError, WrongPasswordError) as e:
            handle_error(e, "비밀번호 화면에서 오류 발생", True)
            await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
            await exit_main_loop(service)
            return detection_states, detection_count
        except Exception as e:
            handle_error(e, "비밀번호 화면에서 예상치 못한 오류 발생", True)
            await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
            await exit_main_loop(service)
            return detection_states, detection_count
        
    return detection_states, detection_count