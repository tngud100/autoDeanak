from src.service.logic.utils.image_processing import load_templates

def initialize(info: dict):
    # 기본 설정
    service_list = ['일반대낙', '10분접속']
    service = info.get('service', '')
    # topClass = (info.get('topClass') == "True")
    password = info.get('password', '')
    queue_id = info.get('queue_id', None)
    deanak_id = info.get('deanak_id', None)
    worker_id = info.get('worker_id', None)
    pc_num = info.get('pc_num', None)
    password_list = [int(i) for i in password]

    # 탐지 상태 변수 초기화
    detection_states = {
        "anyKey_passed": False,
        "password_passed": False,
        "notice_passed": False,
        "team_select_passed": False,
        "main_screen_passed": False,
        "market_screen_passed": False,
        "get_item_screen_passed": False,
        "arrange_btn_screen": False,
        "finish_get_all_item": False
    }
    detection_count = {
        "anyKey": 0,
        "password": 0,
        "notice": 0,
        "team_select": 0,
        "team_select_text": 0,
        "main_screen": 0,
        "market_btn": 0,
        "market_screen": 0,
        "list_btn": 0,
        "get_item_screen": 0,
        "get_item_btn": 0,
        "arrange_btn": 0,
        "get_all_btn": 0,
        "finish_get_all_item": 0,
    }

    return service_list, service, password_list, queue_id, deanak_id, worker_id, pc_num, detection_states, detection_count