from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from src.entity.autoDeanak_entity import Deanak
from src.entity.remote_pcs_entity import RemotePC
from src.entity.service_queue_entity import serviceQueue
from src import state as __state__

class serviceQueueDao:
    @staticmethod
    async def find_service_queue_by_state_and_service(db: AsyncSession, state: int):
        # 비동기 쿼리 수행
        result = await db.execute(
            select(serviceQueue).filter(serviceQueue.state == state).order_by(serviceQueue.priority, serviceQueue.apply_time)
        )
        result_list = list(result.scalars())
        server_id = await __state__.unique_id().read_unique_id()

        for queue in result_list:
            # 대낙 번호가 같은 queue테이블 데이터 조회(같은 서비스인지 확인)
            deanak = await db.execute(select(Deanak).filter(Deanak.id == queue.deanak_id))
            if deanak.scalars().first() is None:
                continue
            
            # 해당 큐의 worker_id를 통해 RemotePC 테이블에서 server_id 조회
            queue_server_id = await db.execute(select(RemotePC.server_id).filter(RemotePC.worker_id == queue.worker_id))
            if queue_server_id.scalars().first() == server_id:
                return queue

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