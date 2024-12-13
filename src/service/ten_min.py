# main.py
import asyncio
import time
import pyautogui
from sqlalchemy.orm import Session

from src import state
from dependencies import get_db_context
from src.service.logic.mainProcess.detect_notice import notice_detection
from src.service.logic.mainProcess.detect_team_select import detect_team_select_for_10min
from src.service.logic.mainProcess.initialize import initialize
from src.service.logic.mainProcess.remote_focus import remote_focus
from src.service.logic.utils.capture import screen_capture
from src.service.logic.utils.image_processing import load_templates
from src.service.logic.utils.keyboard_mouse import exit_main_loop, finish_main_loop
from src.service.logic.utils.error import handle_error
from src.dao.service_queue_dao import serviceQueueDao
from src.dao.remote_pcs_dao import remoteDao

from src.service.logic.mainProcess.detect_anykey import anykey_detection
from src.service.logic.mainProcess.detect_password import password_detection



# 자동 대낙, 10분대낙
async def ten_min(info: dict):
    try:
        async with get_db_context() as db:
            # 초기화
            service_list, service, password_list, queue_id, deanak_id, worker_id, pc_num, detection_states, detection_count = initialize(info)
            # 템플릿 이미지 로드
            templates = load_templates(password_list)
            if templates is None:
                raise FileNotFoundError("템플릿 이미지 로드 중 오류 발생")
            
            # 원격 데스크탑 활성화
            isActive = await remote_focus(db, pc_num, deanak_id, worker_id)
            if isActive:
                state.ten_min_loop = True
            if isActive is False:
                await exit_main_loop(service)

            while state.ten_min_loop:
                try:
                    # 화면 캡처 수행
                    screen = screen_capture()
                    screen_height, screen_width = screen.shape[:2]
                    ratio_width = screen_width / pyautogui.size()[0]
                    ratio_height = screen_height / pyautogui.size()[1]

                    # anyKey 화면 탐지 및 처리
                    detection_states, detection_count = await anykey_detection(db, detection_states, detection_count, screen, templates, deanak_id, worker_id, service)

                    # 비밀번호 화면 탐지 및 처리
                    detection_states, detection_count = await password_detection(db, detection_states, detection_count, screen, screen_width, screen_height, ratio_width, ratio_height, templates, deanak_id, worker_id, service)

                    # 공지사항 화면 탐지 및 처리
                    detection_states, detection_count = await notice_detection(db, detection_states, detection_count, screen, templates, deanak_id, worker_id, service)

                    # 10분 접속 처리
                    detection_states, detection_count = await detect_team_select_for_10min(db, detection_states, detection_count, deanak_id, worker_id, queue_id, pc_num, service, service_list)

                    if detection_states['team_select_passed'] is True:
                        state.ten_min_loop = False
                    await asyncio.sleep(2)  # 일정 시간 대기

                except Exception as e:
                    handle_error(e, "메인 함수의 루프문 내부에서 예상치 못한 오류 발생", True)
                    await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
                    await exit_main_loop(service)
                
    except FileNotFoundError as e:
        handle_error(e, "업로드하신 파일을 찾을 수 없습니다.", True)
        await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
        await exit_main_loop(service)
    except Exception as e:
        handle_error(e, "메인 함수 내부에서 예상치 못한 오류 발생", True)
        await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
        await exit_main_loop(service)
    finally:
        await remoteDao.update_remote_pc_process_by_worker_id(db, worker_id, 'idle')