import asyncio

deanak_running_task = None
deanak_is_running = False
deanak_service = '일반대낙'
ten_min_running_task = None
ten_min_is_running = False
ten_min_service = '10분접속'
lock = asyncio.Lock()

main_loop = False
ten_min_loop = False