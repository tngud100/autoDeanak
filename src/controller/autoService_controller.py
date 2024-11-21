import logging
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import socket

from dependencies import get_db, get_db_context
from fastapi import APIRouter, Depends
from src.service.logic.utils.error import handle_error
from src.service.req import set_data_form
from src.service.remote import openRemote
from src.service.main import main
from src.service.logic.utils.finish_10_min_service import check_pass_10min
from src.entity.service_queue_entity import serviceQueue
from src.dao.remote_pcs_dao import remoteDao
from src.dao.service_queue_dao import serviceQueueDao

router = APIRouter(
    prefix="/api/service",
    tags=["auto_deanak"]
)

running_task = None
is_running = False
lock = asyncio.Lock()

@router.get("/run")
async def run_deanak(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    global is_running, running_task
    async with lock:
        if is_running:
            return JSONResponse(status_code=400, content={"message": "Deanak is already running"})
        is_running = True

    # 현재 IP 가져오기
    hostname = socket.gethostname()
    current_ip = socket.gethostbyname(hostname)
    # await remoteDao.update_remote_pc_state_by_worker_id(db, 'main', 'running', current_ip)

    # auto deanak 프로세스 시작
    running_task = asyncio.create_task(run_auto_deanak())

    return JSONResponse(status_code=200, content={"message": "Deanak started"})


@router.get("/stop")
async def stop_deanak(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    global is_running, running_task
    async with lock:
        if not is_running:
            return JSONResponse(status_code=400, content={"message": "Deanak is not running"})
        is_running = False

    # 실행 중인 작업을 대기하거나 취소
    if running_task and not running_task.done():
        running_task.cancel()
        try:
            await running_task
        except asyncio.CancelledError:
            logging.info("Running task was cancelled.")
        except Exception as e:
            handle_error(e, "Error occurred while stopping the task", critical=True)

    # 원격 PC의 상태 업데이트
    # await remoteDao.update_remote_pc_state_by_worker_id(db, 'main', 'stopped')

    return JSONResponse(status_code=200, content={"message": "Deanak has been stopped"})

async def run_auto_deanak():
    global is_running
    while is_running:
        async with get_db_context() as db:
            await db.commit()
            await check_pass_10min(db)

            get_queue = await serviceQueueDao.find_service_queue_by_state(db, 0)
            logging.info("get_queue: %s", get_queue)

            if get_queue:
                await set_data_form.set_remote_pcs(db, get_queue)
                # auto_deanak 작업을 시작하고 대기하지 않음
                task = asyncio.create_task(auto_deanak(get_queue))
                try:
                    await task
                except Exception as e:
                    handle_error(e, "Error occurred in auto_deanak", critical=True)
            else:
                logging.info("keep watching queue")
                await asyncio.sleep(10)

async def auto_deanak(service_queue_data: serviceQueue):
   async with get_db_context() as db:
        deanak_data, pcs_data = await openRemote.check_running_PC(db, service_queue_data)
        if deanak_data is None:
            logging.warning("Deanak data not found")
            return

        topClass = deanak_data.topclass == 1

        info = {
            "service": deanak_data.service,
            "password": deanak_data.pw2,
            "topClass": topClass,
            "pc_num": deanak_data.pc_num,
            "deanak_id": service_queue_data.deanak_id,
            "worker_id": service_queue_data.worker_id,
            "queue_id": service_queue_data.queue_id
        }
        pc_num = pcs_data.pc_num

        await openRemote.runOpenRemote(db, pc_num)
        await main(db, info)