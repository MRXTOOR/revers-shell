"""Tests for API routes."""
import pytest
import json
from app.redis_client import RedisClient


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/api/health')
    assert response.status_code in [200, 503]  # 503 if Redis is not available
    data = json.loads(response.data)
    assert 'status' in data
    assert 'redis' in data


def test_register_client(client, redis_client_instance):
    """Test client registration."""
    response = client.post('/api/register', json={
        'hostname': 'test-host',
        'username': 'test-user',
        'platform': 'Linux'
    })
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'session_id' in data
    assert 'status' in data
    assert data['status'] == 'registered'


def test_register_client_empty_data(client, redis_client_instance):
    """Test client registration with empty data."""
    response = client.post('/api/register', json={})
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'session_id' in data


def test_poll_command_no_command(client, redis_client_instance):
    """Test polling when no command is available."""
    # First register a client
    register_response = client.post('/api/register', json={
        'hostname': 'test-host',
        'username': 'test-user',
        'platform': 'Linux'
    })
    session_id = json.loads(register_response.data)['session_id']
    
    # Poll for command
    response = client.get(f'/api/poll/{session_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'no_command'
    assert data['command'] is None


def test_poll_command_with_command(client, redis_client_instance):
    """Test polling when command is available."""
    # Register client
    register_response = client.post('/api/register', json={
        'hostname': 'test-host',
        'username': 'test-user',
        'platform': 'Linux'
    })
    session_id = json.loads(register_response.data)['session_id']
    
    # Send a command
    send_response = client.post(f'/api/sessions/{session_id}/command', json={
        'command': 'echo "test"'
    })
    assert send_response.status_code == 200
    
    # Poll for command
    poll_response = client.get(f'/api/poll/{session_id}')
    assert poll_response.status_code == 200
    data = json.loads(poll_response.data)
    assert data['status'] == 'command_available'
    assert data['command'] == 'echo "test"'


def test_submit_result(client, redis_client_instance):
    """Test submitting command execution result."""
    # Register client
    register_response = client.post('/api/register', json={
        'hostname': 'test-host',
        'username': 'test-user',
        'platform': 'Linux'
    })
    session_id = json.loads(register_response.data)['session_id']
    
    # Submit result
    response = client.post(f'/api/result/{session_id}', json={
        'command': 'echo "test"',
        'output': 'test\n'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'result_received'


def test_list_sessions(client, redis_client_instance):
    """Test listing all sessions."""
    # Register multiple clients
    for i in range(3):
        client.post('/api/register', json={
            'hostname': f'test-host-{i}',
            'username': f'test-user-{i}',
            'platform': 'Linux'
        })
    
    # List sessions
    response = client.get('/api/sessions')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'sessions' in data
    assert len(data['sessions']) == 3


def test_get_session(client, redis_client_instance):
    """Test getting session details."""
    # Register client
    register_response = client.post('/api/register', json={
        'hostname': 'test-host',
        'username': 'test-user',
        'platform': 'Linux'
    })
    session_id = json.loads(register_response.data)['session_id']
    
    # Get session
    response = client.get(f'/api/sessions/{session_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['session_id'] == session_id
    assert 'client_info' in data
    assert data['client_info']['hostname'] == 'test-host'


def test_get_session_not_found(client, redis_client_instance):
    """Test getting non-existent session."""
    response = client.get('/api/sessions/non-existent-id')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


def test_send_command(client, redis_client_instance):
    """Test sending command to session."""
    # Register client
    register_response = client.post('/api/register', json={
        'hostname': 'test-host',
        'username': 'test-user',
        'platform': 'Linux'
    })
    session_id = json.loads(register_response.data)['session_id']
    
    # Send command
    response = client.post(f'/api/sessions/{session_id}/command', json={
        'command': 'ls -la'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'command_sent'
    assert data['command'] == 'ls -la'


def test_send_command_empty(client, redis_client_instance):
    """Test sending empty command."""
    # Register client
    register_response = client.post('/api/register', json={
        'hostname': 'test-host',
        'username': 'test-user',
        'platform': 'Linux'
    })
    session_id = json.loads(register_response.data)['session_id']
    
    # Send empty command
    response = client.post(f'/api/sessions/{session_id}/command', json={
        'command': ''
    })
    assert response.status_code == 400


def test_send_command_invalid_session(client, redis_client_instance):
    """Test sending command to non-existent session."""
    response = client.post('/api/sessions/invalid-id/command', json={
        'command': 'ls -la'
    })
    assert response.status_code == 404


def test_delete_session(client, redis_client_instance):
    """Test deleting a session."""
    # Register client
    register_response = client.post('/api/register', json={
        'hostname': 'test-host',
        'username': 'test-user',
        'platform': 'Linux'
    })
    session_id = json.loads(register_response.data)['session_id']
    
    # Delete session
    response = client.delete(f'/api/sessions/{session_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'deleted'
    
    # Verify session is deleted
    get_response = client.get(f'/api/sessions/{session_id}')
    assert get_response.status_code == 404


def test_delete_session_not_found(client, redis_client_instance):
    """Test deleting non-existent session."""
    response = client.delete('/api/sessions/non-existent-id')
    assert response.status_code == 404

