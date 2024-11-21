# 오류 처리 및 정지 함수
import asyncio
from datetime import datetime
import os
import traceback
from typing import Optional
from src import state

# 에러 로그 파일 경로 설정
ERROR_LOG_FILE = 'logs/error_log.txt'

def handle_error(e: Exception, message: str, critical: bool = False, user_message: Optional[str] = None):
    """
    에러를 처리하고 로그를 기록하며, 필요 시 알림을 보냅니다.

    :param e: 발생한 예외 객체
    :param message: 로그에 기록할 메시지
    :param critical: 심각한 에러 여부 (True일 경우 추가 조치)
    :param user_message: 사용자에게 표시할 메시지 (옵션)
    """
    # logs 폴더가 없으면 생성
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # 예외 타입과 스택 트레이스 얻기
    exception_type = type(e).__name__
    tb = traceback.format_exc()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_message = (
        f"Timestamp: {timestamp}\n"
        f"Exception Type: {exception_type}\n"
        f"Message: {message}\n"
        f"Error Details: {e}\n"
        f"Traceback:\n{tb}\n"
        + "-"*80 + "\n"
    )

    # 에러 로그를 텍스트 파일에 기록
    try:
        with open('logs/error_log.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(full_message)
    except Exception as file_error:
        # 파일 기록 실패 시 콘솔에만 출력
        print(f"Failed to write error log to file: {file_error}")

    # 심각한 에러일 경우 추가적인 처리
    if critical:
        print("Critical error occurred.")
        # 추가적인 알림이나 조치를 여기에 추가

    # 사용자에게 알림 (옵션)
    if user_message:
        pass
        # print(user_message)


def task_exception_handler(task):
    try:
        exception = task.exception()
        if exception:
            handle_error(exception, "auto_deanak에서 예상치 못한 오류 발생", critical=True)
            state.is_running = False
    except asyncio.CancelledError as e:
        handle_error(e, "해당 작업을 종료하는 도중 오류 발생", critical=True)
        state.is_running = False
