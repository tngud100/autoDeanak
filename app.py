import asyncio
import os
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

from src.controller.deanak_controller import stop_deanak
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

    print("server_id: ", unique_id_value)
    # 풀링 작업을 비동기 태스크로 실행
    unique_id_instance.polling_task = asyncio.create_task(unique_id_instance.check_remote_state())

@app.on_event("shutdown")
async def shutdown_event():
    unique_id_instance = state.unique_id()
    if state.deanak_running_task:
        await stop_deanak()

    polling_task = unique_id_instance.polling_task
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            print("Polling task cancelled successfully")

    unique_id_value = await unique_id_instance.delete_unique_id()
    async with AsyncSessionLocal() as db:
        await remoteDao.delete_remote_pc_by_server_id(db, unique_id_value)
        await db.close()  # 명시적으로 세션 닫기
        
    print("server_id: ", unique_id_value)

    await async_engine.dispose()  # aiomysql 연결 닫기
    
if __name__ == '__main__':
    try:
        uvicorn.run(app, host='0.0.0.0', port=8000)
    except KeyboardInterrupt:
        print("Application interrupted. Cleaning up...")
