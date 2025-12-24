"""Redis client wrapper for session management."""
import redis
import json
from typing import Optional, Dict, List
from app.config import Config


class RedisClient:
    """Redis client for managing reverse shell sessions."""
    
    def __init__(self, redis_client=None):
        """Initialize Redis connection.
        
        Args:
            redis_client: Optional Redis client instance (for testing).
                         If None, creates a new connection using Config.
        """
        if redis_client is not None:
            self.client = redis_client
        else:
            self.client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD,
                decode_responses=True
            )
    
    def create_session(self, session_id: str, client_info: Dict) -> bool:
        """Create a new reverse shell session."""
        session_data = {
            'session_id': session_id,
            'client_info': client_info,
            'status': 'active',
            'created_at': client_info.get('timestamp', ''),
            'commands': []
        }
        key = f"session:{session_id}"
        self.client.setex(
            key,
            Config.SESSION_TIMEOUT,
            json.dumps(session_data)
        )
        return True
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data by session ID."""
        key = f"session:{session_id}"
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None
    
    def update_session(self, session_id: str, updates: Dict) -> bool:
        """Update session data."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.update(updates)
        key = f"session:{session_id}"
        ttl = self.client.ttl(key)
        if ttl > 0:
            self.client.setex(key, ttl, json.dumps(session))
        else:
            self.client.setex(key, Config.SESSION_TIMEOUT, json.dumps(session))
        return True
    
    def add_command(self, session_id: str, command: str, output: str) -> bool:
        """Add command execution result to session history."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        command_entry = {
            'command': command,
            'output': output,
            'timestamp': str(int(__import__('time').time()))
        }
        
        commands = session.get('commands', [])
        commands.append(command_entry)
        
        # Keep only last N commands
        if len(commands) > Config.MAX_COMMAND_HISTORY:
            commands = commands[-Config.MAX_COMMAND_HISTORY:]
        
        session['commands'] = commands
        key = f"session:{session_id}"
        ttl = self.client.ttl(key)
        if ttl > 0:
            self.client.setex(key, ttl, json.dumps(session))
        else:
            self.client.setex(key, Config.SESSION_TIMEOUT, json.dumps(session))
        return True
    
    def list_sessions(self) -> List[str]:
        """List all active session IDs."""
        pattern = "session:*"
        keys = self.client.keys(pattern)
        return [key.replace("session:", "") for key in keys]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        key = f"session:{session_id}"
        return bool(self.client.delete(key))
    
    def set_command_for_session(self, session_id: str, command: str) -> bool:
        """Set a command to be executed by the client."""
        key = f"command:{session_id}"
        self.client.setex(key, 300, command)  # 5 minutes TTL
        return True
    
    def get_command_for_session(self, session_id: str) -> Optional[str]:
        """Get and remove the next command for a session."""
        key = f"command:{session_id}"
        command = self.client.get(key)
        if command:
            self.client.delete(key)
            return command
        return None
    
    def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return self.client.ping()
        except Exception:
            return False

