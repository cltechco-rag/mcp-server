import os
from dotenv import load_dotenv
from mcp_controller import MCPController

# .env 파일에서 환경 변수 로드
load_dotenv()

def main():
    # API 키 가져오기
    notion_api_key = os.getenv("NOTION_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not notion_api_key or not openai_api_key:
        print("Notion API 키와 OpenAI API 키가 필요합니다.")
        print("'.env' 파일에 다음 내용을 추가해주세요:")
        print("NOTION_API_KEY=your_notion_api_key")
        print("OPENAI_API_KEY=your_openai_api_key")
        return
    
    # MCP 컨트롤러 초기화
    controller = MCPController(notion_api_key, openai_api_key)
    
    print("=== 프롬프트로 제어하는 MCP ===")
    print("(종료하려면 'exit' 또는 'quit'을 입력하세요)")
    
    while True:
        # 사용자 입력 받기
        command = input("\n명령 > ")
        
        # 종료 검사
        if command.lower() in ["exit", "quit", "종료"]:
            print("프로그램을 종료합니다.")
            break
        
        # 도움말 표시
        if command.lower() in ["help", "도움말", "도움"]:
            show_help()
            continue
        
        # 빈 명령어 검사
        if not command.strip():
            continue
        
        print("\n처리 중...")
        
        # 명령어 처리
        result = controller.process_command(command)
        
        # 결과 출력
        print("\n=== 결과 ===")
        print(result)

def show_help():
    """도움말 표시"""
    print("\n=== 도움말 ===")
    print("이 MCP는 자연어 명령을 사용하여 Notion을 제어합니다.")
    print("다음과 같은 명령을 시도해보세요:")
    print("\n1. 데이터베이스 조회:")
    print("   - '내 데이터베이스 목록을 보여줘'")
    print("\n2. 페이지 생성:")
    print("   - '제목이 \"회의록\"이고 내용이 \"오늘의 회의 내용\"인 페이지를 만들어줘'")
    print("\n3. 콘텐츠 생성:")
    print("   - '프로젝트 관리에 대한 To-Do 리스트를 만들어줘'")
    print("\n4. 데이터베이스 쿼리:")
    print("   - '프로젝트 데이터베이스에서 상태가 \"진행 중\"인 항목을 찾아줘'")

if __name__ == "__main__":
    main() 