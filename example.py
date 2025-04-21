from notion_client import NotionMCPClient

def main():
    # 클라이언트 초기화 (.env 파일에서 API 키를 로드합니다)
    client = NotionMCPClient()
    
    try:
        # 사용자의 데이터베이스 목록 가져오기
        databases = client.get_databases()
        print("사용 가능한 데이터베이스:")
        for db in databases.get("results", []):
            print(f"- {db.get('title', [{}])[0].get('text', {}).get('content', '제목 없음')} (ID: {db.get('id')})")
        
        # 예제: 특정 데이터베이스에서 데이터 쿼리하기
        # database_id = "여기에 데이터베이스 ID 입력"
        # query_result = client.query_database(database_id)
        # print(f"\n{database_id} 데이터베이스의 항목:")
        # for item in query_result.get("results", []):
        #     print(f"- {item.get('id')}")
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    main() 