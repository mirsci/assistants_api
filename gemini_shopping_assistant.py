"""
Shopping Assistant with Google Gemini API

This module provides a complete shopping assistant implementation using Google's
Gemini API for multi-turn conversations. It supports:
- Multi-turn product discovery conversations
- Product search with links, images, and prices
- Session-based conversation history
- Multi-tenant support

Example usage:
    assistant = GeminiShoppingAssistant(api_key="your-gemini-api-key")
    conversation_id = assistant.start_conversation()
    response = assistant.ask("Find noise-canceling headphones under $200")
    follow_up = assistant.ask("Which one is best for travel?", conversation_id)
"""

import os
import json
import uuid
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
import re

import google.generativeai as genai


# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

class ModelConfig:
    """Google Gemini model configurations"""
    GEMINI_2_FLASH = "gemini-2.0-flash"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    
    # Default model for shopping assistant
    DEFAULT_MODEL = GEMINI_2_FLASH


class ConversationRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Product:
    """Represents a product with details"""
    name: str
    price: float
    currency: str = "USD"
    url: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_formatted_string(self) -> str:
        """Format product for display"""
        output = f"**{self.name}**\n"
        output += f"Price: ${self.price:.2f} {self.currency}\n"
        
        if self.rating:
            output += f"Rating: {self.rating}/5⭐\n"
        
        if self.description:
            output += f"Description: {self.description}\n"
        
        if self.url:
            output += f"Link: {self.url}\n"
        
        if self.image_url:
            output += f"Image: {self.image_url}\n"
        
        if self.source:
            output += f"Source: {self.source}\n"
        
        return output


@dataclass
class ConversationMessage:
    """Represents a single message in the conversation"""
    role: ConversationRole
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    products: List[Product] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "products": [p.to_dict() for p in self.products]
        }
    
    def to_gemini_format(self) -> Dict[str, str]:
        """Convert to Gemini API format"""
        return {
            "role": "user" if self.role == ConversationRole.USER else "model",
            "parts": [{"text": self.content}]
        }


@dataclass
class ResponseMetrics:
    """Tracks token usage for a response"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class ConversationContext:
    """Manages conversation state and history"""
    conversation_id: str
    user_id: str
    partner_id: str
    messages: List[ConversationMessage] = field(default_factory=list)
    products_found: List[Product] = field(default_factory=list)
    metrics: List[ResponseMetrics] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: ConversationRole, content: str, products: List[Product] = None):
        """Add a message to conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            products=products or []
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history in Gemini format (excluding system messages)"""
        history = []
        for msg in self.messages:
            if msg.role != ConversationRole.SYSTEM:
                history.append(msg.to_gemini_format())
        return history
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "partner_id": self.partner_id,
            "messages": [m.to_dict() for m in self.messages],
            "products_found": [p.to_dict() for p in self.products_found],
            "metrics": [m.to_dict() for m in self.metrics],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }


# ============================================================================
# GEMINI SHOPPING ASSISTANT
# ============================================================================

class GeminiShoppingAssistant:
    """
    Shopping assistant using Google Gemini API.
    
    Provides multi-turn conversation support for product discovery with
    product details including links, images, and prices.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = ModelConfig.DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        Initialize the Gemini shopping assistant.
        
        Args:
            api_key: Google Gemini API key (defaults to GEMINI_API_KEY env var)
            model: Model to use (default: gemini-2.0-flash)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided or set in environment")
        
        genai.configure(api_key=self.api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize the generative model
        self.client = genai.GenerativeModel(
            model_name=model,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )
        
        # In-memory session storage (use database in production)
        self.conversations: Dict[str, ConversationContext] = {}
        
        # System prompt for shopping assistant
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the shopping assistant"""
        return """You are an expert shopping assistant helping users find the best products for their needs.

Your responsibilities:
1. Listen carefully to the user's requirements (budget, features, use case)
2. Search for and recommend relevant products with specific details
3. Provide product information in a structured format including:
   - Product name
   - Price in USD
   - Direct product links (real or realistic URLs)
   - Product images (real or realistic image URLs)
   - Key features and specifications
   - Customer ratings if available
   - Comparison with alternatives

4. Ask clarifying questions to better understand user needs
5. Provide personalized recommendations based on previous context

When recommending products, always format them as:
PRODUCT: [Name]
PRICE: $[Amount]
URL: [Link]
IMAGE: [Image URL]
DESCRIPTION: [Key features]
RATING: [Rating if available]

Be helpful, accurate, and concise. Remember the context from previous messages in the conversation."""
    
    def start_conversation(
        self,
        user_id: str,
        partner_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new shopping conversation.
        
        Args:
            user_id: Unique user identifier
            partner_id: Multi-tenant partner identifier
            metadata: Optional metadata to store with conversation
        
        Returns:
            Conversation ID for tracking
        """
        conversation_id = str(uuid.uuid4())
        
        context = ConversationContext(
            conversation_id=conversation_id,
            user_id=user_id,
            partner_id=partner_id,
            metadata=metadata or {}
        )
        
        self.conversations[conversation_id] = context
        return conversation_id
    
    def ask(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        user_id: str = "default",
        partner_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Ask a question in the shopping assistant.
        
        Args:
            question: User's question or request
            conversation_id: Existing conversation ID (creates new if not provided)
            user_id: User identifier
            partner_id: Partner identifier for multi-tenant support
        
        Returns:
            Dictionary with response, products, and metadata
        """
        # Create new conversation if needed
        if not conversation_id:
            conversation_id = self.start_conversation(user_id, partner_id)
        
        context = self.conversations[conversation_id]
        
        # Add user message to history
        context.add_message(ConversationRole.USER, question)
        
        # Build conversation history
        history = context.get_conversation_history()
        
        try:
            # Make API call to Gemini
            response = self.client.generate_content(
                [
                    {"text": self.system_prompt},
                    *history,
                    {"text": question}
                ],
                stream=False
            )
            
            assistant_response = response.text
            
            # Extract products from response
            products = self._extract_products(assistant_response)
            
            # Add products to context if found
            context.products_found.extend(products)
            
            # Add assistant message to history
            context.add_message(ConversationRole.ASSISTANT, assistant_response, products)
            
            # Track metrics
            metrics = ResponseMetrics(
                prompt_tokens=0,  # Gemini API doesn't expose token counts in standard API
                completion_tokens=0,
                total_tokens=0,
                model=self.model
            )
            context.metrics.append(metrics)
            
            return {
                "conversation_id": conversation_id,
                "response": assistant_response,
                "products": [p.to_dict() for p in products],
                "all_products": [p.to_dict() for p in context.products_found],
                "message_count": len(context.messages),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            # Handle API errors
            error_msg = f"Error communicating with Gemini API: {str(e)}"
            context.add_message(ConversationRole.ASSISTANT, error_msg)
            
            return {
                "conversation_id": conversation_id,
                "response": error_msg,
                "products": [],
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _extract_products(self, response_text: str) -> List[Product]:
        """
        Extract product information from assistant response.
        
        Parses the formatted product blocks from the response and creates
        Product objects.
        
        Args:
            response_text: The assistant's response text
        
        Returns:
            List of extracted Product objects
        """
        products = []
        
        # Pattern to match PRODUCT blocks
        product_pattern = r"PRODUCT:\s*([^\n]+)"
        price_pattern = r"PRICE:\s*\$?([\d,.]+)"
        url_pattern = r"URL:\s*([^\n]+)"
        image_pattern = r"IMAGE:\s*([^\n]+)"
        description_pattern = r"DESCRIPTION:\s*([^\n]+)"
        rating_pattern = r"RATING:\s*([\d.]+)"
        
        # Split response by PRODUCT markers
        product_blocks = response_text.split("PRODUCT:")
        
        for block in product_blocks[1:]:  # Skip the first split (before first PRODUCT)
            try:
                lines = block.strip().split("\n")
                
                # Extract fields
                product_data = {
                    "name": lines[0].strip() if lines else "Unknown",
                    "price": 0.0,
                    "currency": "USD",
                    "url": None,
                    "image_url": None,
                    "description": None,
                    "rating": None
                }
                
                # Parse each line
                for line in lines[1:]:
                    if line.startswith("PRICE:"):
                        try:
                            price_str = line.replace("PRICE:", "").replace("$", "").strip()
                            product_data["price"] = float(price_str.replace(",", ""))
                        except ValueError:
                            pass
                    elif line.startswith("URL:"):
                        product_data["url"] = line.replace("URL:", "").strip()
                    elif line.startswith("IMAGE:"):
                        product_data["image_url"] = line.replace("IMAGE:", "").strip()
                    elif line.startswith("DESCRIPTION:"):
                        product_data["description"] = line.replace("DESCRIPTION:", "").strip()
                    elif line.startswith("RATING:"):
                        try:
                            rating_str = line.replace("RATING:", "").strip()
                            product_data["rating"] = float(rating_str)
                        except ValueError:
                            pass
                
                # Create Product object if we have valid data
                if product_data["name"] and product_data["name"] != "Unknown":
                    products.append(Product(**product_data))
            
            except Exception as e:
                # Skip malformed product blocks
                continue
        
        return products
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get the full conversation history.
        
        Args:
            conversation_id: The conversation ID
        
        Returns:
            List of messages in the conversation
        """
        context = self.conversations.get(conversation_id)
        if not context:
            return []
        
        return [msg.to_dict() for msg in context.messages]
    
    def get_conversation_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the full conversation context.
        
        Args:
            conversation_id: The conversation ID
        
        Returns:
            Dictionary with complete conversation data
        """
        context = self.conversations.get(conversation_id)
        if not context:
            return None
        
        return context.to_dict()
    
    def end_conversation(self, conversation_id: str) -> bool:
        """
        End a conversation and clean up.
        
        Args:
            conversation_id: The conversation ID
        
        Returns:
            True if successful, False otherwise
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def get_active_conversations(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of active conversations.
        
        Args:
            user_id: Optional user ID to filter conversations
        
        Returns:
            List of conversation summaries
        """
        conversations = []
        
        for conv_id, context in self.conversations.items():
            if user_id and context.user_id != user_id:
                continue
            
            conversations.append({
                "conversation_id": conv_id,
                "user_id": context.user_id,
                "partner_id": context.partner_id,
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat(),
                "message_count": len(context.messages),
                "products_found": len(context.products_found)
            })
        
        return conversations


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_usage():
    """
    Example usage of the Gemini shopping assistant.
    """
    # Initialize assistant
    assistant = GeminiShoppingAssistant(
        api_key=os.getenv("GEMINI_API_KEY")
    )
    
    # Start a conversation
    conversation_id = assistant.start_conversation(
        user_id="user123",
        partner_id="store1"
    )
    
    print(f"Started conversation: {conversation_id}\n")
    
    # First question
    print("=" * 60)
    print("Question 1: Find noise-canceling headphones under $200")
    print("=" * 60)
    response1 = assistant.ask(
        "Find noise-canceling headphones under $200",
        conversation_id=conversation_id
    )
    
    print(f"\nAssistant: {response1['response']}\n")
    if response1.get('products'):
        print("Found Products:")
        for product in response1['products']:
            print(f"- {product['name']}: ${product['price']}")
    
    # Follow-up question
    print("\n" + "=" * 60)
    print("Question 2: Which one is best for travel?")
    print("=" * 60)
    response2 = assistant.ask(
        "Which one is best for travel?",
        conversation_id=conversation_id
    )
    
    print(f"\nAssistant: {response2['response']}\n")
    if response2.get('products'):
        print("Found Products:")
        for product in response2['products']:
            print(f"- {product['name']}: ${product['price']}")
    
    # Show conversation history
    print("\n" + "=" * 60)
    print("Full Conversation History")
    print("=" * 60)
    history = assistant.get_conversation_history(conversation_id)
    for i, msg in enumerate(history, 1):
        print(f"\nMessage {i}:")
        print(f"Role: {msg['role']}")
        print(f"Content: {msg['content'][:100]}...")


if __name__ == "__main__":
    example_usage()
