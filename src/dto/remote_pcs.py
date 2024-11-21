from pydantic import BaseModel

# 데이터베이스 모델 정의 (deanak 테이블)
class RemoteResponse(BaseModel):
  idx: int
  pc_num: int
  worker_id: str
  service: str
  ip: str
  state: str = "idle"

  class Config:
    from_attributes=True
