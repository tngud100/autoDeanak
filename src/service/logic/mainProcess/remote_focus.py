import pyautogui
import pygetwindow as gw
from src.service.logic.utils.error import handle_error
from src.dao.service_queue_dao import serviceQueueDao
from src.service.logic.utils.exceptions import unactivatedRemoteError
from src.service.logic.utils.keyboard_mouse import exit_main_loop

async def remote_focus(db, pc_num, deanak_id, worker_id):
    screen_width, screen_height = pyautogui.size()
    print(f"Screen size: {screen_width}x{screen_height}")

    # 모든 창 목록 가져오기 및 창 활성화
    try:
        windows = gw.getWindowsWithTitle(f'{pc_num}번 {pc_num}')
        if windows:
            windows[0].activate()
            return True
        else:
            raise unactivatedRemoteError(f"원격 프로그램의 {pc_num}번 {pc_num}창이 활성화 되지 않았습니다")
    except unactivatedRemoteError as e:
        handle_error(e, f"원격 프로그램 activate오류", True)
        await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
        return False
    except Exception as e:
        handle_error(e, "예상치 못한 오류 발생", True)
        await serviceQueueDao.error_update(db, deanak_id, worker_id, type(e).__name__)
        return False