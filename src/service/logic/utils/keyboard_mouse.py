# keyboard_mouse.py

import asyncio
import pyautogui
from dependencies import get_db_context
from src import state
from src.service.remote import openRemote

async def move_cursor(x, y):
    """마우스를 (x, y) 좌표로 이동합니다."""
    # win32api.SetCursorPos((int(x), int(y)))
    pyautogui.moveTo(x, y)

async def move_and_click(x, y):
    """마우스를 (x, y) 좌표로 이동한 뒤 클릭합니다."""
    # move_cursor(x, y)
    # win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
    # time.sleep(0.1)  # 클릭을 안정적으로 수행하기 위해 잠시 대기
    # win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
    pyautogui.moveTo(x, y)
    pyautogui.click()

async def press_esc_key():
    """Esc 키를 누르고 떼는 동작을 시뮬레이션합니다."""
    # win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)  # Esc 키 누름
    # time.sleep(0.1)
    # win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)  # Esc 키 뗌
    pyautogui.press('esc')

async def press_exit_key():
    """Alt + F4 키를 누르고 떼는 동작을 시뮬레이션합니다."""
    # win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # Alt 키 누름
    # win32api.keybd_event(win32con.VK_F4, 0, 0, 0)  # F4 키 누름
    # time.sleep(0.1)
    # win32api.keybd_event(win32con.VK_F4, 0, win32con.KEYEVENTF_KEYUP, 0)  # F4 키 뗌
    # win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt 키 뗌
    pyautogui.hotkey('alt', 'f4')

async def press_tilde_key():
    """` 키를 누르고 떼는 동작을 시뮬레이션합니다."""
    # win32api.keybd_event(192, 0, 0, 0)  # ` 키 누름
    # time.sleep(0.05)
    # win32api.keybd_event(192, 0, win32con.KEYEVENTF_KEYUP, 0)  # ` 키 뗌
    pyautogui.press('`')

async def exit_main_loop(service):
    # press_exit_key()
    if service == state.deanak_service:
        state.main_loop = False
        state.deanak_is_running = False
    if service == state.ten_min_service:
        state.ten_min_loop = False
        state.ten_min_is_running = False
        
    async with get_db_context() as db:
        await openRemote.delete_remote_pc(db)

    await asyncio.sleep(1)
    # press_tilde_key()

async def finish_main_loop(service):
    if service == state.deanak_service:
        state.main_loop = False
    if service == state.ten_min_service:
        state.ten_min_loop = False

    await press_exit_key()
    await asyncio.sleep(5)
    await press_tilde_key()
    