# main.py
import time
import pyautogui
from sqlalchemy.orm import Session

from src.service.logic.mainProcess.detect_getItem_screen import get_item_detection
from src.service.logic.mainProcess.detect_get_all import finish_get_all_item_detection
from src.service.logic.mainProcess.detect_main import main_detection
from src.service.logic.mainProcess.detect_market import market_detection
from src.service.logic.mainProcess.detect_notice import notice_detection
from src.service.logic.mainProcess.detect_team_select import detect_team_select_for_10min, team_select_detection
from src.service.logic.mainProcess.initialize import initialize
from src.service.logic.mainProcess.remote_focus import remote_focus
from src.service.logic.utils.capture import screen_capture
from src.service.logic.utils.image_processing import load_templates
from src.service.logic.utils.keyboard_mouse import exit_main_loop
from src.service.logic.utils.error import handle_error
from src.dao.service_queue_dao import serviceQueueDao
from src.dao.remote_pcs_dao import remoteDao

from src.service.logic.mainProcess.detect_anykey import anykey_detection
from src.service.logic.mainProcess.detect_password import password_detection



# 자동 대낙, 10분대낙
async def main(db: Session, info: dict):
    try:
        # 초기화
        service_list, service, password_list, queue_id, deanak_id, worker_id, pc_num, detection_states, detection_count = initialize(info)
        # 템플릿 이미지 로드
        templates = load_templates(password_list)
        if templates is None:
            raise FileNotFoundError("템플릿 이미지 로드 중 오류 발생")
        # 원격 데스크탑 활성화
        await remote_focus(db, pc_num, deanak_id, worker_id)

        while True:
            try:
                # 화면 캡처 수행
                screen = screen_capture()
                screen_height, screen_width = screen.shape[:2]
                ratio_width = screen_width / pyautogui.size()[0]
                ratio_height = screen_height / pyautogui.size()[1]
                handler = None

                # anyKey 화면 탐지 및 처리
                detection_states, detection_count, handler = await anykey_detection(db, detection_states, detection_count, screen, templates, deanak_id, worker_id)
                if handler == "break":
                    break
                elif handler == "continue":
                    time.sleep(1)  # 일정 시간 대기
                    continue

                # 비밀번호 화면 탐지 및 처리
                detection_states, detection_count, handler = await password_detection(db, detection_states, detection_count, screen, screen_width, screen_height, ratio_width, ratio_height, templates, deanak_id, worker_id)
                if handler == "break":
                    break
                elif handler == "continue":
                    time.sleep(1)  # 일정 시간 대기
                    continue                

                # 공지사항 화면 탐지 및 처리
                detection_states, detection_count, handler = await notice_detection(db, detection_states, detection_count, screen, templates, deanak_id, worker_id)
                if handler == "break":
                    break
                elif handler == "continue":
                    time.sleep(1)  # 일정 시간 대기
                    continue

                # 10분 접속 처리
                detection_states, detection_count, handler = await detect_team_select_for_10min(db, detection_states, detection_count, deanak_id, worker_id, queue_id, pc_num, service, service_list)
                if handler == "break":
                    break

                # 팀 선택 화면 탐지 및 처리
                detection_states, detection_count, handler = await team_select_detection(db, detection_states, detection_count, screen, templates, ratio_width, ratio_height, deanak_id, worker_id, service, service_list)
                if handler == "break":
                    break
                elif handler == "continue":
                    time.sleep(1)  # 일정 시간 대기
                    continue

                # 메인 화면 탐지 및 처리
                detection_states, detection_count, handler = await main_detection(db, detection_states, detection_count, screen, ratio_width, ratio_height, templates, deanak_id, worker_id)
                if handler == "break":
                    break
                elif handler == "continue":
                    time.sleep(1)  # 일정 시간 대기
                    continue

                # 이적 시장 화면 탐지 및 처리
                detection_states, detection_count, handler = await market_detection(db, detection_states, detection_count, screen, ratio_width, ratio_height, templates, deanak_id, worker_id)
                if handler == "break":
                    break
                elif handler == "continue":
                    time.sleep(1)  # 일정 시간 대기
                    continue

                # 아이템 획득 화면 탐지 및 처리
                detection_states, detection_count, handler = await get_item_detection(db, detection_states, detection_count, screen, ratio_width, ratio_height, templates, deanak_id, worker_id)
                if handler == "break":
                    break
                elif handler == "continue":
                    time.sleep(1)  # 일정 시간 대기
                    continue

                # 모든 아이템 획득 확인 화면 탐지 및 처리
                detection_states, detection_count, handler = await finish_get_all_item_detection(db, detection_states, detection_count, screen, ratio_width, ratio_height, templates, deanak_id, worker_id)
                if handler == "break":
                    break
                elif handler == "continue":
                    time.sleep(1)  # 일정 시간 대기
                    continue

                # 모든 화면 탐지 후 종료
                if detection_states["finish_get_all_item"]:
                    print(f"{deanak_id}번의 자동대낙이 완료되었습니다.")
                    try:
                        await serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '완료')
                        await serviceQueueDao.update_queue_state(db, deanak_id, worker_id, 1)
                        await serviceQueueDao.update_end_time(db, deanak_id, worker_id, time.strftime('%Y-%m-%d %H:%M:%S'))
                        await exit_main_loop()
                        break
                    except Exception as e:
                        handle_error(e, "모든 화면 탐지 후 종료 중 예상치 못한 오류 발생", True)
                        await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
                        break

                time.sleep(3)  # 일정 시간 대기

            except Exception as e:
                handle_error(e, "메인 함수의 루프문 내부에서 예상치 못한 오류 발생", True)
                await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
                break
            
    except FileNotFoundError as e:
        handle_error(e, "업로드 하신 파일을 찾을 수 없습니다.", True)
        await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
        await exit_main_loop()
    except Exception as e:
        handle_error(e, "메인 함수 내부에서 예상치 못한 오류 발생", True)
        await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
        await exit_main_loop()
    finally:
        await remoteDao.update_remote_pc_process_by_worker_id(db, pc_num, 'idle')
