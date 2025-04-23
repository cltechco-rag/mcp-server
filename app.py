from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from mcp_controller import MCPController
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

app = Flask(__name__)
CORS(app)  # CORS 활성화

# MCP 컨트롤러 초기화
controller = MCPController()

# 루트 경로에서 index.html 제공
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/api/process_command', methods=['POST'])
def process_command():
    """사용자 명령을 처리하는 API 엔드포인트"""
    try:
        data = request.json
        command = data.get('command')
        additional_data = data.get('additional_data', None)
        
        if not command:
            return jsonify({"error": "명령이 제공되지 않았습니다."}), 400
        
        # 요약 정보 저장 명령어 처리
        if ('요약' in command and '저장' in command) and additional_data:
            title = additional_data.get('title')
            summary = additional_data.get('summary')
            metadata = additional_data.get('metadata', {})
            
            if not title or not summary:
                return jsonify({"error": "제목 또는 요약 정보가 제공되지 않았습니다."}), 400
                
            result = controller.save_summary(title, summary, metadata)
            return jsonify({"result": result})
            
        # 페이지 삭제 명령어 처리
        elif command == '페이지 삭제' and additional_data:
            page_name = additional_data.get('page_name')
            
            if not page_name:
                return jsonify({"error": "삭제할 페이지 이름이 제공되지 않았습니다."}), 400
                
            result = controller.delete_page(page_name)
            return jsonify({"result": result})
            
        # 일반 명령 처리
        else:
            result = controller.process_command(command)
            return jsonify({"result": result})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/save_summary', methods=['POST'])
def save_summary():
    """외부 서비스에서 생성된 요약 정보를 노션에 저장하는 API 엔드포인트"""
    try:
        data = request.json
        
        # 필수 필드 검증
        if 'title' not in data or not data['title']:
            return jsonify({"error": "제목이 필요합니다."}), 400
        
        if 'summary' not in data or not data['summary']:
            return jsonify({"error": "요약 내용이 필요합니다."}), 400
        
        # 추가 메타데이터 있으면 받기
        metadata = data.get('metadata', {})
        source_url = metadata.get('source_url', '')
        author = metadata.get('author', '')
        tags = metadata.get('tags', [])
        
        # 요약 정보 저장
        result = controller.save_summary(
            title=data['title'],
            summary=data['summary'],
            metadata=metadata
        )
        
        return jsonify({"result": result})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/databases', methods=['GET'])
def get_databases():
    """사용 가능한 데이터베이스 목록을 반환하는 API 엔드포인트"""
    try:
        result = controller._get_databases()
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """API 서버 상태 확인 엔드포인트"""
    return jsonify({"status": "ok"})

@app.route('/api/generate_summary', methods=['POST'])
def generate_summary():
    """비디오 요약을 생성하는 API 엔드포인트"""
    try:
        data = request.json
        video_id = data.get('video_id')
        
        if not video_id:
            return jsonify({"success": False, "message": "비디오 ID가 필요합니다."}), 400
            
        # OpenAI를 사용하여 요약 생성 (실제 구현에서는 비디오 내용을 분석)
        # 이 예제에서는 간단한 요약 예시를 반환
        
        # 비디오 ID에 따라 다른 요약 반환
        if video_id == "vid-001":
            summary = "인공지능의 정의와 역사적 발전 과정부터 시작하여 머신러닝과 딥러닝의 차이점, 그리고 다양한 적용 사례를 다룹니다.\n\n" + \
                    "주요 내용:\n" + \
                    "1. 인공지능의 기본 개념 및 역사\n" + \
                    "2. 머신러닝과 딥러닝의 차이점\n" + \
                    "3. 지도학습, 비지도학습, 강화학습의 특징\n" + \
                    "4. 실생활에서의 AI 적용 사례\n" + \
                    "5. 인공지능의 미래 전망"
        elif video_id == "vid-002":
            summary = "이 영상은 데이터 시각화의 중요성과 다양한 시각화 도구를 소개합니다.\n\n" + \
                    "주요 내용:\n" + \
                    "1. 데이터 시각화의 목적과 중요성\n" + \
                    "2. 파이썬 시각화 라이브러리 비교: Matplotlib, Seaborn, Plotly\n" + \
                    "3. 데이터 유형별 적합한 시각화 방법 선택 방법\n" + \
                    "4. 효과적인 대시보드 구성 팁과 사용자 경험 고려사항\n\n" + \
                    "실제 데이터셋을 활용한 예제를 통해 실무에 바로 적용할 수 있는 기술을 제공합니다. 특히 인터랙티브 시각화 부분이 매우 유용합니다."
        elif video_id == "vid-003":
            summary = "이 영상은 2023년 웹 개발 트렌드와 주요 기술을 분석합니다.\n\n" + \
                    "주요 내용:\n" + \
                    "1. 프론트엔드 프레임워크 최신 동향: React, Vue, Svelte 비교\n" + \
                    "2. 서버리스 아키텍처와 JAMstack의 부상\n" + \
                    "3. WebAssembly와 PWA의 진화\n" + \
                    "4. AI 기반 개발 도구와 자동화의 확산\n\n" + \
                    "각 기술별 실제 적용 사례와 성능 비교를 통해 현업 개발자들이 고려해볼 만한 기술 스택 선택에 도움이 됩니다. 특히 비용 효율성과 확장성 측면의 분석이 유용합니다."
        else:
            summary = "이 영상의 주요 내용은 다음과 같습니다:\n\n" + \
                    "1. 핵심 주제 설명 및 개요\n" + \
                    "2. 중요 개념과 기술적 세부사항\n" + \
                    "3. 실제 적용 사례 및 예시\n" + \
                    "4. 결론 및 향후 전망"
        
        # 요약 저장 (실제 구현에서는 데이터베이스에 저장)
        # 이 예제에서는 저장 로직을 생략
        
        return jsonify({
            "success": True,
            "video_id": video_id,
            "summary": summary,
            "message": "요약이 성공적으로 생성되었습니다."
        })
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/get_summary', methods=['GET'])
def get_summary():
    """비디오 요약을 가져오는 API 엔드포인트"""
    try:
        video_id = request.args.get('video_id')
        
        if not video_id:
            return jsonify({"success": False, "message": "비디오 ID가 필요합니다."}), 400
        
        # 요약 조회 (실제 구현에서는 데이터베이스에서 조회)
        # 이 예제에서는 미리 정의된 요약 반환
        
        # 비디오 ID에 따라 다른 요약 반환
        if video_id == "vid-001":
            summary = "인공지능의 정의와 역사적 발전 과정부터 시작하여 머신러닝과 딥러닝의 차이점, 그리고 다양한 적용 사례를 다룹니다.\n\n" + \
                    "주요 내용:\n" + \
                    "1. 인공지능의 기본 개념 및 역사\n" + \
                    "2. 머신러닝과 딥러닝의 차이점\n" + \
                    "3. 지도학습, 비지도학습, 강화학습의 특징\n" + \
                    "4. 실생활에서의 AI 적용 사례\n" + \
                    "5. 인공지능의 미래 전망"
        elif video_id == "vid-002":
            summary = "이 영상은 데이터 시각화의 중요성과 다양한 시각화 도구를 소개합니다.\n\n" + \
                    "주요 내용:\n" + \
                    "1. 데이터 시각화의 목적과 중요성\n" + \
                    "2. 파이썬 시각화 라이브러리 비교: Matplotlib, Seaborn, Plotly\n" + \
                    "3. 데이터 유형별 적합한 시각화 방법 선택 방법\n" + \
                    "4. 효과적인 대시보드 구성 팁과 사용자 경험 고려사항\n\n" + \
                    "실제 데이터셋을 활용한 예제를 통해 실무에 바로 적용할 수 있는 기술을 제공합니다. 특히 인터랙티브 시각화 부분이 매우 유용합니다."
        elif video_id == "vid-003":
            summary = "이 영상은 2023년 웹 개발 트렌드와 주요 기술을 분석합니다.\n\n" + \
                    "주요 내용:\n" + \
                    "1. 프론트엔드 프레임워크 최신 동향: React, Vue, Svelte 비교\n" + \
                    "2. 서버리스 아키텍처와 JAMstack의 부상\n" + \
                    "3. WebAssembly와 PWA의 진화\n" + \
                    "4. AI 기반 개발 도구와 자동화의 확산\n\n" + \
                    "각 기술별 실제 적용 사례와 성능 비교를 통해 현업 개발자들이 고려해볼 만한 기술 스택 선택에 도움이 됩니다. 특히 비용 효율성과 확장성 측면의 분석이 유용합니다."
        else:
            # 요약 정보가 없는 경우
            return jsonify({"success": False, "message": "해당 비디오의 요약 정보가 존재하지 않습니다."}), 404
        
        return jsonify({
            "success": True,
            "video_id": video_id,
            "summary": summary
        })
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True) 