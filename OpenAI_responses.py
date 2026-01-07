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


# === SIMULATED MULTI-TURN CONVERSATION FOR USE CASE 5 ===
if __name__ == "__main__":
    conversation_id = None

    # Turn 1: Shopping search - Model auto-invokes web_search for laptops 
    print("\n First use case example:\n")
    print("User: Find noise-canceling headphones under $200?\n")
    result = process_message("Find noise-canceling headphones under $200?", conversation_id)
    print("Assistant:", result["response"])
    conversation_id = result["conversation_id"]
    print("\n(Conversation ID from turn 1:", conversation_id, ")")
    print("\n" + "="*80 + "\n")

    # Turn 2: Shopping search - Model auto-invokes web_search for current laptops
    print("User: Which one is best for travel?.\n")
    result = process_message("Which one is best for travel?.", conversation_id)
    print("Assistant:", result["response"])
    conversation_id = result["conversation_id"]
    print("\n(Conversation ID from turn 2:", conversation_id, ")")
    print("\n" + "="*80 + "\n")

    # Turn 1: Simpler implementation without helper function
    print("\n Simpler implementation - First use case example:\n")
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a shopping assistant. "
                    "When asked about products, return a short list with: "
                    "name, price range, merchant link, and image URL."
                )
            },
            {
                "role": "user",
                "content": "Find noise-canceling headphones under $200"
            }
        ]
    )

    print("Assistant reply:\n")
    print(response.output_text)

    # Save conversation state
    previous_response_id = response.id

    # ---- Turn 2: Follow-up question (multi-turn) ----
    follow_up = client.responses.create(
        model="gpt-4.1-mini",
        previous_response_id=previous_response_id,
        input=[
            {
                "role": "user",
                "content": "Which one is best for travel?"
            }
        ]
    )

    print("\nFollow-up reply:\n")
    print(follow_up.output_text)