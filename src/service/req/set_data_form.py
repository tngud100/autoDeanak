from src.entity.autoDeanak_entity import Deanak
from src.entity.service_queue_entity import serviceQueue
from src.entity.remote_pcs_entity import RemotePC
from sqlalchemy.orm import Session
from sqlalchemy import text, update
import logging

from src.dao.remote_pcs_dao import remoteDao, remoteWorkerPCDao
from src.dao.deanak_dao import deanakDao

# Logger 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def set_remote_pcs(db: Session, service_queue_data: serviceQueue):
    # remote_pcs에 deanak_form의 worker_id을 넣어주고 state를 running으로 update
    await db.execute(
        update(RemotePC)
        .where(RemotePC.process == 'idle')
        .where(RemotePC.ip.isnot(None))
        .where(RemotePC.worker_id == service_queue_data.worker_id)
        .values({'process': 'working'})
    )
    await db.commit()

async def set_service_queue(db: Session, deanak_form: Deanak):
    # deanak_form의 state가 2일때 해당 deanak_id와 worker_id, state를 0으로 insert
    # deanak_form의 service가 일반대낙, 10분 접속는 priority가 2
    try:
      print(deanak_form)
      if deanak_form.state == 2:
        priority = 2

        sql = text(
            "INSERT INTO service_queue (deanak_id, worker_id, priority, process, state) VALUES (:deanak_id, :worker_id, :priority, '대기', 0)"
        )
        
        await db.execute(sql, {
            'deanak_id': deanak_form.id,
            'worker_id': deanak_form.worker_id,
            'priority': priority
        })
        await db.commit()
    except Exception as e:
      logger.error("Error occurred while setting service queue: %s", e)
      await db.rollback()

async def rollback_canceled_queue(db: Session, deanak_form: Deanak):
    # deanak_form의 state가 2일때 해당 deanak_id와 worker_id, state를 0으로 insert
    # deanak_form의 service가 일반대낙일때는 priority가 1, 그 외에는 2
    try:
      if deanak_form.state == 2:
        priority = 2 if deanak_form.service == '일반대낙' else 3

        sql = text(
            "INSERT INTO service_queue (deanak_id, worker_id, priority, process, state) VALUES (:deanak_id, :worker_id, :priority, '대기',0)"
        )
        
        await db.execute(sql, {
            'deanak_id': deanak_form.id,
            'worker_id': deanak_form.worker_id,
            'priority': priority
        })
        await db.commit()
    except Exception as e:
      logger.error("Error occurred while setting service queue: %s", e)
      await db.rollback()