import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# API 키 설정
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# API 키가 없으면 오류 발생
if not NOTION_API_KEY:
    raise ValueError("NOTION_API_KEY 환경 변수가 설정되지 않았습니다.")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

# 구성 설정
DEFAULT_OPENAI_MODEL = "gpt-3.5-turbo"  # 또는 "gpt-4" 등 다른 모델
MAX_TOKENS = 1000
TEMPERATURE = 0.7

# Notion API 구성
NOTION_VERSION = "2022-06-28"  # Notion API 버전 