# conversational_ai_openai_conversations.py
import os
import openai
import json

# Securely load OpenAI API key from environment variable
openai_key = os.environ.get("OPENAI_API_KEY")
if not openai_key:
    raise RuntimeError("OPENAI_API_KEY environment variable not set.")
client = openai.OpenAI(api_key=openai_key)

# System instructions for the assistant behavior
system_prompt = """
You are a helpful back-to-school shopping assistant for college students.
- Provide practical study tips when asked.
- Focus on laptops under $800 suitable for students.
- Prioritize lightweight models with good battery life when specified.
- Include direct product links, current prices, key specs, and image URLs (use Markdown for formatting: bold names, links, ![alt](image_url)).
- Compare to tablets if requested.
- Be conversational, encouraging, and cite sources when possible.
- Always use the web_search tool for up-to-date shopping information.
"""
# - For product recommendations (e.g., laptops), search the web for current real-time prices, direct merchant links (e.g., Amazon, Best Buy, Walmart, Lenovo, HP, Dell), product images, and specifications.

def create_or_get_conversation(conversation_id: str = None) -> str:
    """Create a new conversation or retrieve an existing one."""
    if conversation_id:
        return conversation_id
    # Create a new conversation with initial system message
    conv = client.conversations.create(
        items=[
            {"role": "system", "content": system_prompt}
        ]
    )
    return conv.id

def process_message(user_message: str, conversation_id: str) -> dict:
    """
    Append user message and generate a response using the Responses API attached to the conversation.
    The model will automatically use web_search for shopping queries.
    """
    # Enable built-in web_search tool
    tools = [{"type": "web_search"}]

    # Append user message to the conversation
    response = client.conversations.responses.create(
        conversation_id=conversation_id,    
        model="gpt-4o",  # Latest model supporting web_search (as of Dec 2025)   
        role="user",
        content=user_message, 
        tools=tools,
        tool_choice="auto",
        store=True  # Persists the conversation state
    )

    # Extract the final text output (includes citations from web_search)
    response_text = getattr(response, "output_text", "I'm here to help with back-to-school planning!")

    return {
        "response": response_text.strip(),
        "conversation_id": conversation_id
    }


# === SIMULATED MULTI-TURN CONVERSATION FOR USE CASE 5 ===
if __name__ == "__main__":
    # conversation_id = None

    # # Create conversation on first turn
    # conversation_id = create_or_get_conversation(conversation_id)

    # # Turn 1: General AI search
    # print("User: What are essential study tips for college students?\n")
    # result = process_message("What are essential study tips for college students?", conversation_id)
    # print("Assistant:", result["response"])
    # print("\n" + "="*80 + "\n")

    # # Turn 2: Shopping search - Model auto-invokes web_search
    # print("User: Recommend laptops for students under $800.\n")
    # result = process_message("Recommend laptops for students under $800.", conversation_id)
    # print("Assistant:", result["response"])
    # print("\n" + "="*80 + "\n")

    # # Turn 3: Multi-turn refinement - Model uses context + web_search
    # print("User: One with good battery life and lightweight? Compare to tablets?\n")
    # result = process_message("One with good battery life and lightweight? Compare to tablets?", conversation_id)
    # print("Assistant:", result["response"])
    # print("\n(Conversation ID for next turn:", conversation_id, ")")

    # 1) Create a new conversation object
    #    We start it with a system instruction
    conversation = client.conversations.create(
        metadata={"purpose": "shopping_assistant"},
        items=[
            {
                "type": "message",
                "role": "system",
                "content": "You are a shopping assistant. When asked about products, return products with name, price, merchant link, and image URL."
            }
        ]
    )

    conv_id = conversation.id
    print("Conversation ID:", conv_id)

    # 2) First user turn — ask shopping question
    first_user_msg = {
            "type": "message",
            "role": "user",
            "content": "I live in a remote area with frequent energy fluctuations. I want to buy laptop with UPS to protect from dirty electricity. Provide recommendations"
    }
   
    # ---------------------------------------
    # 2) Add first user message
    # ---------------------------------------
    client.conversations.items.create(
        conversation_id=conv_id,
        items=[
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "I live in a remote area with frequent energy fluctuations. I want to buy laptop with UPS to protect from dirty electricity. Provide recommendations"}
                ]
            }
        ]
    )
    # ---------------------------------------
    # 3) Generate the assistant response
    # ---------------------------------------
    response_1 = client.responses.create(
        model="gpt-4.1-mini",
        input=[{"role": "user", "content": "I live in a remote area with frequent energy fluctuations. I want to buy laptop with UPS to protect from dirty electricity. Provide recommendations"}],
        conversation=conv_id
    )

    print("\nAssistant reply:\n", response_1.output_text)


    # Persist the assistant reply back into the conversation
    client.conversations.items.create(
        conv_id,
        items=[
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "output_text", "text": response_1.output_text}
                ]
            }
        ]
    )


    # ---------------------------------------
    # 4) Second (follow-up) user message
    # ---------------------------------------
    client.conversations.items.create(
        conv_id,
        items=[
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Help me make a decision, synthesize these findings"}
                ]
            }
        ]
    )


    # ---------------------------------------
    # 5) Second assistant response
    # ---------------------------------------
    response_2 = client.responses.create(
        model="gpt-4.1-mini",
        input=[{"role": "user", "content": "Help me make a decision, synthesize these findings"}],
        conversation=conv_id
    )

    print("\nFollow-up reply:\n", response_2.output_text)

    # And persist it again
    client.conversations.items.create(
        conv_id,
        items=[
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "output_text", "text": response_2.output_text}
                ]
            }
        ]
    )

