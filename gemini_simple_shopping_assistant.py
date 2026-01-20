"""
Very Simple Gemini Shopping Assistant (No Cache, No DB)

This module provides a minimal implementation of a shopping assistant using
Google Gemini API. It supports multi-turn conversations in memory only.
- No Redis, no PostgreSQL, no external storage
- All data is lost when the process exits
- For demo, testing, or local use only

Usage:
    assistant = SimpleGeminiShoppingAssistant(api_key="your-gemini-api-key")
    conv_id = assistant.start_conversation(user_id="user1")
    resp = assistant.ask("Find noise-canceling headphones under $200", conv_id)
    print(resp['response'])
"""

import os
import uuid
import time
import random
from typing import Dict, Any, Optional, List
from datetime import datetime
import re
import traceback

try:
    from google import genai
    from google.genai import types
except ImportError:
    raise ImportError("Please install google-genai: pip install google-genai")

from token_cost_tracker import TokenCostTracker

class SimpleGeminiShoppingAssistant:
    def __init__(self, api_key: Optional[str] = None, model: str = "models/gemini-2.0-flash", temperature: float = 0.7, max_tokens: int = 2048):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
        # Replace the old configuration method with the new Client initialization
        self.client = genai.Client(api_key=self.api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.cost_tracker = TokenCostTracker("gemini")  # Use centralized token/cost tracker
        
        self.system_prompt = (
            "You are a helpful shopping assistant. "
            "Recommend products with name, price, link, and image. "
            # "Use your existing knowledge and do not make real time web searches"
            "Format each product as: PRODUCT: [Name]\nPRICE: $[Amount]\nURL: [Link]\nIMAGE: [Image URL]\nDESCRIPTION: [Key features]\nRATING: [Rating if available]"
        )

    def start_conversation(self, user_id: str) -> str:
        conv_id = str(uuid.uuid4())
        self.conversations[conv_id] = []
        self.cost_tracker.start_conversation(conv_id, self.model)
        return conv_id

    def ask(self, question: str, conversation_id: str) -> Dict[str, Any]:
        if conversation_id not in self.conversations:
            raise ValueError("Conversation not found")
        history = self.conversations[conversation_id]
        # Add user message
        history.append({"role": "user", "content": question, "timestamp": datetime.utcnow().isoformat()})
        # Build prompt
        messages = [
            {"role": "user", "parts": [{"text": self.system_prompt}]}
        ]
        for msg in history:
            messages.append({"role": msg["role"], "parts": [{"text": msg["content"]}]})
        
        # Retry logic with exponential backoff for rate limiting
        max_retries = 3
        base_wait_time = 45  # Start with 45 seconds (API suggests 40s)
        
        # Adding web search for grounding the responses, will not return any URLs for products or images
        grounding_tool = types.Tool(google_search=types.GoogleSearch())

        config_params = types.GenerateContentConfig(
            tools=[grounding_tool],
            temperature=self.temperature,
            max_output_tokens=self.max_tokens
        )

        for attempt in range(max_retries):
            try:
                # Update the generate_content call
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=messages,
                    config=config_params
                )
                text = response.text
                
                # Extract token usage from response
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
                
                # Track tokens and calculate cost using TokenCostTracker
                cost = self.cost_tracker.add_tokens(conversation_id, input_tokens, output_tokens)
                
                # Add assistant message
                history.append({"role": "model", "content": text, "timestamp": datetime.utcnow().isoformat()})
                products = self._extract_products(text)

                # Assuming response with grounding metadata
                text_with_citations = self.add_citations(response)
                
                # Get current conversation stats from tracker
                stats = self.cost_tracker.get_stats(conversation_id)
               
                return {
                    "conversation_id": conversation_id,
                    "response": text,
                    "products": products,
                    "citations": text_with_citations, 
                    "message_count": len(history),
                    "timestamp": datetime.utcnow().isoformat(),
                    "tokens": {
                        "input": input_tokens,
                        "output": output_tokens,
                        "total": input_tokens + output_tokens
                    },
                    "cost": {
                        "this_turn": cost,
                        "conversation_total": stats["cost"]["total_usd"]
                    }
                }
            except Exception as e:                
                error_msg = str(e)
                traceback.print_exc()
                # Check if it's a rate limit error (429 or RESOURCE_EXHAUSTED)
                if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg) and attempt < max_retries - 1:
                    wait_time = base_wait_time * (2 ** attempt) + random.uniform(0, 5)  # Exponential backoff + jitter
                    print(f"Rate limited. Waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}...", flush=True)
                    time.sleep(wait_time)
                    continue
                else:
                    return {"error": error_msg, "conversation_id": conversation_id}

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        return self.conversations.get(conversation_id, [])

    def get_token_usage(self, conversation_id: str) -> Dict[str, int]:
        """Get token usage for a conversation."""
        stats = self.cost_tracker.get_stats(conversation_id)
        return stats["tokens"]

    def get_conversation_cost(self, conversation_id: str) -> float:
        """Get total cost for a conversation in USD."""
        stats = self.cost_tracker.get_stats(conversation_id)
        return stats["cost"]["total_usd"]

    def get_conversation_stats(self, conversation_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a conversation."""
        tracker_stats = self.cost_tracker.get_stats(conversation_id)
        history = self.conversations.get(conversation_id, [])
        
        return {
            "conversation_id": conversation_id,
            "tokens": tracker_stats["tokens"],
            "cost": {
                "total_usd": tracker_stats["cost"]["total_usd"],
                "total_cents": tracker_stats["cost"]["total_cents"],
                "model": tracker_stats["model"]
            },
            "turns": tracker_stats["turns"],
            "tool_usage": tracker_stats["tool_usage"],
            "message_count": len(history)
        }

    def _extract_products(self, text: str) -> List[Dict[str, Any]]:
        # Very simple parser for PRODUCT blocks
        products = []
        blocks = text.split("PRODUCT:")
        for block in blocks[1:]:
            lines = block.strip().split("\n")
            product = {"name": lines[0].strip() if lines else "Unknown", "price": None, "url": None, "image_url": None, "description": None, "rating": None}
            for line in lines[1:]:
                if line.startswith("PRICE:"):
                    try:
                        product["price"] = float(re.sub(r"[^\d.]", "", line))
                    except Exception:
                        pass
                elif line.startswith("URL:"):
                    product["url"] = line.replace("URL:", "").strip()
                elif line.startswith("IMAGE:"):
                    product["image_url"] = line.replace("IMAGE:", "").strip()
                elif line.startswith("DESCRIPTION:"):
                    product["description"] = line.replace("DESCRIPTION:", "").strip()
                elif line.startswith("RATING:"):
                    try:
                        product["rating"] = float(re.sub(r"[^\d.]", "", line))
                    except Exception:
                        pass
            if product["name"] != "Unknown":
                products.append(product)
        return products
    
    def add_citations(self, response):
        text = response.text
        supports = response.candidates[0].grounding_metadata.grounding_supports
        chunks = response.candidates[0].grounding_metadata.grounding_chunks

        # Sort supports by end_index in descending order to avoid shifting issues when inserting.
        if supports is None:
            return text
        
        sorted_supports = sorted(supports, key=lambda s: s.segment.end_index, reverse=True)

        for support in sorted_supports:
            end_index = support.segment.end_index
            if support.grounding_chunk_indices:
                # Create citation string like [1](link1)[2](link2)
                citation_links = []
                for i in support.grounding_chunk_indices:
                    if i < len(chunks):
                        uri = chunks[i].web.uri
                        citation_links.append(f"[{i + 1}]({uri})")

                citation_string = ", ".join(citation_links)
                text = text[:end_index] + citation_string + text[end_index:]

        return text
