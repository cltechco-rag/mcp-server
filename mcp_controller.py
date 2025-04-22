import json
import re
import os
from notion_client import NotionMCPClient
from openai_client import OpenAIMCPClient
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

class MCPController:
    def __init__(self, notion_api_key=None, openai_api_key=None):
        """노션 및 OpenAI 클라이언트를 초기화합니다."""
        # API 키를 인자로 받거나 환경 변수에서 가져옴
        notion_api_key = notion_api_key or os.getenv("NOTION_API_KEY")
        openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        self.notion_client = NotionMCPClient(api_key=notion_api_key)
        self.openai_client = OpenAIMCPClient(api_key=openai_api_key)
        self.conversation_history = []  # 대화 기록 저장
    
    def process_command(self, command):
        """사용자 명령어를 처리합니다."""
        try:
            print(f"\n[디버그] 입력 명령: '{command}'")
            
            # 사용자 입력의 의도 분석
            intent_result = self.openai_client.analyze_intent(command)
            intent_data = json.loads(intent_result)
            print(f"\n[디버그] 의도 분석 결과: {intent_data}")
            
            if intent_data["intent"] == "notion_command":
                # Notion 관련 명령 처리
                parsed_command = self.openai_client.parse_notion_command(command)
                print(f"\n[디버그] 명령 분석 결과(원본):\n{parsed_command}")
                
                try:
                    # JSON 형식으로 파싱
                    action_data = json.loads(parsed_command)
                    print(f"\n[디버그] 파싱된 JSON:\n{json.dumps(action_data, indent=2, ensure_ascii=False)}")
                    
                    # 명령에 따라 적절한 작업 수행
                    action = action_data.get("action")
                    print(f"\n[디버그] 감지된 작업: {action}")
                    
                    if action == "create_page":
                        return self._create_page(action_data.get("parameters"))
                    elif action == "create_database":
                        return self._create_database(action_data.get("parameters"))
                    elif action == "create_page_in_workspace":
                        return self._create_page_in_workspace(action_data.get("parameters"))
                    elif action == "update_page":
                        return self._update_page(action_data.get("parameters"))
                    elif action == "query_database":
                        return self._query_database(action_data.get("parameters"))
                    elif action == "get_databases":
                        return self._get_databases()
                    elif action == "generate_content":
                        return self._generate_content(action_data.get("parameters"))
                    else:
                        return f"지원하지 않는 작업: {action}"
                except json.JSONDecodeError as e:
                    print(f"\n[디버그] JSON 파싱 오류: {str(e)}")
                    return f"명령 분석 결과(JSON 변환 실패):\n{parsed_command}"
            else:
                # 일반 대화 처리
                response = self.openai_client.chat(command, self.conversation_history)
                
                # 대화 기록 업데이트
                self.conversation_history.append({"role": "user", "content": command})
                self.conversation_history.append({"role": "assistant", "content": response})
                
                # 대화 기록이 너무 길어지면 초기화
                if len(self.conversation_history) > 10:  # 최대 5개의 대화 쌍 유지
                    self.conversation_history = []
                
                return response
        except Exception as e:
            return f"명령 처리 중 오류 발생: {str(e)}"
    
    def _create_database(self, parameters):
        """노션 데이터베이스를 생성합니다."""
        try:
            print(f"\n[디버그] 데이터베이스 생성 매개변수: {json.dumps(parameters, indent=2, ensure_ascii=False)}")
            
            title = parameters.get("title", "새 데이터베이스")
            parent_page_id = parameters.get("parent_page_id", None)
            properties = parameters.get("properties", None)
            
            # 부모 페이지가 없으면 페이지부터 생성
            if not parent_page_id:
                # 워크스페이스에 페이지 생성
                page_title = f"{title} 페이지"
                page_response = self.notion_client.create_page_in_workspace(page_title)
                
                if 'id' in page_response:
                    parent_page_id = page_response['id']
                    print(f"\n[디버그] 부모 페이지 생성됨: {parent_page_id}")
                else:
                    return f"부모 페이지 생성 실패: {page_response}"
            
            # 데이터베이스 생성
            response = self.notion_client.create_database(parent_page_id, title, properties)
            
            if 'id' in response:
                db_url = response.get('url', '')
                return f"데이터베이스 '{title}' 생성 완료 (ID: {response.get('id')})\n링크: {db_url}"
            else:
                return f"데이터베이스 생성 실패: {response}"
        except Exception as e:
            return f"데이터베이스 생성 중 오류 발생: {str(e)}"
    
    def _create_page_in_workspace(self, parameters):
        """워크스페이스에 페이지를 생성합니다."""
        try:
            title = parameters.get("title", "새 페이지")
            icon = parameters.get("icon", None)
            content_prompt = parameters.get("content_prompt", None)
            content_type = parameters.get("content_type", "text")
            
            # 콘텐츠 생성
            children = []
            if content_prompt:
                content = self.openai_client.generate_notion_content(content_prompt, content_type)
                
                # 생성된 내용을 블록으로 변환
                if content_type == "text":
                    for paragraph in content.split("\n\n"):
                        if paragraph.strip():
                            children.append({
                                "object": "block", 
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": paragraph}}]
                                }
                            })
                elif content_type in ["todo", "bullet"]:
                    for line in content.split("\n"):
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("- [ ]"):
                            children.append({
                                "object": "block", 
                                "type": "to_do",
                                "to_do": {
                                    "rich_text": [{"type": "text", "text": {"content": line[5:].strip()}}],
                                    "checked": False
                                }
                            })
                        elif line.startswith("-"):
                            children.append({
                                "object": "block", 
                                "type": "bulleted_list_item",
                                "bulleted_list_item": {
                                    "rich_text": [{"type": "text", "text": {"content": line[1:].strip()}}]
                                }
                            })
                        else:
                            children.append({
                                "object": "block", 
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": line}}]
                                }
                            })
            
            # 페이지 생성
            response = self.notion_client.create_page_in_workspace(title, icon, children)
            
            if 'id' in response:
                page_url = response.get('url', '')
                return f"워크스페이스에 페이지 '{title}' 생성 완료 (ID: {response.get('id')})\n링크: {page_url}"
            else:
                return f"페이지 생성 실패: {response}"
        except Exception as e:
            return f"페이지 생성 중 오류 발생: {str(e)}"
    
    def _create_page(self, parameters):
        """노션 페이지를 생성합니다."""
        try:
            print(f"\n[디버그] 페이지 생성 매개변수: {json.dumps(parameters, indent=2, ensure_ascii=False)}")
            
            parent_id = parameters.get("parent_id")
            properties = parameters.get("properties", {})
            
            # 부모 ID가 실제 UUID가 아닌 텍스트 설명인 경우 처리
            if parent_id and not self._is_valid_uuid(parent_id):
                # 데이터베이스 이름에서 추출
                db_name_match = re.search(r"(.*?)(?:\s+데이터베이스(?:\s+ID)?)?$", parent_id)
                if db_name_match:
                    db_name = db_name_match.group(1).strip()
                    print(f"\n[디버그] 데이터베이스 이름 '{db_name}'으로 ID 검색 중")
                    actual_id = self.notion_client.find_database_by_name(db_name)
                    if actual_id:
                        parent_id = actual_id
                        print(f"\n[디버그] 데이터베이스 ID를 찾았습니다: {parent_id}")
                    else:
                        print(f"\n[디버그] 데이터베이스 '{db_name}'을 찾을 수 없습니다.")
                        parent_id = None
            
            # 데이터베이스 ID가 없는 경우 처리
            if not parent_id:
                # 사용자의 데이터베이스 목록 가져오기
                databases = self.notion_client.get_databases()
                if 'results' in databases and len(databases['results']) > 0:
                    # 첫 번째 데이터베이스 사용
                    parent_id = databases['results'][0]['id']
                    print(f"\n[디버그] 데이터베이스 ID 없음. 첫 번째 데이터베이스 사용: {parent_id}")
                else:
                    # 데이터베이스가 없으면 워크스페이스에 페이지를 생성
                    title = parameters.get("title", "새 페이지")
                    content_prompt = parameters.get("content_prompt", None)
                    content_type = parameters.get("content_type", "text")
                    icon = parameters.get("icon", None)
                    
                    return self._create_page_in_workspace({
                        "title": title,
                        "content_prompt": content_prompt,
                        "content_type": content_type,
                        "icon": icon
                    })
            
            # 데이터베이스 스키마 확인
            db_info = self.notion_client.get_database(parent_id)
            print(f"\n[디버그] 데이터베이스 스키마: {json.dumps(db_info.get('properties', {}), indent=2, ensure_ascii=False)}")
            
            # 속성 이름 매핑 (영어 -> 한글)
            property_name_mapping = {
                "Name": "이름",
                "Description": "설명",
                "Status": "상태",
                "Date": "날짜",
                "Tags": "태그",
                "Priority": "우선순위",
                "Assignee": "담당자",
                "Created": "생성일",
                "Updated": "수정일"
            }
            
            # 매핑된 속성 이름으로 변환
            mapped_properties = {}
            for prop_name, prop_value in properties.items():
                # 매핑된 이름이 있으면 사용, 없으면 원래 이름 사용
                mapped_name = property_name_mapping.get(prop_name, prop_name)
                mapped_properties[mapped_name] = prop_value
                print(f"\n[디버그] 속성 이름 매핑: {prop_name} -> {mapped_name}")
            
            # 페이지 타이틀 속성이 없으면 기본값 추가
            if mapped_properties and not any('title' in prop for prop in mapped_properties.values()):
                # 타이틀 속성 찾기
                title_property = None
                for prop_name, prop_info in db_info.get('properties', {}).items():
                    if prop_info.get('type') == 'title':
                        title_property = prop_name
                        break
                
                if title_property and title_property not in mapped_properties:
                    title_content = parameters.get('title', '새 페이지')
                    mapped_properties[title_property] = {
                        "title": [{"text": {"content": title_content}}]
                    }
                    print(f"\n[디버그] 페이지 타이틀 자동 추가: {title_property} = {title_content}")
            
            # 속성 타입 검증 및 수정
            validated_properties = {}
            for prop_name, prop_value in mapped_properties.items():
                # 데이터베이스에 해당 속성이 있는지 확인
                if prop_name in db_info.get('properties', {}):
                    prop_type = db_info['properties'][prop_name].get('type')
                    print(f"\n[디버그] 속성 '{prop_name}' 타입: {prop_type}")
                    
                    # 속성 타입에 따라 적절한 형식으로 변환
                    if prop_type == 'title':
                        # title 타입은 title 키가 있어야 함
                        if isinstance(prop_value, list) and len(prop_value) > 0:
                            # 리스트 형식으로 제공된 경우
                            validated_properties[prop_name] = {"title": prop_value}
                        elif 'title' in prop_value:
                            # 이미 title 키가 있는 경우
                            validated_properties[prop_name] = prop_value
                        else:
                            # 텍스트만 제공된 경우
                            validated_properties[prop_name] = {
                                "title": [{"text": {"content": str(prop_value)}}]
                            }
                    elif prop_type == 'rich_text' and 'rich_text' in prop_value:
                        validated_properties[prop_name] = prop_value
                    elif prop_type == 'number' and 'number' in prop_value:
                        validated_properties[prop_name] = prop_value
                    elif prop_type == 'select' and 'select' in prop_value:
                        validated_properties[prop_name] = prop_value
                    elif prop_type == 'multi_select' and 'multi_select' in prop_value:
                        validated_properties[prop_name] = prop_value
                    elif prop_type == 'date' and 'date' in prop_value:
                        validated_properties[prop_name] = prop_value
                    elif prop_type == 'formula':
                        # formula 타입은 읽기 전용이므로 제외
                        print(f"\n[디버그] formula 타입 속성 '{prop_name}'은 제외됨 (읽기 전용)")
                    elif prop_type == 'relation':
                        # relation 타입은 특별한 처리가 필요하므로 제외
                        print(f"\n[디버그] relation 타입 속성 '{prop_name}'은 제외됨 (특별한 처리 필요)")
                    elif prop_type == 'rollup':
                        # rollup 타입은 읽기 전용이므로 제외
                        print(f"\n[디버그] rollup 타입 속성 '{prop_name}'은 제외됨 (읽기 전용)")
                    elif prop_type == 'people' and 'people' in prop_value:
                        validated_properties[prop_name] = prop_value
                    elif prop_type == 'files' and 'files' in prop_value:
                        validated_properties[prop_name] = prop_value
                    elif prop_type == 'checkbox' and 'checkbox' in prop_value:
                        validated_properties[prop_name] = prop_value
                    elif prop_type == 'url' and 'url' in prop_value:
                        validated_properties[prop_name] = prop_value
                    elif prop_type == 'email' and 'email' in prop_value:
                        validated_properties[prop_name] = prop_value
                    elif prop_type == 'phone_number' and 'phone_number' in prop_value:
                        validated_properties[prop_name] = prop_value
                    else:
                        # 알 수 없는 타입이거나 속성 형식이 맞지 않는 경우
                        print(f"\n[디버그] 속성 '{prop_name}'의 타입 '{prop_type}'은 지원되지 않거나 형식이 맞지 않음")
                else:
                    # 데이터베이스에 없는 속성은 제외
                    print(f"\n[디버그] 데이터베이스에 없는 속성 '{prop_name}'은 제외됨")
            
            # 페이지 내용이 문자열로 제공된 경우 OpenAI로 생성
            if "content_prompt" in parameters:
                content_type = parameters.get("content_type", "text")
                content = self.openai_client.generate_notion_content(
                    parameters.get("content_prompt"), content_type
                )
                
                # 생성된 내용을 블록으로 변환
                if content_type == "text":
                    children = []
                    for paragraph in content.split("\n\n"):
                        if paragraph.strip():
                            children.append({
                                "object": "block", 
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": paragraph}}]
                                }
                            })
                elif content_type in ["todo", "bullet"]:
                    # TODO 및 bullet 목록을 파싱하여 Notion 형식으로 변환
                    children = []
                    for line in content.split("\n"):
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("- [ ]"):
                            children.append({
                                "object": "block", 
                                "type": "to_do",
                                "to_do": {
                                    "rich_text": [{"type": "text", "text": {"content": line[5:].strip()}}],
                                    "checked": False
                                }
                            })
                        elif line.startswith("-"):
                            children.append({
                                "object": "block", 
                                "type": "bulleted_list_item",
                                "bulleted_list_item": {
                                    "rich_text": [{"type": "text", "text": {"content": line[1:].strip()}}]
                                }
                            })
                        else:
                            # 그 외의 텍스트는 단락으로 처리
                            children.append({
                                "object": "block", 
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [{"type": "text", "text": {"content": line}}]
                                }
                            })
            else:
                children = parameters.get("children", [])
            
            # 페이지 생성
            print(f"\n[디버그] 페이지 생성 요청: parent_id={parent_id}, properties={validated_properties}")
            result = self.notion_client.create_page(parent_id, validated_properties, children)
            
            if 'id' in result:
                page_url = result.get('url', '')
                return f"페이지 생성 완료: {result.get('id')}\n링크: {page_url}"
            else:
                return f"페이지 생성 실패: {result}"
        except Exception as e:
            return f"페이지 생성 중 오류 발생: {str(e)}"
    
    def _is_valid_uuid(self, uuid_str):
        """문자열이 유효한 UUID 형식인지 확인합니다."""
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        return bool(uuid_pattern.match(uuid_str))
    
    def _update_page(self, parameters):
        """노션 페이지를 업데이트합니다."""
        try:
            page_id = parameters.get("page_id")
            properties = parameters.get("properties", {})
            result = self.notion_client.update_page(page_id, properties)
            return f"페이지 업데이트 완료: {result.get('id', '알 수 없음')}"
        except Exception as e:
            return f"페이지 업데이트 중 오류 발생: {str(e)}"
    
    def _query_database(self, parameters):
        """노션 데이터베이스를 쿼리합니다."""
        try:
            database_id = parameters.get("database_id")
            
            # 데이터베이스 ID가 이름인 경우 처리
            if database_id and not self._is_valid_uuid(database_id):
                db_name_match = re.search(r"(.*?)(?:\s+데이터베이스(?:\s+ID)?)?$", database_id)
                if db_name_match:
                    db_name = db_name_match.group(1).strip()
                    actual_id = self.notion_client.find_database_by_name(db_name)
                    if actual_id:
                        database_id = actual_id
                    else:
                        return f"데이터베이스 '{db_name}'을 찾을 수 없습니다."
            
            filter_params = parameters.get("filter", {})
            result = self.notion_client.query_database(database_id, filter_params)
            
            # 상세 정보 추출
            pages = result.get('results', [])
            
            if not pages:
                return "데이터베이스에서 페이지를 찾을 수 없습니다."
            
            # 데이터베이스 정보 가져오기
            db_info = self.notion_client.get_database(database_id)
            db_name = "알 수 없음"
            if 'title' in db_info:
                for item in db_info['title']:
                    if 'plain_text' in item:
                        db_name = item['plain_text']
                        break
            
            # 속성 정보 가져오기
            properties_info = db_info.get('properties', {})
            
            # 결과 메시지 생성
            response = [f"'{db_name}' 데이터베이스 조회 결과: {len(pages)}개의 페이지 찾음"]
            
            # 각 페이지 정보 추가
            for i, page in enumerate(pages):
                page_id = page.get('id', '알 수 없음')
                page_url = page.get('url', '링크 없음')
                
                # 페이지 제목 찾기
                page_title = "제목 없음"
                for prop_name, prop_data in page.get('properties', {}).items():
                    if prop_data.get('type') == 'title':
                        title_array = prop_data.get('title', [])
                        if title_array:
                            texts = [item.get('plain_text', '') for item in title_array if 'plain_text' in item]
                            page_title = ''.join(texts)
                            break
                
                # 페이지 정보 문자열 생성
                page_info = [f"\n{i+1}. {page_title} (ID: {page_id[:8]}...)"]
                page_info.append(f"   링크: {page_url}")
                
                # 주요 속성 추가
                for prop_name, prop_data in page.get('properties', {}).items():
                    if prop_name == 'title' or prop_data.get('type') == 'title':
                        continue  # 이미 제목은 위에서 추출했음
                    
                    prop_type = prop_data.get('type')
                    prop_value = "값 없음"
                    
                    # 속성 타입에 따라 값 추출
                    if prop_type == 'rich_text':
                        texts = prop_data.get('rich_text', [])
                        prop_value = ''.join([item.get('plain_text', '') for item in texts if 'plain_text' in item])
                    elif prop_type == 'number':
                        prop_value = prop_data.get('number', 0)
                    elif prop_type == 'select':
                        select_data = prop_data.get('select', {})
                        prop_value = select_data.get('name', '') if select_data else ''
                    elif prop_type == 'multi_select':
                        multi_select = prop_data.get('multi_select', [])
                        prop_value = ', '.join([item.get('name', '') for item in multi_select if 'name' in item])
                    elif prop_type == 'date':
                        date_data = prop_data.get('date', {})
                        start_date = date_data.get('start', '') if date_data else ''
                        end_date = date_data.get('end', '') if date_data else ''
                        if start_date and end_date:
                            prop_value = f"{start_date} ~ {end_date}"
                        else:
                            prop_value = start_date
                    elif prop_type == 'checkbox':
                        prop_value = "✅" if prop_data.get('checkbox') else "❌"
                    elif prop_type == 'url':
                        prop_value = prop_data.get('url', '')
                    elif prop_type == 'email':
                        prop_value = prop_data.get('email', '')
                    elif prop_type == 'phone_number':
                        prop_value = prop_data.get('phone_number', '')
                    elif prop_type == 'formula':
                        formula_data = prop_data.get('formula', {})
                        if 'string' in formula_data:
                            prop_value = formula_data.get('string', '')
                        elif 'number' in formula_data:
                            prop_value = str(formula_data.get('number', 0))
                        elif 'boolean' in formula_data:
                            prop_value = "✅" if formula_data.get('boolean') else "❌"
                        elif 'date' in formula_data:
                            date_data = formula_data.get('date', {})
                            prop_value = date_data.get('start', '') if date_data else ''
                    
                    if prop_value and str(prop_value).strip():
                        page_info.append(f"   {prop_name}: {prop_value}")
                
                response.append(''.join(page_info))
            
            return '\n'.join(response)
        except Exception as e:
            return f"데이터베이스 쿼리 중 오류 발생: {str(e)}"
    
    def _get_databases(self):
        """사용 가능한 데이터베이스 목록을 가져옵니다."""
        try:
            result = self.notion_client.get_databases()
            databases = result.get("results", [])
            
            # 데이터베이스 정보 출력
            if databases:
                db_info = ["사용 가능한 데이터베이스:"]
                for db in databases:
                    title = self.notion_client._extract_title_from_database(db)
                    db_info.append(f"- {title} (ID: {db['id']})")
                return "\n".join(db_info)
            else:
                return "사용 가능한 데이터베이스가 없습니다."
        except Exception as e:
            return f"데이터베이스 목록 가져오기 중 오류 발생: {str(e)}"
    
    def _generate_content(self, parameters):
        """OpenAI로 콘텐츠를 생성합니다."""
        try:
            prompt = parameters.get("prompt", "")
            content_type = parameters.get("content_type", "text")
            content = self.openai_client.generate_notion_content(prompt, content_type)
            return content
        except Exception as e:
            return f"콘텐츠 생성 중 오류 발생: {str(e)}" 