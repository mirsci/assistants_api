"""
Token and Cost Tracking Utility for API Interactions

This module provides utilities to track token usage and calculate costs
for different AI APIs (OpenAI, Gemini, etc.)
"""

from typing import Dict, Optional
from datetime import datetime

# OpenAI Pricing (as of 2025)
OPENAI_PRICING = {
    "gpt-4o": {
        "input": 2.5 / 1_000_000,       # $2.50 per 1M input tokens
        "output": 10.0 / 1_000_000,     # $10.00 per 1M output tokens
    },
    "gpt-4-turbo": {
        "input": 10.0 / 1_000_000,      # $10.00 per 1M input tokens
        "output": 30.0 / 1_000_000,     # $30.00 per 1M output tokens
    },
    "gpt-3.5-turbo": {
        "input": 0.5 / 1_000_000,       # $0.50 per 1M input tokens
        "output": 1.5 / 1_000_000,      # $1.50 per 1M output tokens
    },
    "gpt-4.1-mini": {
        "input": 0.15 / 1_000_000,      # $0.15 per 1M input tokens
        "output": 0.6 / 1_000_000,      # $0.60 per 1M output tokens
    },
    "gpt-5.2": {
        "input": 5.0 / 1_000_000,       # $5.00 per 1M input tokens (estimated)
        "output": 20.0 / 1_000_000,     # $20.00 per 1M output tokens (estimated)
    },
}

# Gemini Pricing (as of 2025)
GEMINI_PRICING = {
    "models/gemini-2.0-flash": {
        "input": 0.075 / 1_000_000,      # $0.075 per 1M input tokens
        "output": 0.3 / 1_000_000,       # $0.3 per 1M output tokens
    },
    "models/gemini-1.5-pro": {
        "input": 1.25 / 1_000_000,       # $1.25 per 1M input tokens
        "output": 5.0 / 1_000_000,       # $5.0 per 1M output tokens
    },
    "models/gemini-1.5-flash": {
        "input": 0.075 / 1_000_000,      # $0.075 per 1M input tokens
        "output": 0.3 / 1_000_000,       # $0.3 per 1M output tokens
    }
}

# Tool usage costs (estimation)
TOOL_COSTS = {
    "openai": {
        "web_search": 0.0,  # Included in OpenAI Responses API
    },
    "gemini": {
        "web_search": 0.0,  # Included in Gemini API
    }
}


class TokenCostTracker:
    """Track token usage and calculate costs for API interactions"""
    
    def __init__(self, provider: str = "openai"):
        """
        Initialize the tracker.
        
        Args:
            provider: 'openai' or 'gemini'
        """
        self.provider = provider.lower()
        self.conversations: Dict[str, Dict] = {}
    
    def start_conversation(self, conversation_id: str, model: str) -> None:
        """Start tracking a new conversation."""
        self.conversations[conversation_id] = {
            "model": model,
            "tokens": {"input": 0, "output": 0},
            "cost": 0.0,
            "turns": 0,
            "created_at": datetime.utcnow().isoformat(),
            "tool_usage": {}
        }
    
    def add_tokens(self, conversation_id: str, input_tokens: int, 
                   output_tokens: int, tool_name: Optional[str] = None) -> float:
        """
        Add tokens to a conversation and calculate cost.
        
        Args:
            conversation_id: Conversation ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            tool_name: Optional tool name
        
        Returns:
            Cost for this turn in USD
        """
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conv = self.conversations[conversation_id]
        conv["tokens"]["input"] += input_tokens
        conv["tokens"]["output"] += output_tokens
        conv["turns"] += 1
        
        # Calculate cost
        cost = self._calculate_cost(
            conversation_id, 
            input_tokens, 
            output_tokens, 
            tool_name
        )
        conv["cost"] += cost
        
        return cost
    
    def _calculate_cost(self, conversation_id: str, input_tokens: int, 
                        output_tokens: int, tool_name: Optional[str] = None) -> float:
        """Calculate cost for a single API call."""
        conv = self.conversations[conversation_id]
        model = conv["model"]
        
        # Get pricing based on provider
        if self.provider == "openai":
            pricing = OPENAI_PRICING.get(model, OPENAI_PRICING["gpt-3.5-turbo"])
        elif self.provider == "gemini":
            pricing = GEMINI_PRICING.get(model, GEMINI_PRICING["models/gemini-2.0-flash"])
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        
        # Calculate token cost
        input_cost = input_tokens * pricing["input"]
        output_cost = output_tokens * pricing["output"]
        token_cost = input_cost + output_cost
        
        # Add tool cost if applicable
        tool_cost = 0.0
        if tool_name:
            tool_cost_dict = TOOL_COSTS.get(self.provider, {})
            tool_cost = tool_cost_dict.get(tool_name, 0.0)
            
            # Track tool usage
            if tool_name not in conv["tool_usage"]:
                conv["tool_usage"][tool_name] = 0
            conv["tool_usage"][tool_name] += 1
        
        return token_cost + tool_cost
    
    def get_stats(self, conversation_id: str) -> Dict:
        """Get comprehensive statistics for a conversation."""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conv = self.conversations[conversation_id]
        total_tokens = conv["tokens"]["input"] + conv["tokens"]["output"]
        
        return {
            "conversation_id": conversation_id,
            "model": conv["model"],
            "tokens": {
                "input": conv["tokens"]["input"],
                "output": conv["tokens"]["output"],
                "total": total_tokens
            },
            "cost": {
                "total_usd": conv["cost"],
                "total_cents": conv["cost"] * 100,
                "total_millidollars": conv["cost"] * 1000
            },
            "turns": conv["turns"],
            "tool_usage": conv["tool_usage"],
            "avg_cost_per_turn": conv["cost"] / conv["turns"] if conv["turns"] > 0 else 0.0,
            "created_at": conv["created_at"]
        }
    
    def format_cost(self, cost: float, precision: int = 6) -> str:
        """Format cost as a readable string."""
        if cost < 0.01:
            return f"${cost:.{precision}f}"
        else:
            return f"${cost:.4f}"
    
    def get_conversation_summary(self, conversation_id: str) -> str:
        """Get a formatted summary of conversation stats."""
        stats = self.get_stats(conversation_id)
        
        summary = f"""
╔══════════════════════════════════════════════════════╗
║            CONVERSATION SUMMARY                      ║
╚══════════════════════════════════════════════════════╝

Model: {stats['model']}
Turns: {stats['turns']}

📊 TOKEN USAGE:
  • Input:  {stats['tokens']['input']:>8} tokens
  • Output: {stats['tokens']['output']:>8} tokens
  • Total:  {stats['tokens']['total']:>8} tokens

💰 COST:
  • Total:           {self.format_cost(stats['cost']['total_usd'])}
  • Per turn (avg):  {self.format_cost(stats['cost']['total_usd'] / stats['turns'] if stats['turns'] > 0 else 0)}
"""
        
        if stats['tool_usage']:
            summary += "\n🔧 TOOL USAGE:\n"
            for tool, count in stats['tool_usage'].items():
                summary += f"  • {tool}: {count} calls\n"
        
        summary += f"\n Created: {stats['created_at']}\n"
        
        return summary


# Utility functions
def count_tokens_openai(text: str) -> int:
    """
    Estimate token count for OpenAI models.
    Rule of thumb: 1 token ≈ 4 characters
    """
    return len(text) // 4


def count_tokens_gemini(text: str) -> int:
    """
    Estimate token count for Gemini models.
    Rule of thumb: 1 token ≈ 3-4 characters
    """
    return len(text) // 3


if __name__ == "__main__":
    # Example usage
    print("Token and Cost Tracking Utility\n")
    
    # OpenAI example
    tracker = TokenCostTracker("openai")
    conv_id = "conv_123"
    tracker.start_conversation(conv_id, "gpt-4o")
    
    # Simulate multiple turns
    tracker.add_tokens(conv_id, 50, 150)  # Turn 1
    tracker.add_tokens(conv_id, 100, 200)  # Turn 2
    tracker.add_tokens(conv_id, 75, 180)   # Turn 3
    
    print(tracker.get_conversation_summary(conv_id))
    
    # Gemini example
    print("\n" + "="*60 + "\n")
    tracker_gemini = TokenCostTracker("gemini")
    conv_id2 = "conv_456"
    tracker_gemini.start_conversation(conv_id2, "models/gemini-2.0-flash")
    
    tracker_gemini.add_tokens(conv_id2, 100, 300)
    tracker_gemini.add_tokens(conv_id2, 120, 350, "web_search")
    
    print(tracker_gemini.get_conversation_summary(conv_id2))
