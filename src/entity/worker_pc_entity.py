from sqlalchemy import Column, Integer, String
from dependencies import Base

# 데이터베이스 모델 정의 (deanak 테이블)
class WorkerPC(Base):
    __tablename__ = "remote_worker_pc"

    pc_num = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String(45), primary_key=True, index=True)
    service = Column(String(45), index=True)