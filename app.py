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
        
        if not command:
            return jsonify({"error": "명령이 제공되지 않았습니다."}), 400
        
        # 명령 처리
        result = controller.process_command(command)
        
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True) 