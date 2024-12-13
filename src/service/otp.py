import asyncio
from dependencies import get_db_context
from src import state
from src.dao.deanak_dao import deanakDao
from src.dao.remote_pcs_dao import remoteDao, remoteWorkerPCDao
from src.service.logic.utils.capture import screen_capture
from src.service.logic.utils.error import handle_error
from src.service.logic.utils.image_processing import check_and_load_text_template, detect_template, read_text_from_image
from src.service.logic.utils.keyboard_mouse import exit_main_loop, press_tilde_key
from src.service.remote import openRemote


async def check_otp_number(worker_id: str):
  try:
    async with get_db_context() as db:
      if worker_id == None:
        raise Exception("할당된 worker_id가 존재하지 않습니다.")
      
      server_id = await state.unique_id().read_unique_id()

      check_worker_ids = await remoteDao.find_worker_id_by_server_id(db, server_id, worker_id)
      service = await remoteWorkerPCDao.find_worker_service_by_worker_id(db, worker_id)
      print(check_worker_ids, service)

      existed_worker_ids = [worker_id == worker for worker in check_worker_ids]
      if not existed_worker_ids:
        raise Exception("해당 worker_id가 worker_list에 존재하지 않습니다.")

      deanak_list = await deanakDao.find_deanak_list_by_worker_id(db, worker_id)
      pc_num = await remoteWorkerPCDao.find_worker_pc_num_by_worker_id(db, worker_id)
      if deanak_list == None:
        raise Exception("대낙 리스트가 존재하지 않습니다.")
      
      print(deanak_list)

      state.otp_is_running = True
      opt_template_paths = {
        "opt_frame": 'static/image/otpFrame.PNG',
        "otp_number": 'static/image/otpNumber.PNG',
      }
      templates = {
        key: check_and_load_text_template(path)
        for key, path in opt_template_paths.items()
      }
      try:
        await openRemote.runOpenRemote(pc_num)
      except Exception as e:
        handle_error(e, "원격 데스크탑 활성화 중 오류 발생", True)

      await detect_otp_number(templates, deanak_list.id) # deanak_id를 어떻게 가져올
      await remoteDao.update_tasks_request(db, server_id, "None")
      
  except Exception as e:
    state.otp_is_running = False
    await remoteDao.update_tasks_request(db, server_id, "None")
    handle_error(e, "OTP 화면에서 오류 발생", True)

async def detect_otp_number(templates, deanak_id):
  async with get_db_context() as db:
    count = 0
    while state.otp_is_running:
      try:
        count += 1
        if count > 5:
          raise Exception("OTP 화면을 찾을 수 없습니다.")
        # 화면 캡처 수행
        screen = screen_capture()
        print("감지시작")
        top_left, bottom_right, _ = detect_template(screen, templates["opt_frame"], 0.8)
        # OTP 화면 탐지 및 처리
        if top_left or bottom_right:
          print("첫번째 이미지 감지 완료")
          roi = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
          text = await read_text_from_image(screen, templates["otp_number"], 0.6, roi=roi)
          await press_tilde_key()
          await deanakDao.update_otp_number(db, deanak_id, text)
          state.otp_is_running = False
          

        await asyncio.sleep(3)
        

      except Exception as e:
        handle_error(e, "OTP 화면 탐지 중 오류 발생", True)
        state.otp_is_running = False