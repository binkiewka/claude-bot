from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True)
    server_id = Column(String, index=True)
    channel_id = Column(String, index=True)
    user_id = Column(String, index=True)
    conversation_id = Column(String, unique=True, index=True)
    messages = Column(JSON)
    context = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserProfile(Base):
    __tablename__ = 'user_profiles'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, index=True)
    discord_username = Column(String)
    total_interactions = Column(Integer, default=0)
    last_interaction_at = Column(DateTime)
    preferences = Column(JSON)

class ServerRole(Base):
    __tablename__ = 'server_roles'

    id = Column(Integer, primary_key=True)
    server_id = Column(String, index=True, unique=True)
    role_id = Column(String, nullable=False)
    role_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ServerRole(server_id={self.server_id}, role_name={self.role_name})>"

    @classmethod
    def create(cls, server_id: str, role_id: str, role_name: str):
        """Create a new server role"""
        return cls(
            server_id=server_id,
            role_id=role_id,
            role_name=role_name
        )

    def update_role(self, role_id: str, role_name: str):
        """Update role information"""
        self.role_id = role_id
        self.role_name = role_name
        self.updated_at = datetime.utcnow()
