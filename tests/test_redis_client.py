"""Tests for Redis client."""
import pytest
import time
from app.redis_client import RedisClient


def test_create_session(redis_client_instance):
    """Test creating a session."""
    session_id = "test-session-123"
    client_info = {
        'hostname': 'test-host',
        'username': 'test-user',
        'platform': 'Linux',
        'timestamp': str(int(time.time()))
    }
    
    result = redis_client_instance.create_session(session_id, client_info)
    assert result is True
    
    session = redis_client_instance.get_session(session_id)
    assert session is not None
    assert session['session_id'] == session_id
    assert session['client_info']['hostname'] == 'test-host'


def test_get_session_not_found(redis_client_instance):
    """Test getting non-existent session."""
    session = redis_client_instance.get_session("non-existent")
    assert session is None


def test_update_session(redis_client_instance):
    """Test updating session."""
    session_id = "test-session-123"
    client_info = {
        'hostname': 'test-host',
        'username': 'test-user',
        'platform': 'Linux',
        'timestamp': str(int(time.time()))
    }
    
    redis_client_instance.create_session(session_id, client_info)
    
    updates = {'status': 'inactive'}
    result = redis_client_instance.update_session(session_id, updates)
    assert result is True
    
    session = redis_client_instance.get_session(session_id)
    assert session['status'] == 'inactive'


def test_add_command(redis_client_instance):
    """Test adding command to session."""
    session_id = "test-session-123"
    client_info = {
        'hostname': 'test-host',
        'username': 'test-user',
        'platform': 'Linux',
        'timestamp': str(int(time.time()))
    }
    
    redis_client_instance.create_session(session_id, client_info)
    
    result = redis_client_instance.add_command(session_id, 'ls -la', 'output here')
    assert result is True
    
    session = redis_client_instance.get_session(session_id)
    assert len(session['commands']) == 1
    assert session['commands'][0]['command'] == 'ls -la'
    assert session['commands'][0]['output'] == 'output here'


def test_list_sessions(redis_client_instance):
    """Test listing all sessions."""
    # Create multiple sessions
    for i in range(3):
        session_id = f"test-session-{i}"
        client_info = {
            'hostname': f'test-host-{i}',
            'username': 'test-user',
            'platform': 'Linux',
            'timestamp': str(int(time.time()))
        }
        redis_client_instance.create_session(session_id, client_info)
    
    sessions = redis_client_instance.list_sessions()
    assert len(sessions) == 3
    assert 'test-session-0' in sessions
    assert 'test-session-1' in sessions
    assert 'test-session-2' in sessions


def test_delete_session(redis_client_instance):
    """Test deleting a session."""
    session_id = "test-session-123"
    client_info = {
        'hostname': 'test-host',
        'username': 'test-user',
        'platform': 'Linux',
        'timestamp': str(int(time.time()))
    }
    
    redis_client_instance.create_session(session_id, client_info)
    
    result = redis_client_instance.delete_session(session_id)
    assert result is True
    
    session = redis_client_instance.get_session(session_id)
    assert session is None


def test_set_and_get_command(redis_client_instance):
    """Test setting and getting command for session."""
    session_id = "test-session-123"
    
    # Set command
    result = redis_client_instance.set_command_for_session(session_id, 'ls -la')
    assert result is True
    
    # Get command
    command = redis_client_instance.get_command_for_session(session_id)
    assert command == 'ls -la'
    
    # Command should be removed after getting
    command_again = redis_client_instance.get_command_for_session(session_id)
    assert command_again is None


def test_ping(redis_client_instance):
    """Test Redis ping."""
    result = redis_client_instance.ping()
    assert result is True

