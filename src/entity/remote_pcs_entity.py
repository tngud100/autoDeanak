from sqlalchemy import Column, Integer, String
from dependencies import Base

# 데이터베이스 모델 정의 (deanak 테이블)
class RemotePC(Base):
    __tablename__ = "remote_pcs"

    idx = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String(45), index=True)
    ip = Column(String(45), index=True)
    state = Column(String(45), index=True)