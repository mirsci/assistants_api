#!/usr/bin/env python3
"""
Quick Start Demo for Gemini Shopping Assistant

Run this script to test the shopping assistant with example queries.

Usage:
    python gemini_demo.py

Requirements:
    - GEMINI_API_KEY environment variable set
    - google-generativeai installed: pip install google-generativeai
"""

import os
import sys
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gemini_shopping_assistant import GeminiShoppingAssistant
from gemini_integrated_system import IntegratedGeminiShoppingSystem


def demo_basic_assistant():
    """Demo: Basic shopping assistant functionality"""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Shopping Assistant")
    print("=" * 70)
    
    try:
        # Initialize
        print("\n📱 Initializing Gemini Shopping Assistant...")
        assistant = GeminiShoppingAssistant(
            api_key=os.getenv("GEMINI_API_KEY")
        )
        print("   ✓ Ready!")
        
        # Start conversation
        print("\n💬 Starting new conversation...")
        conv_id = assistant.start_conversation(user_id="demo_user")
        print(f"   Conversation ID: {conv_id[:8]}...")
        
        # Question 1
        print("\n❓ Question: 'Find noise-canceling headphones under $200'")
        print("   Thinking...")
        response1 = assistant.ask(
            "Find noise-canceling headphones under $200",
            conversation_id=conv_id
        )
        
        print(f"\n📝 Assistant Response:")
        print(response1['response'][:500] + "..." if len(response1['response']) > 500 else response1['response'])
        
        if response1.get('products'):
            print(f"\n🛍️  Products Found: {len(response1['products'])}")
            for i, product in enumerate(response1['products'][:3], 1):
                print(f"   {i}. {product['name']}")
                print(f"      Price: ${product['price']}")
                if product.get('url'):
                    print(f"      Link: {product['url']}")
        
        # Question 2 (with history)
        print("\n\n❓ Follow-up: 'Which one is best for travel?'")
        print("   Thinking (with conversation context)...")
        response2 = assistant.ask(
            "Which one is best for travel considering portability and battery life?",
            conversation_id=conv_id
        )
        
        print(f"\n📝 Assistant Response:")
        print(response2['response'][:500] + "..." if len(response2['response']) > 500 else response2['response'])
        
        # Show conversation history
        print("\n\n📋 Conversation History:")
        history = assistant.get_conversation_history(conv_id)
        print(f"   Total messages: {len(history)}")
        for i, msg in enumerate(history, 1):
            role = "👤 You" if msg['role'] == 'user' else "🤖 Assistant"
            content = msg['content'][:60] + "..." if len(msg['content']) > 60 else msg['content']
            print(f"   {i}. {role}: {content}")
        
        print("\n✓ Demo 1 Complete!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def demo_integrated_system():
    """Demo: Integrated system with session management"""
    print("\n" + "=" * 70)
    print("DEMO 2: Integrated Shopping System")
    print("=" * 70)
    
    try:
        # Initialize
        print("\n🛒 Initializing Integrated Shopping System...")
        system = IntegratedGeminiShoppingSystem(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            use_persistent_storage=False
        )
        print("   ✓ Ready!")
        
        # Start shopping session
        user_id = "customer_001"
        partner_id = "tech_store"
        
        print(f"\n🎯 Starting shopping session")
        print(f"   User: {user_id}")
        print(f"   Store: {partner_id}")
        
        conv_id = system.start_shopping_session(
            user_id=user_id,
            partner_id=partner_id,
            session_title="Gaming Setup Shopping"
        )
        print(f"   Session ID: {conv_id[:8]}...\n")
        
        # Shopping questions
        questions = [
            "What are the best gaming monitors under $400?",
            "Which one has the best response time for competitive gaming?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"\n❓ Question {i}: '{question}'")
            print("   Thinking...")
            
            response = system.ask_product_question(
                question=question,
                conversation_id=conv_id,
                user_id=user_id,
                partner_id=partner_id
            )
            
            print(f"\n📝 Response: {response['response'][:400]}...")
            
            if response.get('products'):
                print(f"🛍️  Found {len(response['products'])} products")
        
        # Get session summary
        print("\n\n📊 Session Summary:")
        session = system.get_session_details(conv_id, partner_id)
        if session:
            print(f"   Title: {session.get('title', 'N/A')}")
            print(f"   Messages: {session.get('message_count', 0)}")
            print(f"   Products discussed: {len(session.get('products_found', []))}")
            
            if session.get('products_found'):
                print(f"\n   All products mentioned:")
                for product in session['products_found'][:3]:
                    print(f"     - {product['name']}: ${product['price']}")
                if len(session['products_found']) > 3:
                    print(f"     ... and {len(session['products_found']) - 3} more")
        
        print("\n✓ Demo 2 Complete!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def demo_quick_search():
    """Demo: Quick product search"""
    print("\n" + "=" * 70)
    print("DEMO 3: Quick Product Search")
    print("=" * 70)
    
    try:
        print("\n🔍 Initializing search...")
        system = IntegratedGeminiShoppingSystem(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            use_persistent_storage=False
        )
        
        queries = [
            ("Wireless earbuds with active noise cancellation under $150", 3),
            ("Budget laptop for web development under $600", 2),
        ]
        
        for query, max_results in queries:
            print(f"\n🔎 Searching: '{query}'")
            print(f"   (Max results: {max_results})")
            
            products = system.search_products(
                query=query,
                user_id="shopper",
                max_results=max_results
            )
            
            if products:
                print(f"\n   ✓ Found {len(products)} product(s):")
                for i, product in enumerate(products, 1):
                    print(f"   {i}. {product['name']}")
                    print(f"      💵 ${product['price']}")
                    if product.get('description'):
                        print(f"      📝 {product['description'][:80]}...")
            else:
                print("   No products found.")
        
        print("\n✓ Demo 3 Complete!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def show_menu():
    """Show interactive menu"""
    print("\n" + "=" * 70)
    print("🛒 GEMINI SHOPPING ASSISTANT - INTERACTIVE DEMO")
    print("=" * 70)
    print("\nWhat would you like to demo?")
    print("\n1. Basic Assistant (simple Q&A)")
    print("2. Integrated System (full session management)")
    print("3. Quick Search (one-shot searches)")
    print("4. Run All Demos")
    print("5. Custom Query (ask your own question)")
    print("0. Exit")
    
    choice = input("\nEnter your choice (0-5): ").strip()
    return choice


def custom_query_mode():
    """Interactive mode for custom queries"""
    print("\n" + "=" * 70)
    print("💬 CUSTOM QUERY MODE")
    print("=" * 70)
    print("\nEnter your shopping questions. Type 'exit' to quit.\n")
    
    try:
        system = IntegratedGeminiShoppingSystem(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            use_persistent_storage=False
        )
        
        # Start a conversation
        conv_id = system.start_shopping_session(
            user_id="interactive_user",
            partner_id="shopping"
        )
        
        while True:
            question = input("\n❓ Your question: ").strip()
            
            if question.lower() == 'exit':
                print("\nGoodbye! 👋")
                break
            
            if not question:
                print("Please enter a question.")
                continue
            
            print("\n🤔 Thinking...")
            response = system.ask_product_question(
                question=question,
                conversation_id=conv_id,
                user_id="interactive_user",
                partner_id="shopping"
            )
            
            print(f"\n🤖 Assistant:\n{response['response']}")
            
            if response.get('products'):
                print(f"\n🛍️  Found {len(response['products'])} product(s):")
                for product in response['products']:
                    print(f"\n   {product['name']}")
                    print(f"   Price: ${product['price']}")
                    if product.get('url'):
                        print(f"   Link: {product['url']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    """Main demo runner"""
    # Check for API key
    if not os.getenv("GEMINI_API_KEY"):
        print("\n❌ Error: GEMINI_API_KEY environment variable not set!")
        print("\nTo get started:")
        print("1. Visit https://ai.google.dev/")
        print("2. Get an API key")
        print("3. Export it: export GEMINI_API_KEY='your-key-here'")
        sys.exit(1)
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            demo_basic_assistant()
        elif choice == '2':
            demo_integrated_system()
        elif choice == '3':
            demo_quick_search()
        elif choice == '4':
            demo_basic_assistant()
            demo_integrated_system()
            demo_quick_search()
        elif choice == '5':
            custom_query_mode()
        elif choice == '0':
            print("\n👋 Thanks for using Gemini Shopping Assistant!\n")
            break
        else:
            print("\n❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
