from sqlalchemy import Column, Integer, String
from dependencies import Base

# 데이터베이스 모델 정의 (deanak 테이블)
class Deanak(Base):
    __tablename__ = "deanak"

    id = Column(Integer, primary_key=True, index=True)
    service = Column(String(45), index=True)
    game_id = Column(String(45), index=True)
    pw2 = Column(String(10), index=True)
    topclass = Column(Integer, index=True)
    worker_id = Column(String(45), index=True)
    state = Column(Integer, index=True)