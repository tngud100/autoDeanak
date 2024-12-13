import logging
import time
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.dao.deanak_dao import deanakDao
from src.dao.service_queue_dao import serviceQueueDao
from src.dao.ten_min_timer_dao import tenMinTimerDao
from src.dao.remote_pcs_dao import remoteDao, remoteWorkerPCDao
from src.entity.timer_entity import timer
from src.service.logic.utils.keyboard_mouse import press_exit_key, press_tilde_key
from src.service.remote import openRemote
from src.service.logic.utils.capture import screen_capture
from src.service.logic.utils.image_processing import check_and_load_template, detect_template

async def check_pass_10min(db: AsyncSession):
    ten_min_queue = await serviceQueueDao.find_service_queue_by_state(db, 2)
    if ten_min_queue:
        logging.info("10 minutes service found")
        pass_state = await check_pass_10min_service(db, ten_min_queue.queue_id, ten_min_queue.worker_id)
        if pass_state:
            logging.info("10 minutes passed")
            await serviceQueueDao.update_queue_process(db, ten_min_queue.deanak_id, ten_min_queue.worker_id, "완료")
            await serviceQueueDao.update_queue_state(db, ten_min_queue.deanak_id, ten_min_queue.worker_id, 1)
            await deanakDao.update_deanak_state(db, ten_min_queue.deanak_id, 3)
            await serviceQueueDao.update_end_time(db, ten_min_queue.deanak_id, ten_min_queue.worker_id, time.strftime('%Y-%m-%d %H:%M:%S'))


async def check_pass_10min_service(db: AsyncSession, queue_id: int, worker_id: str):
    pc_num = await remoteWorkerPCDao.find_worker_pc_num_by_worker_id(db, worker_id)
    timer_data: timer = await tenMinTimerDao.find_timer_by_queue_id_and_pc_num(db, queue_id, pc_num)
    
    team_select_screen = 'static/image/selectTeam.PNG'
    template = check_and_load_template(team_select_screen)
    
    if timer_data is None:
        return False
    
    if timer_data.state == 0:
        logging.info("queue_id가 %s이고, 10분 접속 중인 %s번 컴퓨터가 있습니다", timer_data.queue_id, timer_data.pc_num)
        # 현재 시간 가져오기 (현지 시간)
        now_time = datetime.now()  # 서버의 현지 시간으로 설정
        start_time = timer_data.start_time
        
        # 시간 차이 계산
        time_diff = (now_time - start_time).total_seconds()

        # 10분(600초)이 지났는지 확인
        if time_diff > 60:  # 실제 운영 시 600으로 설정
            await exit_game(db, timer_data.pc_num, template)
            await tenMinTimerDao.update_end_time_and_state(db, queue_id, pc_num, now_time, 1)
            await remoteDao.update_remote_pc_process_by_worker_id(db, worker_id, 'idle')
            return True
        else:
            return False
    return False

async def exit_game(db: AsyncSession, pc_num: int, img_template):
    await openRemote.runOpenRemote(pc_num)

    done = False
    while not done:
        screen = screen_capture()
        top_left, bottom_right, _ = detect_template(screen, img_template, 0.8)

        if top_left and bottom_right:
            await press_exit_key()
            time.sleep(5)
            await press_tilde_key()
            done = True
        time.sleep(1)
