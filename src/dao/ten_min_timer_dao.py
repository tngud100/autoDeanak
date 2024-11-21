from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, insert
from src.entity.timer_entity import timer

class tenMinTimerDao:
  @staticmethod
  async def insert_timer(db: AsyncSession, queue_id: int, pc_num: int):
    # 비동기 데이터 삽입
    await db.execute(
      insert(timer)
      .values(queue_id=queue_id, pc_num=pc_num)
    )
    await db.commit()

  @staticmethod
  async def find_timer_by_queue_id_and_pc_num(db: AsyncSession, queue_id: int, pc_num: int):
    # 비동기 데이터 조회
    result = await db.execute(
      select(timer).filter(timer.queue_id == queue_id).filter(timer.pc_num == pc_num)
    )
    return result.scalars().first()
  
  @staticmethod
  async def update_end_time_and_state(db: AsyncSession, queue_id: int, pc_num: int, end_time: str, state: int):
    # 비동기 업데이트 쿼리 수행
    await db.execute(
      update(timer)
      .where((timer.queue_id == queue_id) & (timer.pc_num == pc_num))
      .values(end_time=end_time, state=state)
    )
    await db.commit()