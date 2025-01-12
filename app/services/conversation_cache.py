import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List

class ConversationCache:
    def __init__(
        self, 
        max_conversations: int = 100, 
        max_age_hours: int = 24
    ):
        # In-memory conversation storage
        self._conversations: Dict[str, Dict] = {}
        # Track last interaction for each conversation
        self._last_interactions: Dict[str, datetime] = {}
        self._max_conversations = max_conversations
        self._max_age = timedelta(hours=max_age_hours)

    async def add_message(
        self, 
        server_id: str, 
        user_id: str, 
        message: Dict[str, str], 
        conversation_id: Optional[str] = None
    ) -> str:
        """
        Add a message to the conversation cache with enhanced context tracking
        """
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # Initialize conversation if not exists
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = {
                'server_id': server_id,
                'user_id': user_id,
                'messages': [],
                'context': {}
            }

        # Add message to conversation
        full_message = {
            **message,
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id
        }
        self._conversations[conversation_id]['messages'].append(full_message)
        
        # Update last interaction timestamp
        self._last_interactions[conversation_id] = datetime.utcnow()

        # Prune old conversations
        self._prune_conversations()

        return conversation_id

    async def get_conversation(
        self, 
        server_id: str, 
        conversation_id: str, 
        max_messages: int = 10
    ) -> Optional[Dict]:
        """
        Retrieve conversation with context
        """
        # Check if conversation exists and matches server
        if (conversation_id in self._conversations and 
            self._conversations[conversation_id]['server_id'] == server_id):
            
            conversation = self._conversations[conversation_id]
            return {
                'conversation_id': conversation_id,
                'messages': conversation['messages'][-max_messages:],
                'context': conversation.get('context', {}),
                'last_interaction': self._last_interactions.get(conversation_id)
            }
        
        return None

    async def get_recent_conversations(
        self, 
        server_id: str, 
        limit: int = 5
    ) -> List[Dict]:
        """
        Retrieve recent conversations for a server
        """
        # Filter conversations by server and sort by last interaction
        recent_convos = [
            {
                'conversation_id': conv_id,
                'messages': conv_data['messages'],
                'last_interaction': self._last_interactions.get(conv_id)
            }
            for conv_id, conv_data in self._conversations.items()
            if conv_data['server_id'] == server_id
        ]
        
        # Sort by most recent interaction
        recent_convos.sort(
            key=lambda x: x['last_interaction'] or datetime.min, 
            reverse=True
        )
        
        return recent_convos[:limit]

    def _prune_conversations(self):
        """
        Remove conversations older than max_age
        """
        current_time = datetime.utcnow()
        
        # Identify conversations to remove
        conversations_to_remove = [
            conv_id for conv_id, last_interaction in self._last_interactions.items()
            if current_time - last_interaction > self._max_age
        ]
        
        # Remove old conversations
        for conv_id in conversations_to_remove:
            del self._conversations[conv_id]
            del self._last_interactions[conv_id]

    async def clear_conversation(self, conversation_id: str):
        """
        Clear a specific conversation
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            del self._last_interactions[conversation_id]
