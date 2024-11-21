from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from src.entity.autoDeanak_entity import Deanak
from src.entity.remote_pcs_entity import RemotePC
from src.entity.service_queue_entity import serviceQueue

class serviceQueueDao:
    @staticmethod
    async def find_service_queue_by_state_and_service(db: AsyncSession, state: int, service: str, ip: str):
        # 비동기 쿼리 수행
        result = await db.execute(
            select(serviceQueue).filter(serviceQueue.state == state).order_by(serviceQueue.priority, serviceQueue.apply_time)
        )
        result_list = list(result.scalars())

        for queue in result_list:
            deanak = await db.execute(select(Deanak).filter(Deanak.id == queue.deanak_id))
            if deanak.scalars().first().service != service:
                continue
            
            worker_id = await db.execute(select(RemotePC.worker_id).filter(RemotePC.ip == ip).filter(RemotePC.worker_id == queue.worker_id))
            if worker_id:
                return queue
            else: None

    @staticmethod
    async def find_service_queue_by_state(db: AsyncSession, state: int):
        # 비동기 쿼리 수행
        result = await db.execute(
            select(serviceQueue).filter(serviceQueue.state == state).order_by(serviceQueue.priority, serviceQueue.apply_time)
        )
        return result.scalars().first()
            
    @staticmethod
    async def find_service_queue_by_deanak_id(db: AsyncSession, deanak_id: int):
        # 비동기 쿼리 수행
        result = await db.execute(
            select(serviceQueue).filter(serviceQueue.deanak_id == deanak_id)
        )
        return result.scalars()

    @staticmethod
    async def update_queue_state(db: AsyncSession, deanak_id: int, worker_id: int, state: str):
        # 비동기 업데이트 쿼리 수행
        await db.execute(
            update(serviceQueue)
            .where((serviceQueue.deanak_id == deanak_id) & (serviceQueue.worker_id == worker_id))
            .values(state=state)
        )
        await db.commit()

    @staticmethod
    async def update_queue_process(db: AsyncSession, deanak_id: int, worker_id: int, process: str):
        # 비동기 업데이트 쿼리 수행
        await db.execute(
            update(serviceQueue)
            .where((serviceQueue.deanak_id == deanak_id) & (serviceQueue.worker_id == worker_id))
            .values(process=process)
        )
        await db.commit()

    @staticmethod
    async def update_start_time(db: AsyncSession, deanak_id: int, worker_id: int, start_time: str):
        # 비동기 업데이트 쿼리 수행
        await db.execute(
            update(serviceQueue)
            .where((serviceQueue.deanak_id == deanak_id) & (serviceQueue.worker_id == worker_id))
            .values(start_time=start_time)
        )
        await db.commit()

    @staticmethod
    async def update_end_time(db: AsyncSession, deanak_id: int, worker_id: int, end_time: str):
        # 비동기 업데이트 쿼리 수행
        await db.execute(
            update(serviceQueue)
            .where((serviceQueue.deanak_id == deanak_id) & (serviceQueue.worker_id == worker_id))
            .values(end_time=end_time)
        )
        await db.commit()

    @staticmethod
    async def error_update(db: AsyncSession, deanak_id: int, worker_id: int, error: str):
        # 비동기 업데이트 쿼리 수행
        await db.execute(
            update(serviceQueue)
            .where((serviceQueue.deanak_id == deanak_id) & (serviceQueue.worker_id == worker_id))
            .values(error=error, state=-1)
        )
        await db.commit()