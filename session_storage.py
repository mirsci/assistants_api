"""
Session Storage Layer for Multi-Tenant Shopping Assistant

This module provides production-ready session storage using Redis (cache) 
and PostgreSQL (persistence) to replace in-memory storage in the 
conversation manager.

Key features:
- Redis for fast session retrieval and caching
- PostgreSQL for persistent storage and analytics
- Multi-tenant isolation (partner_id scoping)
- GDPR compliance (data deletion)
- Session expiry and cleanup
"""

import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

import redis
from sqlalchemy import (
    create_engine, Column, String, DateTime, Integer, 
    Float, JSON, Text, Index, ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


# ============================================================================
# ABSTRACT STORAGE INTERFACE
# ============================================================================

class SessionStorageInterface(ABC):
    """Abstract interface for session storage backends"""
    
    @abstractmethod
    def create_session(self, session_data: Dict[str, Any]) -> bool:
        """Create a new session"""
        pass
    
    @abstractmethod
    def get_session(self, session_id: str, partner_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session with multi-tenant isolation"""
        pass
    
    @abstractmethod
    def update_session(self, session_id: str, partner_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        pass
    
    @abstractmethod
    def add_turn(self, session_id: str, partner_id: str, turn_data: Dict[str, Any]) -> bool:
        """Add a conversation turn to session"""
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str, partner_id: str) -> bool:
        """Delete session (GDPR compliance)"""
        pass


# ============================================================================
# REDIS CACHE LAYER
# ============================================================================

class RedisSessionCache:
    """
    Redis-based session caching for fast retrieval.
    
    Sessions are stored in Redis with TTL for automatic expiry.
    This provides O(1) lookup time and reduces database load.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        ttl_seconds: int = 3600,
        key_prefix: str = "session:"
    ):
        """
        Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
            ttl_seconds: Time-to-live for cached sessions (default: 1 hour)
            key_prefix: Prefix for Redis keys (for namespace isolation)
        """
        self.redis_client = redis.from_url(redis_url)
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
    
    def _make_key(self, session_id: str, partner_id: str) -> str:
        """
        Generate Redis key with multi-tenant isolation.
        
        Format: session:{partner_id}:{session_id}
        This ensures Partner A cannot access Partner B's sessions.
        """
        return f"{self.key_prefix}{partner_id}:{session_id}"
    
    def set(self, session_id: str, partner_id: str, data: Dict[str, Any]) -> bool:
        """Cache session data with TTL"""
        key = self._make_key(session_id, partner_id)
        try:
            self.redis_client.setex(
                key,
                self.ttl_seconds,
                json.dumps(data)
            )
            return True
        except Exception as e:
            print(f"Redis cache error: {e}")
            return False
    
    def get(self, session_id: str, partner_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached session data"""
        key = self._make_key(session_id, partner_id)
        try:
            data = self.redis_client.get(key)
            if data:
                # Refresh TTL on access (session is still active)
                self.redis_client.expire(key, self.ttl_seconds)
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis cache error: {e}")
            return None
    
    def delete(self, session_id: str, partner_id: str) -> bool:
        """Delete cached session"""
        key = self._make_key(session_id, partner_id)
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Redis cache error: {e}")
            return False
    
    def delete_all_partner_sessions(self, partner_id: str) -> int:
        """Delete all sessions for a partner (for testing/cleanup)"""
        pattern = f"{self.key_prefix}{partner_id}:*"
        deleted = 0
        try:
            for key in self.redis_client.scan_iter(pattern):
                self.redis_client.delete(key)
                deleted += 1
            return deleted
        except Exception as e:
            print(f"Redis cache error: {e}")
            return deleted


# ============================================================================
# POSTGRESQL PERSISTENCE LAYER
# ============================================================================

Base = declarative_base()


class SessionModel(Base):
    """PostgreSQL table for conversation sessions"""
    __tablename__ = "conversation_sessions"
    
    id = Column(String(64), primary_key=True)  # session_id
    partner_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    metadata = Column(JSON, default={})
    
    # Relationships
    turns = relationship("TurnModel", back_populates="session", cascade="all, delete-orphan")
    
    # Multi-tenant composite index for fast lookups
    __table_args__ = (
        Index('idx_partner_user', 'partner_id', 'user_id'),
        Index('idx_partner_session', 'partner_id', 'id'),
    )


class TurnModel(Base):
    """PostgreSQL table for conversation turns"""
    __tablename__ = "conversation_turns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("conversation_sessions.id"), nullable=False)
    
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    response_id = Column(String(128), nullable=False, index=True)  # OpenAI response ID
    
    citations = Column(JSON, default=[])  # List of citation objects
    
    # Token metrics
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    model = Column(String(64), nullable=False)
    
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    session = relationship("SessionModel", back_populates="turns")
    
    # Index for fast retrieval by session
    __table_args__ = (
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
    )


class PostgresSessionStorage(SessionStorageInterface):
    """
    PostgreSQL-based persistent session storage.
    
    Provides full CRUD operations with multi-tenant isolation
    and support for analytics queries.
    """
    
    def __init__(self, database_url: str = "postgresql://localhost/shopping_assistant"):
        """
        Initialize PostgreSQL storage.
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def create_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Create a new session in database.
        
        Args:
            session_data: Dictionary containing session_id, partner_id, user_id, metadata
        """
        db = self.SessionLocal()
        try:
            session = SessionModel(
                id=session_data["session_id"],
                partner_id=session_data["partner_id"],
                user_id=session_data["user_id"],
                metadata=session_data.get("metadata", {})
            )
            db.add(session)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            db.close()
    
    def get_session(self, session_id: str, partner_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session with multi-tenant isolation.
        
        CRITICAL: Always filter by BOTH session_id AND partner_id
        to prevent Partner A from accessing Partner B's data.
        """
        db = self.SessionLocal()
        try:
            session = db.query(SessionModel).filter(
                SessionModel.id == session_id,
                SessionModel.partner_id == partner_id  # Multi-tenant isolation
            ).first()
            
            if not session:
                return None
            
            # Convert to dictionary with turns
            turns = []
            for turn in session.turns:
                turns.append({
                    "user_message": turn.user_message,
                    "assistant_response": turn.assistant_response,
                    "response_id": turn.response_id,
                    "citations": turn.citations,
                    "metrics": {
                        "prompt_tokens": turn.prompt_tokens,
                        "completion_tokens": turn.completion_tokens,
                        "total_tokens": turn.total_tokens,
                        "estimated_cost": turn.estimated_cost,
                        "model": turn.model
                    },
                    "timestamp": turn.timestamp.isoformat()
                })
            
            return {
                "session_id": session.id,
                "partner_id": session.partner_id,
                "user_id": session.user_id,
                "turns": turns,
                "created_at": session.created_at.isoformat(),
                "last_updated": session.last_updated.isoformat(),
                "metadata": session.metadata
            }
        finally:
            db.close()
    
    def update_session(self, session_id: str, partner_id: str, updates: Dict[str, Any]) -> bool:
        """Update session metadata"""
        db = self.SessionLocal()
        try:
            session = db.query(SessionModel).filter(
                SessionModel.id == session_id,
                SessionModel.partner_id == partner_id
            ).first()
            
            if not session:
                return False
            
            if "metadata" in updates:
                session.metadata = updates["metadata"]
            
            session.last_updated = datetime.utcnow()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            db.close()
    
    def add_turn(self, session_id: str, partner_id: str, turn_data: Dict[str, Any]) -> bool:
        """
        Add a conversation turn to session.
        
        Args:
            turn_data: Dictionary containing user_message, assistant_response, 
                      response_id, citations, metrics
        """
        db = self.SessionLocal()
        try:
            # Verify session exists and belongs to partner
            session = db.query(SessionModel).filter(
                SessionModel.id == session_id,
                SessionModel.partner_id == partner_id
            ).first()
            
            if not session:
                return False
            
            metrics = turn_data.get("metrics", {})
            turn = TurnModel(
                session_id=session_id,
                user_message=turn_data["user_message"],
                assistant_response=turn_data["assistant_response"],
                response_id=turn_data["response_id"],
                citations=turn_data.get("citations", []),
                prompt_tokens=metrics.get("prompt_tokens", 0),
                completion_tokens=metrics.get("completion_tokens", 0),
                total_tokens=metrics.get("total_tokens", 0),
                estimated_cost=metrics.get("cost", 0.0),
                model=metrics.get("model", "unknown")
            )
            
            db.add(turn)
            session.last_updated = datetime.utcnow()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            db.close()
    
    def delete_session(self, session_id: str, partner_id: str) -> bool:
        """
        Delete session and all associated turns.
        GDPR compliance: Right to be forgotten.
        """
        db = self.SessionLocal()
        try:
            session = db.query(SessionModel).filter(
                SessionModel.id == session_id,
                SessionModel.partner_id == partner_id
            ).first()
            
            if not session:
                return False
            
            db.delete(session)  # Cascade deletes turns
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            db.close()
    
    def get_partner_analytics(self, partner_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics for a partner.
        
        Useful for dashboard showing:
        - Total conversations
        - Total cost
        - Average conversation length
        - Token usage
        """
        db = self.SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            sessions = db.query(SessionModel).filter(
                SessionModel.partner_id == partner_id,
                SessionModel.created_at >= cutoff_date
            ).all()
            
            total_sessions = len(sessions)
            total_turns = sum(len(s.turns) for s in sessions)
            total_cost = sum(
                sum(t.estimated_cost for t in s.turns)
                for s in sessions
            )
            total_tokens = sum(
                sum(t.total_tokens for t in s.turns)
                for s in sessions
            )
            
            return {
                "partner_id": partner_id,
                "period_days": days,
                "total_sessions": total_sessions,
                "total_turns": total_turns,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "avg_turns_per_session": total_turns / total_sessions if total_sessions > 0 else 0,
                "avg_cost_per_session": total_cost / total_sessions if total_sessions > 0 else 0
            }
        finally:
            db.close()


# ============================================================================
# HYBRID STORAGE: REDIS CACHE + POSTGRESQL PERSISTENCE
# ============================================================================

class HybridSessionStorage(SessionStorageInterface):
    """
    Production-ready storage combining Redis cache and PostgreSQL persistence.
    
    Read path: Check Redis → if miss, read from PostgreSQL → cache in Redis
    Write path: Write to PostgreSQL → update Redis cache
    
    This provides:
    - Fast reads (Redis O(1) lookup)
    - Persistent storage (PostgreSQL)
    - Durability (writes go to PostgreSQL)
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        database_url: str = "postgresql://localhost/shopping_assistant",
        cache_ttl: int = 3600
    ):
        self.cache = RedisSessionCache(redis_url, ttl_seconds=cache_ttl)
        self.db = PostgresSessionStorage(database_url)
    
    def create_session(self, session_data: Dict[str, Any]) -> bool:
        """Create in PostgreSQL and cache in Redis"""
        success = self.db.create_session(session_data)
        if success:
            self.cache.set(
                session_data["session_id"],
                session_data["partner_id"],
                session_data
            )
        return success
    
    def get_session(self, session_id: str, partner_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session with cache-aside pattern.
        
        1. Check Redis cache
        2. If miss, query PostgreSQL
        3. Cache result in Redis
        """
        # Try cache first
        data = self.cache.get(session_id, partner_id)
        if data:
            return data
        
        # Cache miss - query database
        data = self.db.get_session(session_id, partner_id)
        if data:
            # Populate cache
            self.cache.set(session_id, partner_id, data)
        
        return data
    
    def update_session(self, session_id: str, partner_id: str, updates: Dict[str, Any]) -> bool:
        """Update in PostgreSQL and invalidate cache"""
        success = self.db.update_session(session_id, partner_id, updates)
        if success:
            # Invalidate cache to ensure consistency
            self.cache.delete(session_id, partner_id)
        return success
    
    def add_turn(self, session_id: str, partner_id: str, turn_data: Dict[str, Any]) -> bool:
        """Add turn to PostgreSQL and invalidate cache"""
        success = self.db.add_turn(session_id, partner_id, turn_data)
        if success:
            # Invalidate cache - next read will refresh from DB
            self.cache.delete(session_id, partner_id)
        return success
    
    def delete_session(self, session_id: str, partner_id: str) -> bool:
        """Delete from both PostgreSQL and Redis"""
        db_success = self.db.delete_session(session_id, partner_id)
        cache_success = self.cache.delete(session_id, partner_id)
        return db_success


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_storage_usage():
    """Demonstrate storage layer usage"""
    import uuid
    
    # Initialize hybrid storage
    storage = HybridSessionStorage(
        redis_url="redis://localhost:6379/0",
        database_url="postgresql://user:password@localhost/shopping_assistant"
    )
    
    # Create session
    session_id = str(uuid.uuid4())
    storage.create_session({
        "session_id": session_id,
        "partner_id": "partner_fashionhub",
        "user_id": "user_12345",
        "metadata": {"source": "web", "country": "US"}
    })
    
    # Add conversation turn
    storage.add_turn(session_id, "partner_fashionhub", {
        "user_message": "I need a laptop",
        "assistant_response": "I can help! What's your budget?",
        "response_id": "resp_abc123",
        "citations": [],
        "metrics": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "cost": 0.0005,
            "model": "gpt-4o"
        }
    })
    
    # Retrieve session (fast - from Redis cache)
    session_data = storage.get_session(session_id, "partner_fashionhub")
    print(f"Retrieved session: {session_data['session_id']}")
    print(f"Turns: {len(session_data['turns'])}")


if __name__ == "__main__":
    # example_storage_usage()
    pass