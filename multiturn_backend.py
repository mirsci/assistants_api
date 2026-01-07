"""
Multi-Turn Product Discovery Conversation Backend
Use Case 1: Shopping Assistant with OpenAI Responses API

This module provides the core conversation management for a shopping assistant
that handles multi-turn product discovery conversations using OpenAI's Responses API.

Key Features:
- Stateful conversation management using previous_response_id
- Product database integration
- Session isolation per user
- Token tracking and cost management
- Citation handling from web search
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import json

from openai import OpenAI


# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

class ModelConfig:
    """OpenAI model configurations"""
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_1 = "gpt-4.1"
    
    # Token costs per 1M tokens (as of Jan 2025)
    COSTS = {
        GPT_4O: {"input": 2.50, "output": 10.00},
        GPT_4O_MINI: {"input": 0.15, "output": 0.60},
        GPT_4_1: {"input": 5.00, "output": 15.00}
    }


class ConversationRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ConversationMessage:
    """Represents a single message in the conversation"""
    role: ConversationRole
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI API input format"""
        return {
            "role": self.role.value,
            "content": [{"type": "input_text", "text": self.content}]
        }


@dataclass
class Citation:
    """Represents a source citation from web search"""
    url: str
    title: str
    snippet: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResponseMetrics:
    """Tracks token usage and costs for a response"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    model: str
    
    @classmethod
    def from_usage(cls, usage: Any, model: str) -> 'ResponseMetrics':
        """Create from OpenAI usage object"""
        prompt_tokens = getattr(usage, 'prompt_tokens', 0)
        completion_tokens = getattr(usage, 'completion_tokens', 0)
        total_tokens = getattr(usage, 'total_tokens', 0)
        
        # Calculate cost
        cost_config = ModelConfig.COSTS.get(model, {"input": 0, "output": 0})
        estimated_cost = (
            (prompt_tokens / 1_000_000) * cost_config["input"] +
            (completion_tokens / 1_000_000) * cost_config["output"]
        )
        
        return cls(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            model=model
        )


@dataclass
class ConversationTurn:
    """Represents a complete conversation turn (user message + assistant response)"""
    user_message: str
    assistant_response: str
    response_id: str
    citations: List[Citation] = field(default_factory=list)
    metrics: Optional[ResponseMetrics] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_message": self.user_message,
            "assistant_response": self.assistant_response,
            "response_id": self.response_id,
            "citations": [c.to_dict() for c in self.citations],
            "metrics": asdict(self.metrics) if self.metrics else None,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ConversationSession:
    """Manages a complete conversation session for a user"""
    session_id: str
    user_id: str
    partner_id: str
    turns: List[ConversationTurn] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def turn_count(self) -> int:
        return len(self.turns)
    
    @property
    def last_response_id(self) -> Optional[str]:
        """Get the most recent response ID for chaining"""
        if self.turns:
            return self.turns[-1].response_id
        return None
    
    @property
    def total_cost(self) -> float:
        """Calculate total cost across all turns"""
        return sum(
            turn.metrics.estimated_cost 
            for turn in self.turns 
            if turn.metrics
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "partner_id": self.partner_id,
            "turn_count": self.turn_count,
            "total_cost": self.total_cost,
            "turns": [turn.to_dict() for turn in self.turns],
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata
        }


# ============================================================================
# CORE CONVERSATION MANAGER
# ============================================================================

class ProductDiscoveryConversationManager:
    """
    Manages multi-turn product discovery conversations using OpenAI Responses API.
    
    This class handles:
    - Stateful conversation management with previous_response_id
    - System instruction injection
    - Citation extraction from web search
    - Token/cost tracking
    - Session isolation per user/partner
    """
    
    SYSTEM_INSTRUCTIONS = """You are an expert shopping assistant helping customers discover the perfect products.

Your role:
- Ask clarifying questions to understand customer needs (budget, preferences, use cases)
- Provide personalized product recommendations based on conversation context
- Use web search to find current prices, availability, and reviews
- Include specific product links and pricing in your responses
- Compare products objectively when asked
- Be concise but informative

Guidelines:
- Always cite sources for prices and product information
- Ask ONE clarifying question at a time (don't overwhelm the customer)
- Recommend 2-4 products maximum per response
- Focus on helping the customer make an informed decision
- If a product is unavailable, suggest alternatives

Response format:
- Use natural, conversational language
- Include product names, key specs, and prices
- Provide direct links to products
- Cite review sources when mentioning ratings/reviews"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = ModelConfig.GPT_4O,
        enable_web_search: bool = True,
        max_output_tokens: int = 1000,
        temperature: float = 0.7
    ):
        """
        Initialize the conversation manager.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4o)
            enable_web_search: Enable web search tool (default: True)
            max_output_tokens: Maximum tokens in response (default: 1000)
            temperature: Sampling temperature (default: 0.7)
        """
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.enable_web_search = enable_web_search
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        
        # In-memory session storage (replace with Redis/PostgreSQL in production)
        self.sessions: Dict[str, ConversationSession] = {}
    
    def create_session(
        self,
        session_id: str,
        user_id: str,
        partner_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationSession:
        """
        Create a new conversation session.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            partner_id: Partner/tenant identifier for multi-tenancy
            metadata: Optional metadata (e.g., user preferences, context)
        
        Returns:
            ConversationSession object
        """
        session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            partner_id=partner_id,
            metadata=metadata or {}
        )
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve an existing session"""
        return self.sessions.get(session_id)
    
    def _extract_citations(self, response: Any) -> List[Citation]:
        """
        Extract citations from OpenAI response with web search.
        
        The Responses API with web_search tool returns citations in the
        output items. This method extracts them for easy access.
        """
        citations = []
        
        # Check if response has output items
        if not hasattr(response, 'output'):
            return citations
        
        for item in response.output:
            # Look for message items with annotations
            if hasattr(item, 'content'):
                for content_item in item.content:
                    if hasattr(content_item, 'annotations'):
                        for annotation in content_item.annotations:
                            if hasattr(annotation, 'url') and hasattr(annotation, 'title'):
                                citations.append(Citation(
                                    url=annotation.url,
                                    title=annotation.title,
                                    snippet=None  # Responses API doesn't provide snippets
                                ))
        
        return citations
    
    def _extract_output_text(self, response: Any) -> str:
        """
        Extract the text output from OpenAI response.
        
        The Responses API provides a convenient output_text property,
        but we also handle manual extraction for robustness.
        """
        # Try the convenient helper first
        if hasattr(response, 'output_text'):
            return response.output_text
        
        # Fallback: manually extract from output items
        text_parts = []
        if hasattr(response, 'output'):
            for item in response.output:
                if hasattr(item, 'content'):
                    for content_item in item.content:
                        if hasattr(content_item, 'text'):
                            text_parts.append(content_item.text)
        
        return "\n".join(text_parts)
    
    def send_message(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Send a message in an existing conversation and get response.
        
        This method implements the core multi-turn conversation logic:
        1. Retrieve existing session
        2. Use previous_response_id to maintain context
        3. Call OpenAI Responses API with web search
        4. Extract citations and metrics
        5. Store turn in session
        
        Args:
            session_id: Session identifier
            user_message: User's message
        
        Returns:
            Dictionary containing:
            - response: Assistant's response text
            - citations: List of citation objects
            - metrics: Token usage and cost
            - turn_count: Current turn number
        
        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Build tools configuration
        tools = []
        if self.enable_web_search:
            tools.append({"type": "web_search"})
        
        # Prepare API request parameters
        request_params = {
            "model": self.model,
            "input": [{"role": "user", "content": user_message}],
            "instructions": self.SYSTEM_INSTRUCTIONS,
            "tools": tools if tools else None,
            "max_output_tokens": self.max_output_tokens,
            "temperature": self.temperature,
            "store": True  # Enable storage for context persistence
        }
        
        # If this is not the first turn, use previous_response_id for context
        # This is THE KEY to stateful multi-turn conversations in Responses API
        if session.last_response_id:
            request_params["previous_response_id"] = session.last_response_id
        
        # Call OpenAI Responses API
        try:
            response = self.client.responses.create(**request_params)
        except Exception as e:
            # In production, implement proper error handling and retries
            raise RuntimeError(f"OpenAI API error: {str(e)}")
        
        # Extract response components
        assistant_response = self._extract_output_text(response)
        citations = self._extract_citations(response)
        metrics = ResponseMetrics.from_usage(response.usage, self.model)
        
        # Create and store the conversation turn
        turn = ConversationTurn(
            user_message=user_message,
            assistant_response=assistant_response,
            response_id=response.id,
            citations=citations,
            metrics=metrics
        )
        session.turns.append(turn)
        session.last_updated = datetime.utcnow()
        
        # Return structured response
        return {
            "response": assistant_response,
            "citations": [c.to_dict() for c in citations],
            "metrics": {
                "prompt_tokens": metrics.prompt_tokens,
                "completion_tokens": metrics.completion_tokens,
                "total_tokens": metrics.total_tokens,
                "cost": metrics.estimated_cost,
                "model": metrics.model
            },
            "turn_count": session.turn_count,
            "session_id": session_id
        }
    
    def get_conversation_history(
        self,
        session_id: str,
        max_turns: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Session identifier
            max_turns: Optional limit on number of turns to return
        
        Returns:
            Dictionary containing session data and conversation history
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        turns = session.turns
        if max_turns:
            turns = turns[-max_turns:]
        
        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "partner_id": session.partner_id,
            "turn_count": session.turn_count,
            "total_cost": session.total_cost,
            "turns": [turn.to_dict() for turn in turns],
            "created_at": session.created_at.isoformat(),
            "last_updated": session.last_updated.isoformat()
        }
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session (GDPR compliance - right to be forgotten).
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


# ============================================================================
# ALTERNATIVE: CONVERSATIONS API MANAGER
# ============================================================================

class ProductDiscoveryConversationsManager:
    """
    Alternative implementation using OpenAI Conversations API for server-managed state.
    
    The Conversations API provides persistent, server-side conversation storage,
    eliminating the need to manually track previous_response_id.
    
    Key differences from previous_response_id approach:
    - Conversations are stored on OpenAI servers indefinitely
    - No need to track response IDs manually
    - Automatic context management and truncation
    - Better for long-running conversations across sessions/devices
    - Requires creating a conversation object first
    
    Trade-offs:
    - Less control over what's stored
    - Data stored on OpenAI servers (privacy consideration)
    - Slightly more API calls (create conversation, add items)
    """
    
    SYSTEM_INSTRUCTIONS = ProductDiscoveryConversationManager.SYSTEM_INSTRUCTIONS
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = ModelConfig.GPT_4O,
        enable_web_search: bool = True
    ):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.enable_web_search = enable_web_search
        
        # Store mapping of session_id -> conversation_id
        self.session_mapping: Dict[str, str] = {}
    
    def create_session(
        self,
        session_id: str,
        user_id: str,
        partner_id: str,
        initial_message: str
    ) -> Dict[str, Any]:
        """
        Create a new conversation using Conversations API.
        
        Args:
            session_id: Your internal session ID
            user_id: User identifier
            partner_id: Partner identifier
            initial_message: First message from user
        
        Returns:
            Dictionary with conversation_id and first response
        """
        # Create conversation with initial message
        conversation = self.client.conversations.create(
            metadata={
                "session_id": session_id,
                "user_id": user_id,
                "partner_id": partner_id
            },
            items=[{
                "type": "message",
                "role": "user",
                "content": initial_message
            }]
        )
        
        # Store mapping
        self.session_mapping[session_id] = conversation.id
        
        # Generate first response using Responses API with conversation
        tools = [{"type": "web_search"}] if self.enable_web_search else []
        
        response = self.client.responses.create(
            model=self.model,
            conversation=conversation.id,
            instructions=self.SYSTEM_INSTRUCTIONS,
            tools=tools
        )
        
        return {
            "conversation_id": conversation.id,
            "response": response.output_text,
            "response_id": response.id
        }
    
    def send_message(
        self,
        session_id: str,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Send a message in an existing conversation.
        
        With Conversations API, we just pass the conversation ID,
        and OpenAI automatically includes all previous context.
        """
        conversation_id = self.session_mapping.get(session_id)
        if not conversation_id:
            raise ValueError(f"Session {session_id} not found")
        
        # Add user message to conversation
        self.client.conversations.items.create(
            conversation_id,
            items=[{
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": user_message}]
            }]
        )
        
        # Generate response
        tools = [{"type": "web_search"}] if self.enable_web_search else []
        
        response = self.client.responses.create(
            model=self.model,
            conversation=conversation_id,
            instructions=self.SYSTEM_INSTRUCTIONS,
            tools=tools
        )
        
        return {
            "response": response.output_text,
            "response_id": response.id
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_multi_turn_conversation():
    """
    Example demonstrating Use Case 1: Multi-Turn Product Discovery.
    
    This simulates a customer searching for a laptop through multiple turns.
    """
    import uuid
    
    # Initialize manager
    manager = ProductDiscoveryConversationManager(
        model=ModelConfig.GPT_4O,
        enable_web_search=True
    )
    
    # Create session
    session_id = str(uuid.uuid4())
    user_id = "user_12345"
    partner_id = "partner_fashionhub"
    
    manager.create_session(
        session_id=session_id,
        user_id=user_id,
        partner_id=partner_id,
        metadata={"source": "web_widget", "country": "US"}
    )
    
    print(f"Created session: {session_id}\n")
    
    # Simulate multi-turn conversation
    turns = [
        "I need a laptop for video editing",
        "Under $2000, either platform is fine",
        "I travel a lot, so portability matters",
        "Tell me more about the MacBook Pro"
    ]
    
    for i, user_message in enumerate(turns, 1):
        print(f"Turn {i}")
        print(f"USER: {user_message}")
        
        result = manager.send_message(session_id, user_message)
        
        print(f"ASSISTANT: {result['response'][:200]}...")
        print(f"Citations: {len(result['citations'])} sources")
        print(f"Cost: ${result['metrics']['cost']:.6f}")
        print(f"Tokens: {result['metrics']['total_tokens']}")
        print("-" * 80)
    
    # Get full history
    history = manager.get_conversation_history(session_id)
    print(f"\nTotal conversation cost: ${history['total_cost']:.4f}")
    print(f"Total turns: {history['turn_count']}")


if __name__ == "__main__":
    # This would be run in a test environment
    example_multi_turn_conversation()
    pass