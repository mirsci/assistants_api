"""
Session Storage for Gemini Shopping Assistant

This module provides persistent session storage for Gemini-based shopping
conversations using Redis and PostgreSQL, similar to the OpenAI implementation
but adapted for Gemini API specifics.

Features:
- Redis caching for fast session access
- PostgreSQL for persistent storage
- Multi-tenant isolation
- GDPR compliance (data deletion)
- Conversation history management
"""

import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

try:
    import redis
    from sqlalchemy import (
        create_engine, Column, String, DateTime, Integer, 
        Float, JSON, Text, Index, ForeignKey
    )
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False


# ============================================================================
# ABSTRACT STORAGE INTERFACE
# ============================================================================

class GeminiSessionStorageInterface(ABC):
    """Abstract interface for Gemini conversation storage backends"""
    
    @abstractmethod
    def create_conversation(self, conversation_data: Dict[str, Any]) -> bool:
        """Create a new conversation"""
        pass
    
    @abstractmethod
    def get_conversation(self, conversation_id: str, partner_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve conversation with multi-tenant isolation"""
        pass
    
    @abstractmethod
    def update_conversation(self, conversation_id: str, partner_id: str, updates: Dict[str, Any]) -> bool:
        """Update conversation data"""
        pass
    
    @abstractmethod
    def add_message(self, conversation_id: str, partner_id: str, message_data: Dict[str, Any]) -> bool:
        """Add a conversation message"""
        pass
    
    @abstractmethod
    def delete_conversation(self, conversation_id: str, partner_id: str) -> bool:
        """Delete conversation (GDPR compliance)"""
        pass
    
    @abstractmethod
    def list_conversations(self, partner_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List conversations for a partner or user"""
        pass


# ============================================================================
# REDIS CACHE LAYER
# ============================================================================

class GeminiRedisCache:
    """
    Redis-based conversation caching for Gemini sessions.
    
    Conversations are stored in Redis with TTL for automatic expiry.
    This provides O(1) lookup time for active sessions.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        ttl_seconds: int = 3600,
        key_prefix: str = "gemini_conv:"
    ):
        """
        Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
            ttl_seconds: Time-to-live for cached sessions (default: 1 hour)
            key_prefix: Prefix for Redis keys (for namespace isolation)
        """
        if not HAS_DEPENDENCIES:
            self.redis_client = None
            self.available = False
            return
        
        try:
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            self.available = True
        except Exception as e:
            print(f"Warning: Redis not available: {e}")
            self.redis_client = None
            self.available = False
        
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
    
    def _make_key(self, conversation_id: str, partner_id: str) -> str:
        """
        Generate Redis key with multi-tenant isolation.
        
        Format: gemini_conv:{partner_id}:{conversation_id}
        """
        return f"{self.key_prefix}{partner_id}:{conversation_id}"
    
    def set_conversation(
        self,
        conversation_id: str,
        partner_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """Cache a conversation with TTL"""
        if not self.available:
            return False
        
        try:
            key = self._make_key(conversation_id, partner_id)
            self.redis_client.setex(
                key,
                self.ttl_seconds,
                json.dumps(data, default=str)
            )
            return True
        except Exception as e:
            print(f"Redis cache error: {e}")
            return False
    
    def get_conversation(self, conversation_id: str, partner_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a cached conversation"""
        if not self.available:
            return None
        
        try:
            key = self._make_key(conversation_id, partner_id)
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Redis retrieval error: {e}")
        
        return None
    
    def delete_conversation(self, conversation_id: str, partner_id: str) -> bool:
        """Delete a cached conversation"""
        if not self.available:
            return False
        
        try:
            key = self._make_key(conversation_id, partner_id)
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Redis deletion error: {e}")
            return False
    
    def expire_conversation(self, conversation_id: str, partner_id: str) -> bool:
        """Reset TTL for a conversation"""
        if not self.available:
            return False
        
        try:
            key = self._make_key(conversation_id, partner_id)
            self.redis_client.expire(key, self.ttl_seconds)
            return True
        except Exception as e:
            print(f"Redis expiry error: {e}")
            return False


# ============================================================================
# POSTGRESQL STORAGE LAYER (Schema Definition)
# ============================================================================

if HAS_DEPENDENCIES:
    Base = declarative_base()
    
    class ConversationRecord(Base):
        """PostgreSQL table for storing conversations"""
        __tablename__ = 'gemini_conversations'
        
        id = Column(String(36), primary_key=True)  # UUID
        partner_id = Column(String(255), nullable=False, index=True)
        user_id = Column(String(255), nullable=False, index=True)
        title = Column(String(255), nullable=True)
        metadata = Column(JSON, nullable=True)
        created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
        updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
        
        # Indexes for common queries
        __table_args__ = (
            Index('idx_partner_user', 'partner_id', 'user_id'),
            Index('idx_partner_created', 'partner_id', 'created_at'),
        )
    
    class MessageRecord(Base):
        """PostgreSQL table for storing conversation messages"""
        __tablename__ = 'gemini_messages'
        
        id = Column(String(36), primary_key=True)  # UUID
        conversation_id = Column(String(36), nullable=False, index=True)
        partner_id = Column(String(255), nullable=False)
        role = Column(String(50), nullable=False)  # 'user' or 'model'
        content = Column(Text, nullable=False)
        products = Column(JSON, nullable=True)  # Array of products
        timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
        
        # Index for conversation queries
        __table_args__ = (
            Index('idx_conversation_time', 'conversation_id', 'timestamp'),
        )


# ============================================================================
# HYBRID STORAGE IMPLEMENTATION
# ============================================================================

class GeminiHybridSessionStorage(GeminiSessionStorageInterface):
    """
    Hybrid storage combining Redis (cache) and PostgreSQL (persistence).
    
    This implementation provides:
    - Fast access to active conversations via Redis
    - Durable storage via PostgreSQL
    - Automatic cache invalidation
    - Multi-tenant isolation
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        database_url: str = "postgresql://localhost/gemini_shopping",
        enable_cache: bool = True,
        enable_db: bool = False
    ):
        """
        Initialize hybrid storage.
        
        Args:
            redis_url: Redis connection URL
            database_url: PostgreSQL connection URL
            enable_cache: Use Redis caching
            enable_db: Use PostgreSQL persistence
        """
        self.cache = None
        self.db_session = None
        
        if enable_cache:
            self.cache = GeminiRedisCache(redis_url)
        
        if enable_db and HAS_DEPENDENCIES:
            try:
                engine = create_engine(database_url)
                Base.metadata.create_all(engine)
                self.db_session = sessionmaker(bind=engine)
            except Exception as e:
                print(f"Warning: PostgreSQL not available: {e}")
    
    def create_conversation(self, conversation_data: Dict[str, Any]) -> bool:
        """Create a new conversation"""
        conversation_id = conversation_data.get('conversation_id')
        partner_id = conversation_data.get('partner_id')
        
        # Cache in Redis
        if self.cache:
            self.cache.set_conversation(conversation_id, partner_id, conversation_data)
        
        # Persist to PostgreSQL
        if self.db_session:
            try:
                session = self.db_session()
                record = ConversationRecord(
                    id=conversation_id,
                    partner_id=partner_id,
                    user_id=conversation_data.get('user_id', ''),
                    title=conversation_data.get('title'),
                    metadata=conversation_data.get('metadata'),
                    created_at=conversation_data.get('created_at', datetime.utcnow()),
                    updated_at=datetime.utcnow()
                )
                session.add(record)
                session.commit()
                session.close()
            except Exception as e:
                print(f"Database error creating conversation: {e}")
        
        return True
    
    def get_conversation(
        self,
        conversation_id: str,
        partner_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve conversation with cache-first approach"""
        # Try cache first
        if self.cache:
            cached = self.cache.get_conversation(conversation_id, partner_id)
            if cached:
                # Update cache expiry
                self.cache.expire_conversation(conversation_id, partner_id)
                return cached
        
        # Fall back to database
        if self.db_session:
            try:
                session = self.db_session()
                record = session.query(ConversationRecord).filter_by(
                    id=conversation_id,
                    partner_id=partner_id
                ).first()
                session.close()
                
                if record:
                    data = {
                        'conversation_id': record.id,
                        'partner_id': record.partner_id,
                        'user_id': record.user_id,
                        'title': record.title,
                        'metadata': record.metadata,
                        'created_at': record.created_at.isoformat(),
                        'updated_at': record.updated_at.isoformat()
                    }
                    # Re-cache for future access
                    if self.cache:
                        self.cache.set_conversation(conversation_id, partner_id, data)
                    return data
            except Exception as e:
                print(f"Database error retrieving conversation: {e}")
        
        return None
    
    def update_conversation(
        self,
        conversation_id: str,
        partner_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update conversation in both cache and database"""
        # Update cache
        if self.cache:
            current = self.cache.get_conversation(conversation_id, partner_id)
            if current:
                current.update(updates)
                current['updated_at'] = datetime.utcnow().isoformat()
                self.cache.set_conversation(conversation_id, partner_id, current)
        
        # Update database
        if self.db_session:
            try:
                session = self.db_session()
                record = session.query(ConversationRecord).filter_by(
                    id=conversation_id,
                    partner_id=partner_id
                ).first()
                
                if record:
                    for key, value in updates.items():
                        if hasattr(record, key):
                            setattr(record, key, value)
                    record.updated_at = datetime.utcnow()
                    session.commit()
                
                session.close()
                return True
            except Exception as e:
                print(f"Database error updating conversation: {e}")
        
        return False
    
    def add_message(
        self,
        conversation_id: str,
        partner_id: str,
        message_data: Dict[str, Any]
    ) -> bool:
        """Add a message to a conversation"""
        # Store in database
        if self.db_session:
            try:
                session = self.db_session()
                record = MessageRecord(
                    id=str(__import__('uuid').uuid4()),
                    conversation_id=conversation_id,
                    partner_id=partner_id,
                    role=message_data.get('role', 'user'),
                    content=message_data.get('content', ''),
                    products=message_data.get('products'),
                    timestamp=message_data.get('timestamp', datetime.utcnow())
                )
                session.add(record)
                session.commit()
                session.close()
            except Exception as e:
                print(f"Database error adding message: {e}")
        
        return True
    
    def delete_conversation(self, conversation_id: str, partner_id: str) -> bool:
        """Delete conversation from both cache and database"""
        # Delete from cache
        if self.cache:
            self.cache.delete_conversation(conversation_id, partner_id)
        
        # Delete from database
        if self.db_session:
            try:
                session = self.db_session()
                session.query(ConversationRecord).filter_by(
                    id=conversation_id,
                    partner_id=partner_id
                ).delete()
                session.query(MessageRecord).filter_by(
                    conversation_id=conversation_id,
                    partner_id=partner_id
                ).delete()
                session.commit()
                session.close()
            except Exception as e:
                print(f"Database error deleting conversation: {e}")
        
        return True
    
    def list_conversations(
        self,
        partner_id: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List conversations for a partner or user"""
        conversations = []
        
        if self.db_session:
            try:
                session = self.db_session()
                query = session.query(ConversationRecord).filter_by(partner_id=partner_id)
                
                if user_id:
                    query = query.filter_by(user_id=user_id)
                
                records = query.order_by(ConversationRecord.updated_at.desc()).all()
                
                for record in records:
                    conversations.append({
                        'conversation_id': record.id,
                        'user_id': record.user_id,
                        'partner_id': record.partner_id,
                        'title': record.title,
                        'created_at': record.created_at.isoformat(),
                        'updated_at': record.updated_at.isoformat()
                    })
                
                session.close()
            except Exception as e:
                print(f"Database error listing conversations: {e}")
        
        return conversations


# ============================================================================
# SIMPLE IN-MEMORY STORAGE (for testing without dependencies)
# ============================================================================

class GeminiMemoryStorage(GeminiSessionStorageInterface):
    """
    Simple in-memory storage for testing and development.
    
    Not suitable for production use. Use GeminiHybridSessionStorage
    with Redis/PostgreSQL for production deployments.
    """
    
    def __init__(self):
        """Initialize in-memory storage"""
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.messages: List[Dict[str, Any]] = []
    
    def create_conversation(self, conversation_data: Dict[str, Any]) -> bool:
        """Create a new conversation"""
        conv_id = conversation_data.get('conversation_id')
        self.conversations[conv_id] = conversation_data.copy()
        return True
    
    def get_conversation(
        self,
        conversation_id: str,
        partner_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve conversation"""
        conv = self.conversations.get(conversation_id)
        if conv and conv.get('partner_id') == partner_id:
            return conv
        return None
    
    def update_conversation(
        self,
        conversation_id: str,
        partner_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update conversation"""
        conv = self.conversations.get(conversation_id)
        if conv and conv.get('partner_id') == partner_id:
            conv.update(updates)
            conv['updated_at'] = datetime.utcnow().isoformat()
            return True
        return False
    
    def add_message(
        self,
        conversation_id: str,
        partner_id: str,
        message_data: Dict[str, Any]
    ) -> bool:
        """Add a message"""
        conv = self.conversations.get(conversation_id)
        if conv and conv.get('partner_id') == partner_id:
            self.messages.append({
                **message_data,
                'conversation_id': conversation_id,
                'partner_id': partner_id
            })
            return True
        return False
    
    def delete_conversation(self, conversation_id: str, partner_id: str) -> bool:
        """Delete conversation"""
        conv = self.conversations.get(conversation_id)
        if conv and conv.get('partner_id') == partner_id:
            del self.conversations[conversation_id]
            self.messages = [m for m in self.messages if m.get('conversation_id') != conversation_id]
            return True
        return False
    
    def list_conversations(
        self,
        partner_id: str,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List conversations"""
        conversations = []
        for conv in self.conversations.values():
            if conv.get('partner_id') == partner_id:
                if user_id is None or conv.get('user_id') == user_id:
                    conversations.append({
                        'conversation_id': conv.get('conversation_id'),
                        'user_id': conv.get('user_id'),
                        'partner_id': conv.get('partner_id'),
                        'created_at': conv.get('created_at'),
                        'updated_at': conv.get('updated_at')
                    })
        return conversations
