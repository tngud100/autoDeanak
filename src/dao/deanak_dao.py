from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from src.dto.deanak import DeanakResponse
from src.entity.service_queue_entity import serviceQueue
from src.entity.autoDeanak_entity import Deanak

class deanakDao:
    @staticmethod
    async def find_deanak_data(db: AsyncSession, deanak_id: int):
        # 비동기 데이터 조회
        result = await db.execute(
            select(Deanak).filter(Deanak.id == deanak_id)
        )
        return result.scalars().first()
    
    @staticmethod
    async def find_deanak_by_service(db: AsyncSession, state: int, service: str):
        # 비동기 데이터 조회
        result = await db.execute(
            select(Deanak).filter(Deanak.state == state, Deanak.service == service).order_by(Deanak.id)
        )
        return result.scalars().first()
    

    @staticmethod
    async def update_deanak_state(db: AsyncSession, deanak_id: int, state: int):
        # 비동기 상태 업데이트
        await db.execute(
            update(Deanak)
            .where(Deanak.id == deanak_id)
            .values(state=state)
        )
        await db.commit()

    @staticmethod
    async def add_deanak_data(db: AsyncSession, deanak_data: DeanakResponse):
        # 비동기 데이터 추가
        new_record = Deanak(**deanak_data.dict())
        print("new_data: %s", new_record)
        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)
        return new_record
    
    @staticmethod
    async def find_deanak_list(db: AsyncSession):
         # 비동기 데이터 조회
        result = await db.execute(
            select(Deanak)
        )
        return result.scalars().all()