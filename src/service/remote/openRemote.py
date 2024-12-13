import asyncio
import logging
import httpx
import pyautogui
import pygetwindow as gw
import time
from pywinauto import Desktop
from sqlalchemy.ext.asyncio import AsyncSession

from src import state
from src.entity.remote_pcs_entity import RemotePC
from src.dao.remote_pcs_dao import remoteDao
from src.dao.deanak_dao import deanakDao
from src.entity.service_queue_entity import serviceQueue
# from src.service.logic.utils.keyboard_mouse import exit_main_loop


# 방향키 이동 함수
async def move_arrow_key(steps, direction='right'):
    # key = win32con.VK_RIGHT if direction == 'right' else win32con.VK_LEFT
    # for _ in range(steps):
    #     win32api.keybd_event(key, 0, 0, 0)
    #     time.sleep(0.1)
    #     win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
    #     time.sleep(0.1)
    key = 'right' if direction == 'right' else 'left'
    for _ in range(steps):
        pyautogui.press(key)
        time.sleep(0.1)
        print(f"{key} 키 입력 완료. {steps}번 반복.")

# ` 키를 누르는 함수
async def press_tilde_key():
    # win32api.keybd_event(192, 0, 0, 0)
    # time.sleep(0.1)
    # win32api.keybd_event(192, 0, win32con.KEYEVENTF_KEYUP, 0)
    pyautogui.press('`')
    time.sleep(0.1)

# 창 초기화 및 랜덤 이동 함수
async def initialize_and_move(num):
    await move_arrow_key(1, 'right')  # 초기화
    await move_arrow_key(4, 'left')  # 초기화
    await asyncio.sleep(1)

    running_num = num  # 현재 작업중인 컴퓨터

    if running_num == 1:
        await move_arrow_key(1, 'right')
        await move_arrow_key(1, 'left')
    else:
        await move_arrow_key(running_num - 1, 'right')
    
    # ~ 키 입력
    await press_tilde_key()
    print(f"~ 키 입력 완료. 컴퓨터 번호 {running_num}.")
    
    return running_num
    
async def check_running_PC(db: AsyncSession, service_queue_data: serviceQueue):
    worker_id = service_queue_data.worker_id
    pcs_data = await remoteDao.find_remote_pc_process_by_worker_id(db, worker_id)
    deanak_data = await deanakDao.find_deanak_data(db, service_queue_data.deanak_id)

    if pcs_data == 'working':
        return deanak_data
    # else:
    #     await exit_main_loop(deanak_data.service)

    
async def select_remote(num):
    try:
        desktop = Desktop(backend="uia")
        window = desktop.window(title_re="멀티 원격관리 프로그램 Rimo")
        if not window.exists():
            print("해당 프로그램 창을 찾을 수 없습니다.")
            return
        
        window.restore()
        window.set_focus()
        running_num = await initialize_and_move(num)
        return running_num
    except Exception as e:
        print(f"오류 발생: {e}")

# 프로그램 실행 로직
async def runOpenRemote(pc_num: int):
    try:
        running_num = await select_remote(pc_num)
        print(f"{running_num}번 {running_num} 창이 열렸습니다.")
        await asyncio.sleep(1)

    except Exception as e:
        logging.error(f"Failed to activate window: {e}")
        return {"error": str(e)}

async def stop_remote_pc(db: AsyncSession, service: str):
    server_id = await state.unique_id().read_unique_id()
    # remote_pcs의request를 stop_deanak으로 바꾸고 process를 error로 바꾼다.
    await remoteDao.update_remote_pc_process_by_server_id(db, server_id, 'error_stop')
    
    if service == "일반대낙":
        await remoteDao.update_tasks_request(db, server_id, 'deanak_stop')
    if service == "10분접속":
        await remoteDao.update_tasks_request(db, server_id, 'ten_min_stop')
        
