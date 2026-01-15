"""
Complete Integration Example for Gemini Shopping Assistant

This module demonstrates how to use the Gemini shopping assistant with
session storage for a production-ready shopping assistant system.

Features:
- Multi-turn conversations with Gemini API
- Persistent session storage
- Product discovery and recommendations
- Multi-tenant support
- Error handling and logging
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

from gemini_shopping_assistant import (
    GeminiShoppingAssistant,
    ConversationRole,
    Product
)
from gemini_session_storage import (
    GeminiMemoryStorage,
    GeminiHybridSessionStorage
)


# ============================================================================
# INTEGRATED SHOPPING SYSTEM
# ============================================================================

class IntegratedGeminiShoppingSystem:
    """
    Complete shopping system integrating Gemini assistant with session storage.
    
    This is the main orchestration class that handles:
    1. Conversation management with Gemini
    2. Session persistence
    3. Multi-tenant support
    4. User session tracking
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        use_persistent_storage: bool = False,
        redis_url: str = "redis://localhost:6379/0",
        database_url: str = "postgresql://localhost/gemini_shopping"
    ):
        """
        Initialize the integrated shopping system.
        
        Args:
            gemini_api_key: Google Gemini API key
            use_persistent_storage: Use Redis+PostgreSQL (requires dependencies)
            redis_url: Redis connection URL
            database_url: PostgreSQL connection URL
        """
        # Initialize Gemini assistant
        self.assistant = GeminiShoppingAssistant(api_key=gemini_api_key)
        
        # Initialize storage
        if use_persistent_storage:
            self.storage = GeminiHybridSessionStorage(
                redis_url=redis_url,
                database_url=database_url,
                enable_cache=True,
                enable_db=False  # Set to True if PostgreSQL is available
            )
        else:
            self.storage = GeminiMemoryStorage()
        
        # User session tracking
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [conversation_ids]
        
        print("✓ Gemini Shopping System initialized")
        print(f"  - Gemini Assistant: Ready")
        print(f"  - Storage: {type(self.storage).__name__}")
    
    def start_shopping_session(
        self,
        user_id: str,
        partner_id: str = "default",
        session_title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start a new shopping conversation session.
        
        Args:
            user_id: Unique user identifier
            partner_id: Partner/store identifier for multi-tenant support
            session_title: Optional title for the session
            metadata: Optional metadata to store with session
        
        Returns:
            Conversation ID
        """
        # Start conversation with assistant
        conversation_id = self.assistant.start_conversation(
            user_id=user_id,
            partner_id=partner_id,
            metadata=metadata or {}
        )
        
        # Create storage record
        conversation_data = {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'partner_id': partner_id,
            'title': session_title or f"Shopping Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        self.storage.create_conversation(conversation_data)
        
        # Track in user sessions
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = []
        self.user_sessions[user_id].append(conversation_id)
        
        return conversation_id
    
    def ask_product_question(
        self,
        question: str,
        conversation_id: str,
        user_id: str,
        partner_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Ask a product question within an existing conversation.
        
        Args:
            question: The user's question
            conversation_id: ID of the conversation
            user_id: User identifier
            partner_id: Partner identifier
        
        Returns:
            Response with products and metadata
        """
        # Ask the assistant
        response = self.assistant.ask(
            question=question,
            conversation_id=conversation_id,
            user_id=user_id,
            partner_id=partner_id
        )
        
        # Store message in persistent storage
        message_data = {
            'role': 'user',
            'content': question,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.storage.add_message(conversation_id, partner_id, message_data)
        
        # Store assistant response
        response_data = {
            'role': 'model',
            'content': response.get('response', ''),
            'products': response.get('products', []),
            'timestamp': datetime.utcnow().isoformat()
        }
        self.storage.add_message(conversation_id, partner_id, response_data)
        
        # Update conversation metadata
        context = self.assistant.get_conversation_context(conversation_id)
        if context:
            self.storage.update_conversation(
                conversation_id,
                partner_id,
                {
                    'updated_at': datetime.utcnow().isoformat(),
                    'message_count': len(context['messages']),
                    'products_found': len(context['products_found'])
                }
            )
        
        return response
    
    def get_session_details(
        self,
        conversation_id: str,
        partner_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get full details of a conversation session.
        
        Args:
            conversation_id: The conversation ID
            partner_id: Partner identifier
        
        Returns:
            Complete session details including messages and products
        """
        # Get from persistent storage
        storage_data = self.storage.get_conversation(conversation_id, partner_id)
        
        # Get from assistant's in-memory context
        assistant_data = self.assistant.get_conversation_context(conversation_id)
        
        if assistant_data:
            return {
                **storage_data or {},
                **assistant_data,
                'messages': assistant_data.get('messages', []),
                'products_found': assistant_data.get('products_found', [])
            }
        
        return storage_data
    
    def list_user_sessions(
        self,
        user_id: str,
        partner_id: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        List all conversations for a user.
        
        Args:
            user_id: User identifier
            partner_id: Partner identifier
        
        Returns:
            List of conversation summaries
        """
        # Get from storage
        storage_sessions = self.storage.list_conversations(partner_id, user_id)
        
        # Get from assistant's in-memory tracking
        assistant_sessions = self.assistant.get_active_conversations(user_id)
        
        # Merge and deduplicate
        sessions_dict = {}
        for session in storage_sessions + assistant_sessions:
            conv_id = session['conversation_id']
            sessions_dict[conv_id] = session
        
        return list(sessions_dict.values())
    
    def end_session(
        self,
        conversation_id: str,
        partner_id: str,
        save_transcript: bool = True
    ) -> bool:
        """
        End a shopping session.
        
        Args:
            conversation_id: The conversation ID
            partner_id: Partner identifier
            save_transcript: Whether to save the transcript
        
        Returns:
            True if successful
        """
        # Save transcript if requested
        if save_transcript:
            context = self.assistant.get_conversation_context(conversation_id)
            if context:
                # In production, save to file or database
                transcript = {
                    'conversation_id': conversation_id,
                    'ended_at': datetime.utcnow().isoformat(),
                    'messages': context['messages'],
                    'products_found': context['products_found'],
                    'metrics': context['metrics']
                }
                # TODO: Save transcript to permanent storage
        
        # Clean up in-memory storage
        self.assistant.end_conversation(conversation_id)
        
        # Clean up persistent storage
        self.storage.delete_conversation(conversation_id, partner_id)
        
        return True
    
    def search_products(
        self,
        query: str,
        user_id: str,
        partner_id: str = "default",
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Quick product search (starts a new conversation if needed).
        
        Args:
            query: Product search query
            user_id: User identifier
            partner_id: Partner identifier
            max_results: Maximum number of products to return
        
        Returns:
            List of matching products
        """
        # Start a quick session
        conv_id = self.start_shopping_session(
            user_id=user_id,
            partner_id=partner_id,
            session_title=f"Quick Search: {query}"
        )
        
        # Ask the question
        response = self.ask_product_question(
            question=f"Find {max_results} best options for: {query}",
            conversation_id=conv_id,
            user_id=user_id,
            partner_id=partner_id
        )
        
        # Return products (limit to max_results)
        products = response.get('products', [])[:max_results]
        
        # Clean up quick session
        self.end_session(conv_id, partner_id, save_transcript=False)
        
        return products


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_detailed_shopping_session():
    """
    Detailed example showing a complete shopping conversation flow.
    """
    print("\n" + "=" * 70)
    print("GEMINI SHOPPING ASSISTANT - DETAILED SESSION EXAMPLE")
    print("=" * 70)
    
    # Initialize the system
    system = IntegratedGeminiShoppingSystem(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        use_persistent_storage=False
    )
    
    # User and partner info
    user_id = "customer_001"
    partner_id = "electronics_store"
    
    # Start a shopping session
    print(f"\n1. Starting shopping session for user: {user_id}")
    conv_id = system.start_shopping_session(
        user_id=user_id,
        partner_id=partner_id,
        session_title="Headphones Shopping",
        metadata={"budget": "$200", "use_case": "travel"}
    )
    print(f"   ✓ Session ID: {conv_id}")
    
    # First question - find products with constraints
    print(f"\n2. First question: Find noise-canceling headphones under $200")
    print("   Asking Gemini...")
    response1 = system.ask_product_question(
        question="I need noise-canceling headphones under $200 for travel. What are the best options?",
        conversation_id=conv_id,
        user_id=user_id,
        partner_id=partner_id
    )
    
    print(f"   Response: {response1['response'][:200]}...")
    if response1.get('products'):
        print(f"   Found {len(response1['products'])} products:")
        for product in response1['products'][:3]:
            print(f"     - {product['name']}: ${product['price']}")
    
    # Follow-up question - asking for comparison
    print(f"\n3. Follow-up question: Which one is best for travel?")
    print("   Asking Gemini (with conversation history)...")
    response2 = system.ask_product_question(
        question="Which one from these would be best for frequent travelers? Consider portability and battery life.",
        conversation_id=conv_id,
        user_id=user_id,
        partner_id=partner_id
    )
    
    print(f"   Response: {response2['response'][:200]}...")
    
    # Get full session details
    print(f"\n4. Session Summary:")
    session = system.get_session_details(conv_id, partner_id)
    if session:
        print(f"   Total messages: {session.get('message_count', 0)}")
        print(f"   Products found: {session.get('products_found', 0)}")
        print(f"   Session created: {session.get('created_at', 'N/A')[:19]}")
        print(f"   Last updated: {session.get('updated_at', 'N/A')[:19]}")
    
    # List user sessions
    print(f"\n5. User's sessions:")
    sessions = system.list_user_sessions(user_id, partner_id)
    print(f"   Total active sessions: {len(sessions)}")
    for sess in sessions:
        print(f"     - {sess.get('conversation_id', 'N/A')[:8]}... ({sess.get('title', 'Untitled')})")
    
    # End the session
    print(f"\n6. Ending session...")
    system.end_session(conv_id, partner_id, save_transcript=True)
    print(f"   ✓ Session ended and archived")


def example_quick_product_search():
    """
    Quick example showing a single product search.
    """
    print("\n" + "=" * 70)
    print("GEMINI SHOPPING ASSISTANT - QUICK SEARCH EXAMPLE")
    print("=" * 70)
    
    system = IntegratedGeminiShoppingSystem(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        use_persistent_storage=False
    )
    
    # Quick search for gaming laptops
    print("\n🔍 Searching for: Gaming laptops under $1500")
    products = system.search_products(
        query="Gaming laptops under $1500",
        user_id="user_123",
        partner_id="laptop_store",
        max_results=5
    )
    
    if products:
        print(f"\n📦 Found {len(products)} products:\n")
        for i, product in enumerate(products, 1):
            print(f"{i}. {product['name']}")
            print(f"   Price: ${product['price']}")
            if product.get('description'):
                print(f"   {product['description']}")
            if product.get('url'):
                print(f"   Link: {product['url']}")
            print()
    else:
        print("No products found.")


def example_multi_tenant_support():
    """
    Example showing multi-tenant support with different stores.
    """
    print("\n" + "=" * 70)
    print("GEMINI SHOPPING ASSISTANT - MULTI-TENANT EXAMPLE")
    print("=" * 70)
    
    system = IntegratedGeminiShoppingSystem(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        use_persistent_storage=False
    )
    
    user_id = "shared_customer"
    
    # Session 1: Electronics store
    print(f"\n1️⃣  Electronics Store Session")
    conv1 = system.start_shopping_session(user_id, partner_id="electronics_store")
    response1 = system.ask_product_question(
        "Show me budget smartphones",
        conv1,
        user_id,
        "electronics_store"
    )
    print(f"   Found {len(response1.get('products', []))} products")
    
    # Session 2: Fashion store (same user, different partner)
    print(f"\n2️⃣  Fashion Store Session")
    conv2 = system.start_shopping_session(user_id, partner_id="fashion_store")
    response2 = system.ask_product_question(
        "Show me winter jackets",
        conv2,
        user_id,
        "fashion_store"
    )
    print(f"   Found {len(response2.get('products', []))} products")
    
    # List all sessions for the user (per partner)
    print(f"\n3️⃣  User's sessions by store:")
    for partner in ["electronics_store", "fashion_store"]:
        sessions = system.list_user_sessions(user_id, partner)
        print(f"   {partner}: {len(sessions)} session(s)")


if __name__ == "__main__":
    # Run examples
    try:
        example_detailed_shopping_session()
        # example_quick_product_search()
        # example_multi_tenant_support()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("  1. Set GEMINI_API_KEY environment variable")
        print("  2. Installed google-generativeai: pip install google-generativeai")
