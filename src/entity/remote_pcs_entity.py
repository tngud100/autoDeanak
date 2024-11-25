from sqlalchemy import Column, Index, Integer, String
from dependencies import Base

# 데이터베이스 모델 정의 (deanak 테이블)
class RemotePC(Base):
    __tablename__ = "remote_pcs"

    idx = Column(Integer, primary_key=True, index=True)
    server_id = Column(String(100), unique=True, index=True)
    ip = Column(String(45))
    request = Column(String(45), index=True)
    service = Column(String(45))
    worker_id = Column(String(45))
    process = Column(String(45))

    # 복합 인덱스 정의
    __table_args__ = (
        Index("ix_remotepcs_serverid_request", "server_id", "request"),  # 복합 인덱스
    )