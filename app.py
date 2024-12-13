import asyncio
import os
import threading
import uuid
import comtypes
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
import httpx
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from dependencies import get_db, AsyncSessionLocal, async_engine

# from src.controller import autoService_controller
from src import state
from src.controller import req_deanak_controller
# from src.controller import deanak_controller
# from src.controller import ten_min_controller
import warnings

from src.controller.deanak_controller import do_task, stop_deanak
from src.dao.remote_pcs_dao import remoteDao

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# FastAPI 애플리케이션 설정
app = FastAPI()

origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# app.include_router(autoService_controller.router)
app.include_router(req_deanak_controller.router)
# app.include_router(deanak_controller.router)
# app.include_router(ten_min_controller.router)


@app.on_event("startup")
async def startup_event():

    unique_id_instance = state.unique_id()
    unique_id_value = await unique_id_instance.generate_unique_id()
    if not unique_id_value:
        unique_id_value = await unique_id_instance.read_unique_id()

    async with AsyncSessionLocal() as db:
        await remoteDao.insert_remote_pc_server_id(db, unique_id_value)

    # 비동기 태스크로 모니터링 실행
    state.monitoring_task = asyncio.create_task(state.monitor_binlog(unique_id_value))
        
    print("server_id: ", unique_id_value)

@app.on_event("shutdown")
async def shutdown_event():
    unique_id_instance = state.unique_id()
    if state.deanak_running_task:
        await stop_deanak()

    # BinLogStreamReader와 관련된 비동기 작업 정리
    # 이미 실행된 모니터링 태스크가 있다면 종료해야 함
    if hasattr(state, 'monitoring_task') and state.monitoring_task:
        state.monitoring_task.cancel()
        try:
            await state.monitoring_task
        except asyncio.CancelledError:
            print("BinLog monitoring task cancelled successfully")

    unique_id_value = await unique_id_instance.delete_unique_id()
    async with AsyncSessionLocal() as db:
        await remoteDao.delete_remote_pc_by_server_id(db, unique_id_value)
        
    print("server_id: ", unique_id_value)
    
    # 비동기 엔진 해제
    # 주석 해제하여 MySQL 연결을 확실히 닫아줌
    await async_engine.dispose()  # aiomysql 연결 닫기

    
if __name__ == '__main__':
    try:
        uvicorn.run(app, host='0.0.0.0', port=8000)
    except KeyboardInterrupt:
        print("Application interrupted. Cleaning up...")
    except asyncio.CancelledError:
        print("Application shutdown requested, cancelling tasks...")
