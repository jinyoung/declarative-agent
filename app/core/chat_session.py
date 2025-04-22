"""
Chat Session module for managing continuous conversations with agents.

This module provides functionality for managing chat sessions with agents,
allowing for continuous conversations over multiple requests.
"""
from typing import Dict, List, Optional, Any
import time
import uuid
import logging

# Configure logging
logger = logging.getLogger(__name__)

class Message:
    """A message in a chat session."""
    
    def __init__(self, role: str, content: str, timestamp: float = None):
        """
        Initialize a chat message.
        
        Args:
            role: Role of the message sender ('user' or 'assistant')
            content: Content of the message
            timestamp: Optional timestamp (defaults to current time)
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary representation."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a message from a dictionary representation."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", time.time())
        )


class ChatSession:
    """
    Manages a continuous conversation with an agent.
    
    This class stores the history of a conversation and provides methods
    to add messages and retrieve the conversation history.
    """
    
    def __init__(self, session_id: str = None, agent_id: str = None):
        """
        Initialize a chat session.
        
        Args:
            session_id: Optional session ID (generated if not provided)
            agent_id: ID of the agent associated with this session
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.agent_id = agent_id
        self.messages: List[Message] = []
        self.created_at = time.time()
        self.last_activity = self.created_at
    
    def add_message(self, role: str, content: str) -> Message:
        """
        Add a message to the conversation.
        
        Args:
            role: Role of the message sender ('user' or 'assistant')
            content: Content of the message
            
        Returns:
            The created message
        """
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.last_activity = message.timestamp
        return message
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """
        Get all messages in the conversation as dictionaries.
        
        Returns:
            List of message dictionaries
        """
        return [msg.to_dict() for msg in self.messages]
    
    def get_history_as_string(self) -> str:
        """
        Get the conversation history as a formatted string.
        
        This format is suitable for including in prompts to LLMs.
        
        Returns:
            Formatted conversation history
        """
        history = []
        for msg in self.messages:
            prefix = "User" if msg.role == "user" else "Assistant"
            history.append(f"{prefix}: {msg.content}")
        return "\n".join(history)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the session to a dictionary representation."""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at,
            "last_activity": self.last_activity
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatSession':
        """Create a session from a dictionary representation."""
        session = cls(
            session_id=data["session_id"],
            agent_id=data.get("agent_id")
        )
        session.created_at = data.get("created_at", time.time())
        session.last_activity = data.get("last_activity", session.created_at)
        session.messages = [Message.from_dict(msg) for msg in data.get("messages", [])]
        return session


class ChatSessionManager:
    """
    Manages multiple chat sessions.
    
    This class provides methods to create, retrieve, update, and delete chat sessions.
    """
    
    def __init__(self):
        """Initialize the chat session manager."""
        self.sessions: Dict[str, ChatSession] = {}
    
    def create_session(self, agent_id: str = None) -> ChatSession:
        """
        Create a new chat session.
        
        Args:
            agent_id: Optional ID of the agent associated with this session
            
        Returns:
            The created chat session
        """
        session = ChatSession(agent_id=agent_id)
        self.sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get a chat session by ID.
        
        Args:
            session_id: ID of the session to retrieve
            
        Returns:
            The chat session, or None if not found
        """
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session.
        
        Args:
            session_id: ID of the session to delete
            
        Returns:
            True if the session was deleted, False otherwise
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def clean_inactive_sessions(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up inactive sessions older than the specified age.
        
        Args:
            max_age_seconds: Maximum age of inactive sessions in seconds
            
        Returns:
            Number of sessions removed
        """
        now = time.time()
        to_remove = [
            session_id for session_id, session in self.sessions.items()
            if now - session.last_activity > max_age_seconds
        ]
        
        for session_id in to_remove:
            del self.sessions[session_id]
        
        return len(to_remove) 