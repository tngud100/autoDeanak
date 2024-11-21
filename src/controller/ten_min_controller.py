import logging
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import socket

from dependencies import get_db, get_db_context
from fastapi import APIRouter, Depends
from src.dao.deanak_dao import deanakDao
from src.service.logic.utils.error import handle_error, task_exception_handler
from src.service.req import set_data_form
from src.service.remote import openRemote
from src.service.ten_min import ten_min
from src.service.logic.utils.finish_10_min_service import check_pass_10min
from src.entity.service_queue_entity import serviceQueue
from src.dao.remote_pcs_dao import remoteDao
from src.dao.service_queue_dao import serviceQueueDao

router = APIRouter(
    prefix="/api/ten_min",
    tags=["auto_deanak"]
)

service = '10분접속'

# @router.get("/run")
async def run_deanak(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    async with lock:
        if is_running:
            return JSONResponse(status_code=400, content={"message": "Deanak is already running"})
        is_running = True

    # auto deanak 프로세스 시작
    running_task = asyncio.create_task(run_auto_deanak())

    return JSONResponse(status_code=200, content={"message": "10min started"})

@router.get("/stop")
async def stop_deanak(db: AsyncSession = Depends(get_db)) -> JSONResponse:
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

  return JSONResponse(status_code=200, content={"message": "10min stopped"})

async def run_auto_deanak():
  global is_running
  try:
    while is_running:
      async with get_db_context() as db:
        await check_pass_10min(db)

        get_queue = await serviceQueueDao.find_service_queue_by_state_and_service(db, 0, service)
        if get_queue:
            logging.info("10min data found")
            await set_data_form.set_remote_pcs(db, get_queue)
            await auto_deanak(get_queue)
            await asyncio.sleep(2)
        else:
            logging.info("keep watching queue")
            await asyncio.sleep(10)
  except Exception as e:
    handle_error(e, "run_auto_deanak에서 예상치 못한 오류 발생", critical=True)
    is_running = False
  finally:
    is_running = False

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
        await ten_min(db, info)