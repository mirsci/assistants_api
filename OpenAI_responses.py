# conversational_ai_openai_only.py
import os
import openai
import re
import json

try:
    import tiktoken
except ImportError:
    raise ImportError("Please install tiktoken: pip install tiktoken")

from token_cost_tracker import TokenCostTracker

# Securely load OpenAI API key from environment variable
openai_key = os.environ.get("OPENAI_API_KEY")
if not openai_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set.")
client = openai.OpenAI(api_key=openai_key)

# Initialize tiktoken encoder for token counting
# Using cl100k_base encoding which is used by gpt-4, gpt-3.5-turbo, etc.
encoding = tiktoken.get_encoding("cl100k_base")

# System instructions to guide the model for shopping queries
system_prompt = """
You are a shopping assistant. 
When asked about products, return a short list with: 
name, price range, merchant link, and image URL.
"""

# Initialize token/cost tracker
cost_tracker = TokenCostTracker("openai")


def count_tokens(text: str) -> int:
    """
    Count tokens in text using tiktoken.
    
    Args:
        text: The text to count tokens for
    
    Returns:
        Number of tokens
    """
    try:
        tokens = encoding.encode(text)
        print("## Tokens counted: " + str(len(tokens)))  # Debug: Show encoded tokens")
        return len(tokens)
    except Exception as e:
        # Fallback to character-based estimation if tiktoken fails
        print(f"Warning: tiktoken encoding failed ({e}), falling back to estimation")
        return len(text) // 4


def process_message(user_message: str, conversation_id: str = None, previous_response_id: str = None) -> dict:
    """
    Process a message using OpenAI Responses API with built-in web_search tool.
    The model automatically invokes web_search when needed for up-to-date product info.
    No external APIs or custom functions required.
    """
    # Simple string input is sufficient and commonly used
    input_text = user_message

    # Enable the built-in web_search tool
    tools = [
        {"type": "web_search"}
    ]

    response_params = {
        "model": "gpt-5.2",  # Latest advanced model as of December 2025 (supports web_search)
        "input": input_text,
        "instructions": system_prompt, 
        "tools": tools,
        "tool_choice": "auto",  # Model decides when to use web_search
        "store": True  # Enables stateful multi-turn conversations
    }

    if previous_response_id:
        response_params["previous_response_id"] = previous_response_id

    try:
        response = client.responses.create(**response_params)

        # Extract conversation ID for continuity
        new_response_id= response.id
        
        # Initialize tracker for this conversation if not already tracked
        # This handles both first turn (conversation_id is None) and subsequent turns
        try:
            # Try to get stats - if it fails, conversation doesn't exist in tracker yet
            cost_tracker.get_stats(conversation_id)
        except (ValueError, KeyError):
            # Conversation not in tracker, initialize it
            print(f"Initializing cost tracker for new conversation { conversation_id}")
            cost_tracker.start_conversation(conversation_id, "gpt-5.2")
       
        # Primary way to access the final synthesized text (includes citations from web_search)
        response_text = response.output_text
        
        # Count tokens using tiktoken for accurate token counting
        input_tokens = count_tokens(input_text)
        output_tokens = count_tokens(response_text)
        
        # Track tokens and cost (always track, even if estimated)
        cost = 0.0
        if input_tokens > 0 or output_tokens > 0:
            cost = cost_tracker.add_tokens( conversation_id, input_tokens, output_tokens)
        
        # Get stats for response
        stats = cost_tracker.get_stats(conversation_id)
        
        return {
            "response": response_text,
            "conversation_id": conversation_id,
            "new_response_id": new_response_id,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens
            },
            "tool_usage": stats["tool_usage"],
            "cost": {
                "this_turn": cost,
                "conversation_total": stats["cost"]["total_usd"]
            }
        }
    except Exception as e:
        return {
            "response": f"Error: {str(e)}",
            "conversation_id": conversation_id
        }


# === INTERACTIVE MULTI-TURN CONVERSATION ===
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🛍️  OPENAI SHOPPING ASSISTANT - Multi-Turn Chat")
    print("="*80)
    print("Ask shopping questions and get web search results.")
    print("Type 'exit', 'quit', 'bye', 'goodbye', 'stats', or 'summary' to end or view stats.\n")

    conversation_id = None
    new_response_id = None
    turn = 0

    while True:
        turn += 1
        conversation_id = 1
        user_input = input(f"You (Turn {turn}): ").strip()
        
        if not user_input:
            print("⚠️  Please enter a question.\n")
            continue
        
        if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            print("\n👋 Thanks for using OpenAI Shopping Assistant! Goodbye!")
            break
        
        if user_input.lower() in ['stats', 'summary']:
            if conversation_id:
                stats = cost_tracker.get_stats(conversation_id)
                print("\n" + "="*80)
                print("📈 CONVERSATION SUMMARY")
                print("="*80)
                print(f"Model: {stats['model']}")
                print(f"Total turns: {stats['turns']}")
                print(f"\n📊 Token Usage (entire conversation):")
                print(f"  Input:  {stats['tokens']['input']} tokens")
                print(f"  Output: {stats['tokens']['output']} tokens")
                print(f"  Total:  {stats['tokens']['total']} tokens")
                print(f"\n📊 Tool Usage (entire conversation):")
                print(f"  Web Search: {stats['tool_usage'].get('web_search', 0)} queries")

                print(f"\n💰 Cost Information:")
                print(f"  Total cost: ${stats['cost']['total_usd']:.6f}")
                if stats['turns'] > 0:
                    print(f"  Per turn (avg): ${stats['cost']['total_usd'] / stats['turns']:.6f}")
                print("="*80 + "\n")
            else:
                print("⚠️  No conversation started yet.\n")
            continue
        
        print(f"\n⏳ Processing your request...")
        result = process_message(user_input, conversation_id, new_response_id)
        
        if "Error" not in result["response"]:
            print(f"\n🤖 Assistant:\n{result['response']}")
            conversation_id = result["conversation_id"]
            new_response_id = result["new_response_id"]
            
            # Show token/cost info
            if result.get("tokens", {}).get("total", 0) > 0:
                tokens = result["tokens"]
                cost = result["cost"]
                print(f"\n📊 Token Usage (this turn):")
                print(f"  Input:  {tokens['input']} tokens")
                print(f"  Output: {tokens['output']} tokens")
                print(f"  Total:  {tokens['total']} tokens")
                print(f"\n💰 Cost Information:")
                print(f"  This turn: ${cost['this_turn']:.6f}")
                print(f"  Conversation total: ${cost['conversation_total']:.6f}")
        else:
            print(f"\n❌ Error: {result['response']}")
        
        print(f"\n{'─'*80}\n")