# 프롬프트 기반 노션 MCP 클라이언트

OpenAI API와 Notion API를 사용하여 자연어 명령으로 노션 작업 공간을 제어하는 클라이언트입니다.

## 설치 방법

1. 저장소를 클론합니다:
```
git clone [저장소 URL]
cd [프로젝트 폴더]
```

2. 가상 환경을 생성하고 활성화합니다:
```
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 필요한 패키지를 설치합니다:
```
pip install -r requirements.txt
```

4. API 키 설정:
   - `.env` 파일을 생성하고 다음 내용을 추가합니다:
   ```
   NOTION_API_KEY=your_notion_api_key
   OPENAI_API_KEY=your_openai_api_key
   ```
   - 또는 `config.py` 파일에서 직접 API 키를 설정할 수 있습니다.

## 주요 기능

- 자연어 명령으로 노션 작업 제어
- OpenAI를 활용한 노션 콘텐츠 자동 생성
- 데이터베이스 조회 및 쿼리
- 페이지 생성 및 수정

## 사용 방법

### 기본 사용법

```python
from mcp_controller import MCPController

# 컨트롤러 초기화
controller = MCPController()

# 자연어 명령 처리
result = controller.process_command("내 데이터베이스 목록을 보여줘")
print(result)
```

### 프롬프트 기반 CLI 실행

```
python prompt_mcp_example.py
```

다음과 같은 명령을 시도해보세요:

1. 데이터베이스 조회:
   - '내 데이터베이스 목록을 보여줘'

2. 페이지 생성:
   - '제목이 "회의록"이고 내용이 "오늘의 회의 내용"인 페이지를 만들어줘'

3. 콘텐츠 생성:
   - '프로젝트 관리에 대한 To-Do 리스트를 만들어줘'

4. 데이터베이스 쿼리:
   - '프로젝트 데이터베이스에서 상태가 "진행 중"인 항목을 찾아줘'

## 구성 요소

- `notion_client.py`: Notion API 클라이언트
- `openai_client.py`: OpenAI API 클라이언트
- `mcp_controller.py`: 노션과 OpenAI 클라이언트를 통합하는 컨트롤러
- `prompt_mcp_example.py`: 프롬프트 기반 CLI 예제
- `config.py`: 구성 설정 파일

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 