from typing import Optional
from pydantic import BaseModel

# 데이터베이스 모델 정의 (deanak 테이블)
class DeanakResponse(BaseModel):
  service: str
  game_id: str
  pw2: str
  worker_id: str
  topclass: Optional[int] = 0
  state: Optional[int] = 2

  class Config:
    from_attributes=True
