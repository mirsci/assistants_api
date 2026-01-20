"""
Minimal Demo for SimpleGeminiShoppingAssistant

Usage:
    python gemini_simple_demo.py

Requires:
    - google-generativeai (pip install google-generativeai)
    - GEMINI_API_KEY environment variable set
"""

import os
from gemini_simple_shopping_assistant import SimpleGeminiShoppingAssistant

def print_products(products):
    """Helper function to print products from a response"""
    if products:
        print("\n📦 Products found:")
        for p in products:
            print(f"  • {p['name']} (${p['price']})" if p.get('price') else f"  • {p['name']}")
            if p.get('url'):
                print(f"    Link: {p['url']}")
            if p.get('image_url'):
                print(f"    Image: {p['image_url']}")
            if p.get('description'):
                print(f"    Description: {p['description']}")
            if p.get('rating'):
                print(f"    Rating: {p['rating']} ⭐")

def print_token_and_cost_info(response):
    """Helper function to print token usage and cost information"""
    if "tokens" in response:
        tokens = response["tokens"]
        print(f"\n📊 Token Usage (this turn):")
        print(f"  Input:  {tokens['input']} tokens")
        print(f"  Output: {tokens['output']} tokens")
        print(f"  Total:  {tokens['total']} tokens")
    
    if "cost" in response:
        cost = response["cost"]
        print(f"\n💰 Cost Information:")
        print(f"  This turn: ${cost['this_turn']:.6f}")
        print(f"  Conversation total: ${cost['conversation_total']:.6f}")

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Please set GEMINI_API_KEY environment variable.")
        exit(1)

    assistant = SimpleGeminiShoppingAssistant(api_key=api_key)
    conv_id = assistant.start_conversation(user_id="demo_user")

    print("\n" + "="*60)
    print("🛍️  GEMINI SHOPPING ASSISTANT - Multi-Turn Chat")
    print("="*60)
    print("Ask shopping questions (e.g., 'Find noise-canceling headphones under $200')")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    turn = 0
    while True:
        turn += 1
        question = input(f"You (Turn {turn}): ").strip()
        
        if not question:
            print("⚠️  Please enter a question.\n")
            continue
        
        if question.lower() in ['exit', 'quit', 'bye', 'goodbye', 'stats', 'summary']:
            if question.lower() in ['stats', 'summary']:
                # Show conversation summary before exiting
                stats = assistant.get_conversation_stats(conv_id)
                print("\n" + "="*60)
                print("📈 CONVERSATION SUMMARY")
                print("="*60)
                print(f"Total turns: {stats['turns']}")
                print(f"Total messages: {stats['message_count']}")
                print(f"\n📊 Token Usage (entire conversation):")
                print(f"  Input:  {stats['tokens']['input']} tokens")
                print(f"  Output: {stats['tokens']['output']} tokens")
                print(f"  Total:  {stats['tokens']['total']} tokens")
                print(f"\n📊 Tool Usage (entire conversation):")
                print(f"  Web Search: {stats['tool_usage'].get('web_search', 0)} queries")
                print(f"\n💰 Cost Information:")
                print(f"  Model: {stats['cost']['model']}")
                print(f"  Total cost: ${stats['cost']['total_usd']:.6f}")
                print("="*60)
            print("\n👋 Thanks for using Gemini Shopping Assistant! Goodbye!")
            break
        
        print(f"\n⏳ Processing your request...")
        response = assistant.ask(question, conv_id)
        
        if "response" in response:
            print(f"\n🤖 Assistant:\n{response['response']}")
        else:
            print(f"\n❌ Error: {response.get('error', 'Unknown error occurred')}")
            continue
        
        print_products(response.get("products", []))
        print_token_and_cost_info(response)
        print(f"\n{'─'*60}\n")

if __name__ == "__main__":
    main()
