from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# serviceQueue 객체를 직렬화할 pydantic 모델
class ServiceQueueResponse(BaseModel):
    queue_id: int
    deanak_id: int
    worker_id: str
    priority: int
    process: str
    state: int
    apply_time: Optional[datetime]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    error: Optional[str]

    class Config:
        from_attributes=True