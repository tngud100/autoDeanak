from sqlalchemy import Column, Integer, String, DateTime
from dependencies import Base

# 데이터베이스 모델 정의 (deanak 테이블)
class serviceQueue(Base):
  __tablename__ = "service_queue"

  queue_id = Column(Integer, primary_key=True, index=True)
  deanak_id = Column(Integer, index=True)
  worker_id = Column(String(45), index=True)
  priority = Column(Integer, index=True)
  process = Column(String(45), index=True) # 대기, 2차비밀번호, 공지사항, 팀선택, 메인화면, 이적시장, 상세 이적시장, 판매 리스트, 모두받기, 완료
  state = Column(Integer, index=True)
  apply_time = Column(DateTime, index=True) # 신청 시간
  start_time = Column(DateTime, index=True)
  end_time = Column(DateTime, index=True)
  error = Column(String(45), index=True)
