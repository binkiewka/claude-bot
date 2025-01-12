from collections import deque
from dataclasses import dataclass
from typing import Dict
from datetime import datetime

@dataclass
class Message:
    content: str
    timestamp: datetime
    is_bot: bool

class ConversationManager:
    def __init__(self, max_messages: int = 50):
        self.max_messages = max_messages
        self.conversations: Dict[int, deque] = {}
    
    def add_message(self, channel_id: int, content: str, is_bot: bool = False):
        if channel_id not in self.conversations:
            self.conversations[channel_id] = deque(maxlen=self.max_messages)
        
        self.conversations[channel_id].append(
            Message(content=content, timestamp=datetime.now(), is_bot=is_bot)
        )
    
    def get_context(self, channel_id: int, last_n: int = 5) -> str:
        if channel_id not in self.conversations:
            return ""
            
        recent_messages = list(self.conversations[channel_id])[-last_n:]
        context = []
        
        for msg in recent_messages:
            prefix = "Assistant" if msg.is_bot else "User"
            context.append(f"{prefix}: {msg.content}")
            
        return "\n".join(context)

    def clear_context(self, channel_id: int):
        """Clear conversation context for a specific channel"""
        if channel_id in self.conversations:
            del self.conversations[channel_id]
