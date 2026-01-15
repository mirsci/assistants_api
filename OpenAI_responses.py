# conversational_ai_openai_only.py
import os
import openai
import re
import json

# Securely load OpenAI API key from environment variable
openai_key = os.environ.get("OPENAI_API_KEY")
if not openai_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set.")
client = openai.OpenAI(api_key=openai_key)

# System instructions to guide the model for shopping queries
system_prompt = """
You are a shopping assistant. 
When asked about products, return a short list with: 
name, price range, merchant link, and image URL.
"""

def process_message(user_message: str, conversation_id: str = None) -> dict:
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

    if conversation_id:
        response_params["previous_response_id"] = conversation_id

    try:
        response = client.responses.create(**response_params)

        # Extract conversation ID for continuity
        new_conversation_id = response.id
       
        # Primary way to access the final synthesized text (includes citations from web_search)
        response_text = response.output_text
        return {
            "response": response_text,
            "conversation_id": new_conversation_id
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
    print("Type 'exit', 'quit', 'bye', or 'goodbye' to end the conversation.\n")

    conversation_id = None
    turn = 0

    while True:
        turn += 1
        user_input = input(f"You (Turn {turn}): ").strip()
        
        if not user_input:
            print("⚠️  Please enter a question.\n")
            continue
        
        if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
            print("\n👋 Thanks for using OpenAI Shopping Assistant! Goodbye!")
            break
        
        print(f"\n⏳ Processing your request...")
        result = process_message(user_input, conversation_id)
        
        print(f"\n🤖 Assistant:\n{result['response']}")
        conversation_id = result["conversation_id"]
        print(f"\n{'─'*80}\n")