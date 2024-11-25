import asyncio
import json
import os
import uuid
from dependencies import AsyncSessionLocal
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

main_loop = False
ten_min_loop = False


class unique_id:
  def __init__(self):
    self.path = 'unique_id.json'
    self.polling_task = None
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
