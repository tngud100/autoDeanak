import logging
import socket
from fastapi.responses import JSONResponse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from fastapi import APIRouter, Depends
from dependencies import get_db, get_db_context

from src.dao.remote_pcs_dao import remoteDao, remoteWorkerPCDao
from src.service.ten_min import ten_min
from src.service.logic.utils.finish_10_min_service import check_pass_10min
from src.dao.deanak_dao import deanakDao
from src.service.deanak import deanak
from src.service.logic.utils.error import handle_error, task_exception_handler
from src.service.req import set_data_form
from src.service.remote import openRemote
from src.entity.service_queue_entity import serviceQueue
from src.dao.service_queue_dao import serviceQueueDao
from src import state

router = APIRouter(
    prefix="/api",
    tags=["auto_deanak"]
)


@router.get("/deanak/run")
async def run_deanak(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    async with state.lock:
        if state.deanak_is_running:
            return JSONResponse(status_code=400, content={"message": "Deanak is already running"})
        state.deanak_is_running = True

    # 현재 IP 가져오기 (httpx 사용)
    async with httpx.AsyncClient() as client:
        response = await client.get("https://checkip.amazonaws.com/")
    current_ip = response.text.strip()  # IP 응답에서 공백 제거

    await remoteDao.insert_remote_pc(db, 'idle', current_ip)

    # auto deanak 프로세스 시작
    state.deanak_running_task = asyncio.create_task(run_auto_deanak(current_ip))

    return JSONResponse(status_code=200, content={"message": "Deanak started"})

@router.get("/deanak/stop")
async def stop_deanak(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    async with state.lock:
        if not state.deanak_is_running:
            return JSONResponse(status_code=400, content={"message": "Deanak is not running"})
        state.deanak_is_running = False

    # 실행 중인 작업을 대기하거나 취소
    if state.deanak_running_task and not state.deanak_running_task.done():
        state.deanak_running_task.cancel()
        # ip가져와서 remote_PC 컬럼 삭제
        await openRemote.delete_remote_pc(db)
        try:
            await state.deanak_running_task
        except asyncio.CancelledError:
            logging.info("Running task was cancelled.")

    return JSONResponse(status_code=200, content={"message": "Deanak stopped"})

@router.get("/ten_min/run")
async def run_ten_min(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    async with state.lock:
        if state.ten_min_is_running:
            return JSONResponse(status_code=400, content={"message": "ten_min is already running"})
        state.ten_min_is_running = True

    # 현재 IP 가져오기 (httpx 사용)
    async with httpx.AsyncClient() as client:
        response = await client.get("https://checkip.amazonaws.com/")
    current_ip = response.text.strip()  # IP 응답에서 공백 제거

    for i in range(0,5):
      await remoteDao.insert_remote_pc(db, 'idle', current_ip)

    # auto deanak 프로세스 시작
    state.ten_min_running_task = asyncio.create_task(run_auto_ten_min(current_ip))

    return JSONResponse(status_code=200, content={"message": "ten_min started"})

@router.get("/ten_min/stop")
async def stop_ten_min(db: AsyncSession = Depends(get_db)) -> JSONResponse:
    async with state.lock:
        if not state.ten_min_is_running:
            return JSONResponse(status_code=400, content={"message": "ten_min is not running"})
        state.ten_min_is_running = False


    # 실행 중인 작업을 대기하거나 취소
    if state.ten_min_running_task and not state.ten_min_running_task.done():
        state.ten_min_running_task.cancel()
        # ip가져와서 remote_PC 컬럼 삭제
        await openRemote.delete_remote_pc(db)
        try:
            await state.ten_min_running_task
        except asyncio.CancelledError:
            logging.info("Running task was cancelled.")

    return JSONResponse(status_code=200, content={"message": "ten_min stopped"})

async def run_auto_deanak(ip: str):
  try:
    while state.deanak_is_running:
      async with get_db_context() as db:
        remote_pcs = await remoteDao.find_remote_pc_worker_id_by_ip(db, ip, state.deanak_service)
        if not remote_pcs:
          logging.info("server needs child PCs")
          await asyncio.sleep(10)
          continue

        get_queue = await serviceQueueDao.find_service_queue_by_state_and_service(db, 0, state.deanak_service, ip)
        if get_queue:
          logging.info("Deanak data found")
          await set_data_form.set_remote_pcs(db, get_queue)
          await auto_service(get_queue)
          await asyncio.sleep(2)
          # auto_deanak 작업을 시작하고 대기하지 않음
          # task = asyncio.create_task(auto_deanak(get_queue))
          # # 태스크를 백그라운드에서 실행하고, 예외 처리를 위해 콜백 추가
          # task.add_done_callback(task_exception_handler)
        else:
          logging.info("keep watching queue")
          await asyncio.sleep(10)

  except Exception as e:
    handle_error(e, "run_auto_deanak에서 예상치 못한 오류 발생", critical=True)
    state.deanak_is_running = False
  finally:
    state.deanak_is_running = False

async def run_auto_ten_min(ip: str):
  try:
    while state.ten_min_is_running:
      async with get_db_context() as db:
        await check_pass_10min(db)

        remote_pcs = await remoteDao.find_remote_pc_worker_id_by_ip(db, ip, state.deanak_service)
        if not remote_pcs:
          logging.info("server needs child PCs")
          await asyncio.sleep(10)
          continue

        get_queue = await serviceQueueDao.find_service_queue_by_state_and_service(db, 0, state.ten_min_service, ip)
        if get_queue:
            logging.info("10min_queue data found")
            await set_data_form.set_remote_pcs(db, get_queue)
            await auto_service(get_queue)
            await asyncio.sleep(2)
        else:
          logging.info("keep watching 10_min_queue")
          await asyncio.sleep(10)

  except Exception as e:
    handle_error(e, "run_auto_ten_min에서 예상치 못한 오류 발생", critical=True)
    state.ten_min_is_running = False
  finally:
    state.ten_min_is_running = False

async def auto_service(service_queue_data: serviceQueue):
   async with get_db_context() as db:
      deanak_data= await openRemote.check_running_PC(db, service_queue_data)
      if deanak_data is None:
        logging.warning("Deanak data or remote PCs data not found")
        return

      # topClass = deanak_data.topclass == 1
      # info["topClass"]: topClass,

      pc_num = await remoteWorkerPCDao.find_worker_pc_num_by_worker_id(db, service_queue_data.worker_id)

      info = {  
        "service": deanak_data.service,
        "password": deanak_data.pw2,
        "pc_num": pc_num,
        "deanak_id": service_queue_data.deanak_id,
        "worker_id": service_queue_data.worker_id,
        "queue_id": service_queue_data.queue_id
      }

      await openRemote.runOpenRemote(pc_num)

      if deanak_data.service == state.deanak_service:
        await deanak(info)
      elif deanak_data.service == state.ten_min_service:
        await ten_min(info)
