# main.py
import asyncio
import logging
import time
import pyautogui
from sqlalchemy.orm import Session

from dependencies import get_db_context
from src.dao.deanak_dao import deanakDao
from src.service.logic.mainProcess.detect_getItem_screen import get_item_detection
from src.service.logic.mainProcess.detect_get_all import finish_get_all_item_detection
from src.service.logic.mainProcess.detect_main import main_detection
from src.service.logic.mainProcess.detect_market import market_detection
from src.service.logic.mainProcess.detect_notice import notice_detection
from src.service.logic.mainProcess.detect_team_select import team_select_detection
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
from src import state


# 자동 대낙, 10분대낙
async def deanak(info: dict):
    try:
        async with get_db_context() as db:
            # 초기화
            service_list, service, password_list, _, deanak_id, worker_id, pc_num, detection_states, detection_count = initialize(info)
            # 템플릿 이미지 로드
            templates = load_templates(password_list)
            if templates is None:
                raise FileNotFoundError("템플릿 이미지 로드 중 오류 발생")
            # 원격 데스크탑 활성화
            isActive = await remote_focus(db, pc_num, deanak_id, worker_id)
            if isActive:
                state.main_loop = True
            if isActive is False:
                await exit_main_loop(service)

            while state.main_loop:
                try:
                    # 화면 캡처 수행
                    screen = screen_capture()
                    screen_height, screen_width = screen.shape[:2]
                    ratio_width = screen_width / pyautogui.size()[0]
                    ratio_height = screen_height / pyautogui.size()[1]
                    
                    # anyKey 화면 탐지 및 처리
                    detection_states, detection_count= await anykey_detection(db, detection_states, detection_count, screen, templates, deanak_id, worker_id, service)
                    
                    # 비밀번호 화면 탐지 및 처리
                    detection_states, detection_count = await password_detection(db, detection_states, detection_count, screen, screen_width, screen_height, ratio_width, ratio_height, templates, deanak_id, worker_id, service)
                    
                    # 공지사항 화면 탐지 및 처리
                    detection_states, detection_count = await notice_detection(db, detection_states, detection_count, screen, templates, deanak_id, worker_id, service)

                    # 팀 선택 화면 탐지 및 처리
                    detection_states, detection_count = await team_select_detection(db, detection_states, detection_count, screen, templates, ratio_width, ratio_height, deanak_id, worker_id, service, service_list)
                    
                    # 메인 화면 탐지 및 처리
                    detection_states, detection_count = await main_detection(db, detection_states, detection_count, screen, ratio_width, ratio_height, templates, deanak_id, worker_id, service)

                    # 이적 시장 화면 탐지 및 처리
                    detection_states, detection_count = await market_detection(db, detection_states, detection_count, screen, ratio_width, ratio_height, templates, deanak_id, worker_id, service)
                    
                    # 아이템 획득 화면 탐지 및 처리
                    detection_states, detection_count = await get_item_detection(db, detection_states, detection_count, screen, ratio_width, ratio_height, templates, deanak_id, worker_id, service)

                    # 모든 아이템 획득 확인 화면 탐지 및 처리
                    detection_states, detection_count = await finish_get_all_item_detection(db, detection_states, detection_count, screen, ratio_width, ratio_height, templates, deanak_id, worker_id, service)
                    
                    # 모든 화면 탐지 후 종료
                    if detection_states["finish_get_all_item"]:
                        print(f"{deanak_id}번의 자동대낙이 완료되었습니다.")
                        try:
                            await serviceQueueDao.update_queue_process(db, deanak_id, worker_id, '완료')
                            await serviceQueueDao.update_queue_state(db, deanak_id, worker_id, 1)
                            await serviceQueueDao.update_end_time(db, deanak_id, worker_id, time.strftime('%Y-%m-%d %H:%M:%S'))
                            await deanakDao.update_deanak_state(db, deanak_id, 3)
                            await finish_main_loop(service)
                        except Exception as e:
                            handle_error(e, "모든 화면 탐지 후 종료 중 예상치 못한 오류 발생", True)
                            await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
                            await exit_main_loop(service)

                    await asyncio.sleep(1)

                except Exception as e:
                    handle_error(e, "메인 함수의 루프문 내부에서 예상치 못한 오류 발생", True)
                    await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
                    await exit_main_loop(service)
            
    except FileNotFoundError as e:
        handle_error(e, "업로드 하신 파일을 찾을 수 없습니다.", True)
        await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
        await exit_main_loop(service)
    except Exception as e:
        handle_error(e, "메인 함수 내부에서 예상치 못한 오류 발생", True)
        await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
        await exit_main_loop(service)
    finally:
        await remoteDao.update_remote_pc_state_by_worker_id(db, worker_id, 'idle')
