from sqlalchemy import Column, ForeignKey, Integer, DateTime
from dependencies import Base

# 데이터베이스 모델 정의 (deanak 테이블)
class timer(Base):
    __tablename__ = "ten_min_timer"

    queue_id = Column(Integer, ForeignKey('service_queue_entity.queue_id'), primary_key=True, index=True)
    pc_num = Column(Integer, ForeignKey('remote_pcs_entity.pc_num'), primary_key=True, index=True)
    state = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
