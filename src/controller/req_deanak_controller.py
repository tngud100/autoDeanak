import logging
from typing import Dict, List
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from dependencies import get_db
from fastapi import APIRouter, Depends, HTTPException, Request
from src.dao.remote_pcs_dao import remoteDao
from src.dto.remote_pcs import RemoteResponse
from src.entity.service_queue_entity import serviceQueue
from src.service.logic.utils.error import handle_error
from src.service.otp import check_otp_number
from src.service.req import set_data_form
from src.dao.deanak_dao import deanakDao
from src.dto.deanak import DeanakResponse

router = APIRouter(
    prefix="/api",
    tags=["auto_deanak"]
)

# 대낙 요청시 - 서비스 큐에 추가
@router.get("/req/{deanak_id}")
async def req_deanak_form(deanak_id: int, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    try:
        # 비동기적으로 Deanak 데이터 조회
        deanak_data = await deanakDao.find_deanak_data(db, deanak_id)
        if deanak_data is None:
            return JSONResponse(status_code=404, content={"message": "Deanak data not found"})
        
        # 비동기적으로 서비스 큐 설정
        await set_data_form.set_service_queue(db, deanak_data)
        logging.info("Deanak data added to service queue")

        return JSONResponse(status_code=200, content={"message": "Success"})
    except Exception as e:
        logging.error("Error occurred while requesting deanak form: %s", e)
        return JSONResponse(status_code=500, content={"message": "Internal server error"})

# 서비스 큐 조회
@router.get("/get/queue")
async def get_queue_form(db: AsyncSession = Depends(get_db)):
    try:
        # SQLAlchemy 모델인 serviceQueue를 사용하여 쿼리 실행
        result = await db.execute(select(serviceQueue))
        service_queue = result.scalars().all()

        if not service_queue:
            raise HTTPException(status_code=200, detail="Service queue is empty")

        return {"message": "Success", "data": service_queue}
    except Exception as e:
        logging.error("Error occurred while getting deanak form: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
    
# 대낙신청
@router.post("/deanak/apply")
async def apply_deanak(formData: DeanakResponse, db: AsyncSession = Depends(get_db))-> JSONResponse:
    try:
        # 비동기적으로 Deanak 데이터 추가
        await deanakDao.add_deanak_data(db, formData)
        return JSONResponse(status_code=200, content={"message": "Success"})
    except Exception as e:
        logging.error("Error occurred while applying deanak: %s", e)
        return JSONResponse(status_code=500, content={"message": "Internal server error"})

# 대낙 리스트 조회
@router.get("/get/deanak")
async def find_deanak_list(db: AsyncSession = Depends(get_db)):
    try:
        # 비동기적으로 Deanak 데이터 조회
        deanak_list = await deanakDao.find_deanak_list(db)
        return {"message": "Success", "data": deanak_list}
    except Exception as e:
        logging.error("Error occurred while getting deanak list: %s", e)
        return JSONResponse(status_code=500, content={"message": "Internal server error"})

# 실행되고 있는 서버 조회    
@router.get("/get/server")
async def find_server_list(db: AsyncSession = Depends(get_db)):
    try:
        # 비동기적으로 remote_pcs 데이터 조회
        remote_pcs = await remoteDao.find_remote_pc_list(db)
        return {"message": "Success", "data": remote_pcs}
    except Exception as e:
        logging.error("Error occurred while getting server list: %s", e)
        return JSONResponse(status_code=500, content={"message": "Internal server error"})
    
# 해당 작업자 아이디 선택한 서버에 참가
@router.post("/join/server")
async def join_server(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        # 요청에서 JSON 데이터 파싱
        data = await request.json()
        worker_id = data.get("worker_id")
        server_id = data.get("server_id")

        # 서비스 신청 여부 확인
        check_service = await remoteDao.find_service_by_server_id(db, server_id)
        if check_service is None:
            return JSONResponse(status_code=404, content={"message": "서비스를 먼저 선택해 주세요."})
        
        # 중복 아이디 유효성 검사
        check_worker_id = await remoteDao.check_duplicate_worker_id(db, server_id, worker_id)
        if check_worker_id:
            return JSONResponse(status_code=404, content={"message": "이미 등록된 아이디 입니다."})

        # worker_id를 서버에 등록(검사 : 아이디의 서비스가 틀림, 아이디가 없음)
        isUpdate = await remoteDao.join_remote_pc_by_server_id(db, server_id, worker_id, check_service)
        if not isUpdate:
            return JSONResponse(status_code=404, content={"message": "존재하지 않는 worker_id이거나 서비스가 일치하지 않습니다."})

        if check_service == '일반대낙':
            # 비동기적으로 일반대낙 서비스 요청
            # await remoteDao.update_tasks_request(db, server_id, 'deanak_start')
            pass
        if check_service == "10분접속":
            # 비동기적으로 10분접속 서비스 요청
            # await remoteDao.update_tasks_request(db, server_id, 'ten_min_start')
            pass

        return JSONResponse(status_code=200, content={"message": "Success"})
    except Exception as e:
        handle_error(e, "대낙 id등록 중 오류 발생", critical=True)
        logging.error("Error occurred while joining server: %s", e)
        return JSONResponse(status_code=500, content={"message": "Internal server error"})
    
@router.post("/choice/service")
async def choice_service(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        data = await request.json()
        service = data.get("service")
        server_id = data.get("server_id")

        check_service = await remoteDao.find_service_by_server_id(db, server_id)
        if check_service is not None:
            return JSONResponse(status_code=404, content={"message": "이미 서비스를 선택하셨습니다."})

        # server_id에 해당하는 row를 복사해서 4개의 row를 추가
        if service == '10분접속':
            await remoteDao.add_ten_min_client(db, server_id)
        
        # remote_pcs 데이터 추가
        await remoteDao.choose_remote_pc_service(db, server_id, service)

        return JSONResponse(status_code=200, content={"message": "Success"})
    except Exception as e:
        logging.error("Error occurred while choice service: %s", e)
        return JSONResponse(status_code=500, content={"message": "Internal server error"})
    
@router.post("/service/run/{server_id}")
async def run_deanak(server_id: str, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    try:
        data = await request.json()
        service = data.get("service")
        if service == '일반대낙':
            state = 'deanak_start'
        elif service == "10분접속":
            state = 'ten_min_start'
            
        await remoteDao.update_tasks_request(db, server_id, state)
        return JSONResponse(status_code=200, content={"message": "Success"})
    except Exception as e:
        logging.error("Error occurred while running deanak: %s", e)
        return JSONResponse(status_code=500, content={"message": "Internal server error"})

@router.post("/service/stop/{server_id}")
async def stop_deanak(server_id: str, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    try:
        data = await request.json()
        service = data.get("service")
        if service == '일반대낙':
            state = 'deanak_stop'
        elif service == "10분접속":
            state = 'ten_min_stop'

        await remoteDao.update_tasks_request(db, server_id, state)
        return JSONResponse(status_code=200, content={"message": "Success"})
    except Exception as e:
        logging.error("Error occurred while stopping deanak: %s", e)
        return JSONResponse(status_code=500, content={"message": "Internal server error"})
    
@router.post("/otp/detect/{server_id}")
async def get_otp_number(server_id: str, request:Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    try:
        request = await request.json()
        worker_id = request.get("worker_id")


        if worker_id is None:
            return JSONResponse(status_code=404, content={"message": "Worker ID not found"})
        
        worker_id = await remoteDao.find_worker_id_by_server_id(db, server_id, worker_id)
        if worker_id is None:
            return JSONResponse(status_code=404, content={"message": "Worker ID not found"})

        # OTP 번호 확인
        await remoteDao.update_tasks_request(db, server_id, "otp_check")
        # otp_number = await check_otp_number(info)
        # OTP 번호가 일치하면 성공
        return JSONResponse(status_code=200, content={"message": "you got otp number!"})
    except Exception as e:
        handle_error(e, "OTP 번호 확인 중 오류 발생", critical=True)
        logging.error("Error occurred while checking OTP number: %s", e)
        return JSONResponse(status_code=500, content={"message": "Internal server error"})