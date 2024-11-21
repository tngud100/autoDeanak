class TemplateLoadError(Exception): 
  """템플릿 로드 중 발생하는 예외"""
class ScreenCaptureError(Exception): 
  """화면 캡처 중 발생하는 예외"""
class DetectTemplateError(Exception): 
  """템플릿 탐지 중 발생하는 예외"""


class NoDetectionError(Exception):
  """탐지 결과가 없는 경우"""
class WrongPasswordError(Exception): 
  """잘못된 비밀번호 발생하는 예외"""
class unactivatedRemoteError(Exception): 
  """원격프로그램의 비활성화된 창에서 발생하는 예외"""

