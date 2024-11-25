import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update
from src.entity.remote_pcs_entity import RemotePC
from src.entity.worker_pc_entity import WorkerPC

class remoteDao:
    @staticmethod
    async def insert_remote_pc_server_id(db: AsyncSession, server_id: str):
        new_data = RemotePC(server_id=server_id, request='None')
        db.add(new_data)
        await db.commit()
        
    @staticmethod
    async def delete_remote_pc_by_server_id(db: AsyncSession, server_id: str):
        # 비동기 쿼리 작성
        await db.execute(
            delete(RemotePC)
            .where(RemotePC.server_id == server_id)
        )
        await db.commit()

    @staticmethod
    async def choose_remote_pc_service(db: AsyncSession, server_id: str, service: str):
        await db.execute(
            update(RemotePC)
            .where(RemotePC.server_id == server_id)
            .values(service=service)
        )
        await db.commit()

    @staticmethod
    async def get_pending_tasks(db: AsyncSession, server_id: str):
        result = await db.execute(
            select(RemotePC.request)
            .filter(RemotePC.server_id == server_id)
        )
        return result.scalars().first()

    @staticmethod
    async def update_tasks_request(db: AsyncSession, server_id: str, request: str):
        await db.execute(
            update(RemotePC)
            .where(RemotePC.server_id == server_id)
            .values(request=request)
        )
        await db.commit()

    @staticmethod
    async def update_remote_pc_process_by_server_id(db: AsyncSession, server_id: str, process: str):
        # 비동기 쿼리 작성
        await db.execute(
            update(RemotePC)
            .where(RemotePC.server_id == server_id)
            .values(process=process)
        )
        await db.commit()    

    @staticmethod
    async def join_remote_pc_by_server_id(db: AsyncSession, server_id: str, worker_id: str):
        # 비동기 쿼리 작성
        service = await remoteWorkerPCDao.find_worker_serive_by_worker_id(db, worker_id)

        if service == '일반대낙':
            await db.execute(
                update(RemotePC)
                .where(RemotePC.server_id == server_id, RemotePC.worker_id.is_(None))
                .values(worker_id=worker_id)
            )
            await db.commit()
            return True

        # 10분접속 일때 원격 피씨 worker_id가 없는 행을 찾아서 업데이트
        if service == '10분접속':
            blank_remote_row = await db.execute(
                select(RemotePC)
                .where(RemotePC.server_id == server_id, RemotePC.worker_id.is_(None))
                .limit(1)
            )
            row_to_update = blank_remote_row.scalar_one_or_none()
            
            if row_to_update:
                await db.execute(
                    update(RemotePC)
                    .where(RemotePC.idx == row_to_update.idx)  # 특정 행에 대해서만 업데이트
                    .values(worker_id=worker_id)
                )
                await db.commit()
                return True
            
            return False
        
    
    @staticmethod
    async def insert_remote_pc_ip(db: AsyncSession, server_id: str, process: str, ip: str = None):
        await db.execute(
            update(RemotePC)
            .where(RemotePC.server_id == server_id)
            .values(ip=ip, process=process)
        )
        
        await db.commit()
        
    @staticmethod
    async def find_service_by_server_id(db: AsyncSession, server_id: str):
        result = await db.execute(
            select(RemotePC.service)
            .filter(RemotePC.server_id == server_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_remote_pc_list(db: AsyncSession):
        # 비동기 데이터 조회
        result = await db.execute(
            select(RemotePC)
        )
        return result.scalars().all()

    @staticmethod
    async def find_remote_pc_worker_id_by_ip(db: AsyncSession, ip: str, service: str):
        # 비동기 데이터 조회
        result = await db.execute(
            select(RemotePC.worker_id).filter(RemotePC.ip == ip)
        )
        if service == '일반대낙':
            return result.scalars().first()
        if service == '10분접속':
            return result.scalars().all()

    @staticmethod
    async def find_remote_pc_process_by_worker_id(db: AsyncSession, worker_id: str):
        # 비동기 데이터 조회
        result = await db.execute(
            select(RemotePC.process).filter(RemotePC.worker_id == worker_id)
        )
        return result.scalars().first()
    
    @staticmethod
    async def find_remote_pc_by_worker_id_and_ip(db: AsyncSession, worker_id: str, ip: str):
        result = await db.execute(
            select(RemotePC)
            .filter(RemotePC.ip == ip)
            .filter(RemotePC.worker_id == worker_id))
        return result.scalars().first()
    
    @staticmethod
    async def update_remote_pc_process_by_worker_id(db: AsyncSession, worker_id: str, process: str):
        # 비동기 쿼리 작성
        await db.execute(
            update(RemotePC)
            .where(RemotePC.worker_id == worker_id)
            .values(process=process)
        )
        await db.commit()

    @staticmethod
    async def find_waiting_remote_pc(db: AsyncSession):
        # 비동기 데이터 조회
        result = await db.execute(
            select(RemotePC).filter(RemotePC.state != 'waiting')
        )
        return result.scalars().all()
    
    @staticmethod
    async def idle_pc_count(db: AsyncSession):
        # 비동기 데이터 조회
        result = await db.execute(
            select(RemotePC).filter(RemotePC.state == 'idle')
        )
        return len(result.scalars().all())
    
class remoteWorkerPCDao:
    @staticmethod
    async def find_worker_pc_num_by_worker_id(db: AsyncSession, worker_id: str):
        # 비동기 데이터 조회
        result = await db.execute(
            select(WorkerPC.pc_num).filter(WorkerPC.worker_id == worker_id)
        )
        return result.scalars().first()
    
    @staticmethod
    async def find_worker_serive_by_worker_id(db: AsyncSession, worker_id: str):
        # 비동기 데이터 조회
        result = await db.execute(
            select(WorkerPC.service).filter(WorkerPC.worker_id == worker_id)
        )
        return result.scalars().first()