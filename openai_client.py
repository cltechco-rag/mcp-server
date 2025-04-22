import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import re
import json

# .env 파일에서 환경 변수 로드
load_dotenv()

class OpenAIMCPClient:
    def __init__(self, api_key=None):
        """Azure OpenAI API 클라이언트를 초기화합니다."""
        # API 키를 인자로 받거나 환경 변수에서 가져옴
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Azure OpenAI API 키가 필요합니다.")
        
        # Azure OpenAI 클라이언트 설정
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
    
    def analyze_intent(self, user_input):
        """사용자 입력의 의도를 분석합니다."""
        try:
            system_prompt = """당신은 사용자의 입력을 분석하여 적절한 작업을 결정하는 전문가입니다.
다음 중 하나의 의도를 결정해야 합니다:

1. notion_command: Notion 관련 작업 (데이터베이스 생성, 페이지 추가 등)
2. general_chat: 일반적인 대화나 질문

응답 형식:
{
    "intent": "notion_command 또는 general_chat",
    "explanation": "의도 판단 이유에 대한 간단한 설명"
}

Notion 관련 키워드:
- 데이터베이스, 페이지, 노션, Notion, 추가, 생성, 조회, 목록

예시:
입력: "KT 데이터베이스에 새 페이지 추가해줘"
응답: {"intent": "notion_command", "explanation": "Notion 데이터베이스 작업 요청"}

입력: "오늘 날씨 어때?"
응답: {"intent": "general_chat", "explanation": "일반적인 날씨 관련 질문"}

중요: 반드시 위의 JSON 형식으로만 응답하고, 다른 텍스트나 설명은 추가하지 마세요."""

            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            
            # JSON 형식 검증
            try:
                # 응답 내용에서 JSON 부분만 추출 (가끔 모델이 다른 텍스트를 추가할 수 있음)
                json_pattern = r'(\{.*\})'
                json_match = re.search(json_pattern, result, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(1)
                    # 유효성 검사
                    json.loads(json_str)
                    return json_str
                else:
                    # JSON 아니면 기본값 반환
                    return '{"intent": "general_chat", "explanation": "의도 분석 실패, 일반 대화로 처리"}'
            except:
                # JSON 파싱 오류 시 기본값 반환
                return '{"intent": "general_chat", "explanation": "의도 분석 실패, 일반 대화로 처리"}'
                
        except Exception as e:
            print(f"의도 분석 오류: {str(e)}")
            return '{"intent": "general_chat", "explanation": "오류 발생"}'
            
    def chat(self, user_input, conversation_history=None):
        """일반적인 대화를 처리합니다."""
        try:
            messages = [
                {"role": "system", "content": "당신은 친절하고 지식이 풍부한 AI 어시스턴트입니다. 사용자의 질문에 명확하고 도움이 되는 답변을 제공합니다."}
            ]
            
            # 대화 기록이 있으면 추가
            if conversation_history:
                messages.extend(conversation_history)
            
            # 현재 사용자 입력 추가
            messages.append({"role": "user", "content": user_input})
            
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"대화 처리 오류: {str(e)}"
    
    def generate_text(self, prompt, model=None, max_tokens=1000, temperature=0.7, system_prompt=None):
        """텍스트 생성 함수"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            else:
                messages.append({"role": "system", "content": "You are a helpful assistant."})
                
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"텍스트 생성 오류: {str(e)}"
    
    def generate_notion_content(self, prompt, content_type="text"):
        """노션에 적합한 콘텐츠를 생성합니다."""
        instruction = ""
        if content_type == "text":
            instruction = "노션 페이지에 들어갈 텍스트 콘텐츠를 생성해주세요."
        elif content_type == "todo":
            instruction = "노션 To-Do 목록을 생성해주세요. 각 항목은 새로운 줄에 '- [ ] ' 형식으로 작성해주세요."
        elif content_type == "table":
            instruction = "노션 테이블 형식의 데이터를 생성해주세요. 마크다운 테이블 형식으로 작성해주세요."
        elif content_type == "bullet":
            instruction = "노션 글머리 기호 목록을 생성해주세요. 각 항목은 새로운 줄에 '- ' 형식으로 작성해주세요."
        
        full_prompt = f"{instruction}\n\n{prompt}"
        return self.generate_text(full_prompt)
    
    def parse_notion_command(self, command):
        """사용자 명령을 분석하여 노션 작업으로 변환합니다."""
        try:
            system_prompt = """당신은 사용자 명령을 노션 API 작업으로 변환하는 전문가입니다.
사용자의 자연어 명령을 분석하여 적절한 노션 API 작업과 필요한 매개변수를 JSON 형식으로 제공해야 합니다.

가능한 작업 유형:
1. get_databases: 사용자의 데이터베이스 목록 조회
2. query_database: 특정 데이터베이스에서 조건으로 검색
3. create_page: 데이터베이스에 새 페이지 생성
4. create_page_in_workspace: 워크스페이스에 새 페이지 생성 (데이터베이스 없이)
5. create_database: 새 데이터베이스 생성
6. update_page: 기존 페이지 업데이트
7. generate_content: AI로 콘텐츠 생성

중요: 데이터베이스나 페이지를 식별할 때는 ID 대신 이름을 사용하세요.
예를 들어, "KT 데이터베이스 ID" 대신 단순히 "KT"라고 지정하세요.
시스템이 이름으로 실제 ID를 찾을 수 있습니다.

데이터베이스 생성 시 필요한 매개변수 예시:
{
  "action": "create_database",
  "parameters": {
    "title": "데이터베이스 이름",
    "parent_page_id": "부모_페이지_ID" // 선택 사항, 없으면 자동으로 생성됨
  },
  "description": "새 데이터베이스 생성"
}

워크스페이스에 페이지 생성 시 필요한 매개변수 예시:
{
  "action": "create_page_in_workspace",
  "parameters": {
    "title": "페이지 제목",
    "content_prompt": "페이지 내용 생성을 위한 프롬프트", // 선택 사항
    "content_type": "text", // text, todo, bullet 중 하나, 기본값은 text
    "icon": "🚀" // 선택 사항, 이모지 또는 이미지 URL
  },
  "description": "워크스페이스에 새 페이지 생성"
}

데이터베이스 내 페이지 생성 시 필요한 매개변수 예시:
{
  "action": "create_page",
  "parameters": {
    "parent_id": "데이터베이스 이름", // 데이터베이스의 정확한 ID 대신 이름을 사용
    "title": "페이지 제목", // 페이지 제목
    "properties": {
      "Name": { // 데이터베이스의 필드 이름에 따라 다름, "Name"은 예시
        "title": [{ "text": { "content": "페이지 제목" } }]
      }
      // 필요한 경우 다른 속성 추가
    },
    "content_prompt": "페이지 내용 생성을 위한 프롬프트", // 선택 사항
    "content_type": "text" // text, todo, bullet 중 하나, 기본값은 text
  },
  "description": "데이터베이스에 새 페이지 생성"
}

데이터베이스 쿼리 시 필요한 매개변수 예시:
{
  "action": "query_database",
  "parameters": {
    "database_id": "데이터베이스 이름", // 데이터베이스의 정확한 ID 대신 이름을 사용
    "filter": { // 선택 사항, 필터 조건
      "property": "속성명",
      "조건 타입": { "조건 값": "값" }
    }
  },
  "description": "데이터베이스 내 항목 조회"
}

사용자가 "xx 데이터베이스 만들어줘"와 같이 요청하면 반드시 create_database 작업을 사용하세요.
사용자가 그냥 페이지를 생성하려는 의도면 create_page_in_workspace 작업을 사용하세요.
데이터베이스에 항목을 추가하려는 의도면 create_page 작업을 사용하세요.
사용자가 데이터베이스 내용이나 항목을 보고 싶어하면 반드시 query_database 작업을 사용하세요.

JSON 응답 형식은 다음과 같아야 합니다:
{
  "action": "작업유형",
  "parameters": {
    // 작업에 필요한 매개변수들
  },
  "description": "작업에 대한 간단한 설명"
}

중요: 반드시 유효한 JSON 형식으로만 응답하고, JSON 외에 다른 텍스트나 설명은 추가하지 마세요."""
            
            prompt = f"다음 사용자 명령을 노션 작업으로 변환해주세요: {command}"
            
            response = self.generate_text(prompt, system_prompt=system_prompt)
            
            # JSON 형식 검증
            try:
                # 응답 내용에서 JSON 부분만 추출 (가끔 모델이 다른 텍스트를 추가할 수 있음)
                json_pattern = r'(\{.*\})'
                json_match = re.search(json_pattern, response, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(1)
                    # 유효성 검사
                    json.loads(json_str)
                    return json_str
                else:
                    # JSON 형식이 아니면 기본 응답 제공
                    default_response = {
                        "action": "create_page_in_workspace",
                        "parameters": {
                            "title": "새 페이지",
                            "content_prompt": command
                        },
                        "description": "JSON 파싱 실패로 기본 작업 수행"
                    }
                    return json.dumps(default_response, ensure_ascii=False)
            except:
                # JSON 파싱 오류 시 기본값 반환
                default_response = {
                    "action": "create_page_in_workspace",
                    "parameters": {
                        "title": "새 페이지",
                        "content_prompt": command
                    },
                    "description": "JSON 파싱 실패로 기본 작업 수행"
                }
                return json.dumps(default_response, ensure_ascii=False)
        except Exception as e:
            print(f"명령 파싱 오류: {str(e)}")
            # 오류 발생 시 기본 응답 제공
            default_response = {
                "action": "create_page_in_workspace",
                "parameters": {
                    "title": "새 페이지",
                    "content_prompt": command
                },
                "description": "오류로 인한 기본 작업 수행"
            }
            return json.dumps(default_response, ensure_ascii=False) 