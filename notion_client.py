import os
import requests
import json
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

class NotionMCPClient:
    def __init__(self, api_key=None):
        # API 키를 인자로 받거나 환경 변수에서 가져옴
        self.api_key = api_key or os.getenv("NOTION_API_KEY")
        if not self.api_key:
            raise ValueError("Notion API 키가 필요합니다.")
        
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"  # 노션 API 버전
        }
        print(f"[노션 클라이언트] 초기화됨: API 키 = {self.api_key[:4]}...{self.api_key[-4:]}")
    
    def get_databases(self):
        """사용자가 접근 가능한 데이터베이스 목록을 가져옵니다."""
        print("[노션 API] 데이터베이스 목록 조회 - search 엔드포인트 사용")
        url = f"{self.base_url}/search"
        
        # 데이터베이스만 필터링
        payload = {
            "filter": {
                "value": "database",
                "property": "object"
            },
            "sort": {
                "direction": "descending",
                "timestamp": "last_edited_time"
            }
        }
        
        print(f"[노션 API 요청] POST {url}")
        print(f"[노션 API 요청 본문] {json.dumps(payload, ensure_ascii=False)}")
        
        response = requests.post(url, headers=self.headers, json=payload)
        print(f"[노션 API 응답] 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[노션 API 오류] {response.text}")
            return response.json()
            
        # 응답에서 데이터베이스 이름을 추출하여 로그 출력
        result = response.json()
        if 'results' in result and result['results']:
            print(f"[노션 API] {len(result['results'])}개의 데이터베이스를 찾았습니다.")
            for db in result['results']:
                title = self._extract_title_from_database(db)
                print(f"[노션 API] 데이터베이스: {title} (ID: {db['id']})")
                
        return result
    
    def _extract_title_from_database(self, database):
        """데이터베이스 객체에서 제목을 추출합니다."""
        title = "제목 없음"
        try:
            if 'title' in database:
                title_items = database['title']
                if title_items:
                    for item in title_items:
                        if 'plain_text' in item:
                            title = item['plain_text']
                            break
            return title
        except Exception as e:
            print(f"[노션 API] 데이터베이스 제목 추출 오류: {e}")
            return "제목 추출 오류"
    
    def find_database_by_name(self, name):
        """이름으로 데이터베이스를 찾습니다."""
        print(f"[노션 API] '{name}' 이름의 데이터베이스 검색 중")
        
        # 데이터베이스 목록 가져오기
        databases = self.get_databases()
        
        if 'results' not in databases or not databases['results']:
            print("[노션 API] 데이터베이스를 찾을 수 없습니다.")
            return None
            
        # 이름 기준으로 데이터베이스 검색
        for db in databases['results']:
            title = self._extract_title_from_database(db)
            if name.lower() in title.lower():
                print(f"[노션 API] 데이터베이스를 찾았습니다: {title} (ID: {db['id']})")
                return db['id']
                
        print(f"[노션 API] '{name}' 이름의 데이터베이스를 찾을 수 없습니다.")
        return None
    
    def get_database(self, database_id):
        """특정 데이터베이스의 정보를 가져옵니다."""
        url = f"{self.base_url}/databases/{database_id}"
        print(f"[노션 API 요청] GET {url}")
        response = requests.get(url, headers=self.headers)
        print(f"[노션 API 응답] 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[노션 API 오류] {response.text}")
            
        return response.json()
    
    def create_database(self, parent_page_id, title, properties=None):
        """새 데이터베이스를 생성합니다."""
        url = f"{self.base_url}/databases"
        
        # 기본 속성 설정
        if not properties:
            properties = {
                "Name": {
                    "title": {}
                },
                "Description": {
                    "rich_text": {}
                },
                "Status": {
                    "select": {
                        "options": [
                            {"name": "진행 중", "color": "blue"},
                            {"name": "완료", "color": "green"},
                            {"name": "대기 중", "color": "yellow"}
                        ]
                    }
                },
                "생성일": {
                    "date": {}
                }
            }
        
        # 페이지 ID가 없으면 워크스페이스 루트 사용
        if not parent_page_id:
            # 먼저 사용자 페이지 목록 가져오기
            url_search = f"{self.base_url}/search"
            payload_search = {
                "filter": {
                    "value": "page",
                    "property": "object"
                },
                "sort": {
                    "direction": "descending",
                    "timestamp": "last_edited_time"
                }
            }
            response_search = requests.post(url_search, headers=self.headers, json=payload_search)
            
            if response_search.status_code == 200:
                search_results = response_search.json()
                if 'results' in search_results and search_results['results']:
                    parent_page_id = search_results['results'][0]['id']
                    print(f"[노션 API] 부모 페이지를 찾았습니다: {parent_page_id}")
                else:
                    return {"error": "부모 페이지를 찾을 수 없습니다. 먼저 페이지를 생성하세요."}
            else:
                return {"error": "페이지 검색 중 오류가 발생했습니다."}
        
        # 데이터베이스 생성 요청
        payload = {
            "parent": {
                "type": "page_id",
                "page_id": parent_page_id
            },
            "title": [
                {
                    "type": "text",
                    "text": {
                        "content": title
                    }
                }
            ],
            "properties": properties
        }
        
        print(f"[노션 API 요청] POST {url}")
        print(f"[노션 API 요청 본문] {json.dumps(payload, ensure_ascii=False)[:500]}...")
        
        response = requests.post(url, headers=self.headers, json=payload)
        print(f"[노션 API 응답] 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[노션 API 오류] {response.text}")
            
        return response.json()
    
    def query_database(self, database_id, filter_params=None):
        """데이터베이스에서 데이터를 쿼리합니다."""
        url = f"{self.base_url}/databases/{database_id}/query"
        payload = filter_params if filter_params else {}
        print(f"[노션 API 요청] POST {url}")
        print(f"[노션 API 요청 본문] {json.dumps(payload, ensure_ascii=False)}")
        
        response = requests.post(url, headers=self.headers, json=payload)
        print(f"[노션 API 응답] 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[노션 API 오류] {response.text}")
            
        return response.json()
    
    def create_page(self, parent_id, properties, children=None):
        """새 페이지를 생성합니다."""
        url = f"{self.base_url}/pages"
        payload = {
            "parent": {"database_id": parent_id},
            "properties": properties
        }
        if children:
            payload["children"] = children
        
        print(f"[노션 API 요청] POST {url}")
        print(f"[노션 API 요청 본문] {json.dumps(payload, ensure_ascii=False)[:500]}...")
        
        response = requests.post(url, headers=self.headers, json=payload)
        print(f"[노션 API 응답] 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[노션 API 오류] {response.text}")
            
        return response.json()
    
    def create_page_in_workspace(self, title, icon=None, children=None):
        """워크스페이스에 새 페이지를 생성합니다 (데이터베이스 없이)."""
        url = f"{self.base_url}/pages"
        
        # 먼저 최상위 페이지를 찾아서 그 아래에 새 페이지를 생성
        url_search = f"{self.base_url}/search"
        payload_search = {
            "filter": {
                "value": "page",
                "property": "object"
            },
            "sort": {
                "direction": "descending",
                "timestamp": "last_edited_time"
            },
            "page_size": 10
        }
        
        print(f"[노션 API 요청] 최상위 페이지 검색 POST {url_search}")
        response_search = requests.post(url_search, headers=self.headers, json=payload_search)
        print(f"[노션 API 응답] 상태 코드: {response_search.status_code}")
        
        parent_page_id = None
        if response_search.status_code == 200:
            search_results = response_search.json()
            if 'results' in search_results and search_results['results']:
                # 첫 번째 페이지를 부모로 선택
                parent_page_id = search_results['results'][0]['id']
                print(f"[노션 API] 부모 페이지를 찾았습니다: {parent_page_id}")
            else:
                print(f"[노션 API 오류] 사용 가능한 페이지를 찾을 수 없습니다.")
                return {"error": "사용 가능한 페이지를 찾을 수 없습니다."}
        else:
            print(f"[노션 API 오류] 페이지 검색 실패: {response_search.text}")
            return {"error": f"페이지 검색 실패: {response_search.text}"}
        
        # 페이지 생성 요청
        payload = {
            "parent": {
                "type": "page_id",
                "page_id": parent_page_id
            },
            "properties": {
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        }
        
        if icon:
            if icon.startswith("http"):
                payload["icon"] = {"type": "external", "external": {"url": icon}}
            else:
                payload["icon"] = {"type": "emoji", "emoji": icon}
        
        if children:
            payload["children"] = children
            
        print(f"[노션 API 요청] POST {url}")
        print(f"[노션 API 요청 본문] {json.dumps(payload, ensure_ascii=False)[:500]}...")
        
        response = requests.post(url, headers=self.headers, json=payload)
        print(f"[노션 API 응답] 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[노션 API 오류] {response.text}")
            
        return response.json()
    
    def update_page(self, page_id, properties):
        """페이지를 업데이트합니다."""
        url = f"{self.base_url}/pages/{page_id}"
        payload = {"properties": properties}
        
        print(f"[노션 API 요청] PATCH {url}")
        print(f"[노션 API 요청 본문] {json.dumps(payload, ensure_ascii=False)}")
        
        response = requests.patch(url, headers=self.headers, json=payload)
        print(f"[노션 API 응답] 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[노션 API 오류] {response.text}")
            
        return response.json()
    
    def get_page(self, page_id):
        """페이지 정보를 가져옵니다."""
        url = f"{self.base_url}/pages/{page_id}"
        
        print(f"[노션 API 요청] GET {url}")
        response = requests.get(url, headers=self.headers)
        print(f"[노션 API 응답] 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[노션 API 오류] {response.text}")
            
        return response.json()
    
    def get_block_children(self, block_id):
        """블록의 하위 항목을 가져옵니다."""
        url = f"{self.base_url}/blocks/{block_id}/children"
        
        print(f"[노션 API 요청] GET {url}")
        response = requests.get(url, headers=self.headers)
        print(f"[노션 API 응답] 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[노션 API 오류] {response.text}")
            
        return response.json()
    
    def append_block_children(self, block_id, children):
        """블록에 하위 항목을 추가합니다."""
        url = f"{self.base_url}/blocks/{block_id}/children"
        payload = {"children": children}
        
        print(f"[노션 API 요청] PATCH {url}")
        print(f"[노션 API 요청 본문] {json.dumps(payload, ensure_ascii=False)[:500]}...")
        
        response = requests.patch(url, headers=self.headers, json=payload)
        print(f"[노션 API 응답] 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[노션 API 오류] {response.text}")
            
        return response.json()
    
    def search(self, query="", filter_params=None, sort_params=None):
        """노션 내 객체를 검색합니다."""
        url = f"{self.base_url}/search"
        
        payload = {}
        if query:
            payload["query"] = query
        if filter_params:
            payload["filter"] = filter_params
        if sort_params:
            payload["sort"] = sort_params
            
        print(f"[노션 API 요청] POST {url}")
        print(f"[노션 API 요청 본문] {json.dumps(payload, ensure_ascii=False)}")
        
        response = requests.post(url, headers=self.headers, json=payload)
        print(f"[노션 API 응답] 상태 코드: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[노션 API 오류] {response.text}")
            
        return response.json() 