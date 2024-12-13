import asyncio
import json
import os
import uuid
from dependencies import AsyncSessionLocal
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import UpdateRowsEvent
from src.dao.remote_pcs_dao import remoteDao
from src.controller.deanak_controller import do_task
from src.service.logic.utils.error import handle_error

deanak_running_task = None
deanak_is_running = False
deanak_service = '일반대낙'
ten_min_running_task = None
ten_min_is_running = False
ten_min_service = '10분접속'
lock = asyncio.Lock()
otp_is_running = False

main_loop = False
ten_min_loop = False

monitoring_task = None

class unique_id:
  def __init__(self):
    self.path = 'unique_id.json'
    self.server_is_running = False
    self.server_id = None

  async def read_unique_id(self):
      try:
        if os.path.exists(self.path):
          with open(self.path, 'r') as f:
            server_id_json = json.load(f)
            uuid_id = server_id_json["server_id"]
            return uuid_id
      except:
          pass

  async def generate_unique_id(self):
    try:
      self.server_is_running = True
      if not os.path.exists(self.path):
        with open(self.path, 'w') as f:
          uuid_id = str(uuid.uuid4())
          server_id_json = {"server_id": uuid_id}
          json.dump(server_id_json, f)
          self.server_id = uuid_id

          return uuid_id
    except:
      pass

  async def delete_unique_id(self):
      try:
        self.server_is_running = False
        if os.path.exists(self.path):
          with open(self.path, 'r') as f:
            server_id_json = json.load(f)
            uuid_id = server_id_json["server_id"]
            return uuid_id
      except:
        pass
      finally:
        os.remove(self.path)

  async def check_remote_state(self):
    try:
      while self.server_is_running:
        async with AsyncSessionLocal() as db:
          server_id = await self.read_unique_id()
          tasks = await remoteDao.get_pending_tasks(db, server_id)
          print(f"request : {tasks}")
          await do_task(tasks)
          
        await asyncio.sleep(10)

    except asyncio.CancelledError:
      print("Polling task cancelled")
    except Exception as e:
      print(f"Error in check_remote_state: {e}")
      handle_error(e, "Error in check_remote_state", critical=True)


# Background Task: Binlog 이벤트 감지
# Binlog 이벤트 감지 함수 request요청 모니터링# Binlog 이벤트 감지 (비동기 처리)
async def monitor_binlog(server_id: str):
  mysql_settings = {
    "host": "121.175.15.136",
    "port": 3306,
    "user": "gameins",
    "passwd": "0000"
  }

  stream = BinLogStreamReader(
    connection_settings=mysql_settings,
    server_id=1,
    blocking=True,
    resume_stream=True,
    only_events=[UpdateRowsEvent],
    only_tables=["remote_pcs"],
    only_schemas=["ez_daenak"]
  )

  try:
    while True:
      # 동기 작업을 비동기 스레드로 실행
      binlogevent = await asyncio.to_thread(stream.fetchone)
      if binlogevent is None:
        continue

      for row in binlogevent.rows:
        before_values = row["before_values"]
        after_values = row["after_values"]

        if after_values["server_id"] != server_id:
          continue

        # request 변경 감지 
        if before_values["request"] != after_values["request"]:
          print("Column changed!")
          print("request:", after_values["request"])
          if after_values["request"] == "otp_check":
            asyncio.create_task(do_task(after_values["request"], after_values["worker_id"]))
          else: asyncio.create_task(do_task(after_values["request"]))

  except Exception as e:
      print(f"Error in BinLogStreamReader: {e}")
      await asyncio.sleep(5)  # 오류 발생 시 5초 대기 후 재시도
      
  finally:
    stream.close()
    print("BinLogStreamReader closed.")