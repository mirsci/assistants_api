"""
Token Counting Utility for OpenAI and Gemini APIs

This module provides token counting functions using tiktoken for OpenAI models
and estimated counting for Gemini models.
"""

from typing import Optional

try:
    import tiktoken
except ImportError:
    raise ImportError("Please install tiktoken: pip install tiktoken")


class TokenCounter:
    """Token counter for different API providers and models."""
    
    def __init__(self):
        """Initialize token encoders for different models."""
        # OpenAI encodings
        self.encoders = {
            # cl100k_base is used by gpt-4, gpt-4-turbo, gpt-3.5-turbo, gpt-5.2
            "cl100k_base": tiktoken.get_encoding("cl100k_base"),
            # r50k_base is used by gpt-2 and older models
            "r50k_base": tiktoken.get_encoding("r50k_base"),
        }
        
        # Model to encoding mapping
        self.model_to_encoding = {
            # OpenAI models
            "gpt-5.2": "cl100k_base",
            "gpt-4o": "cl100k_base",
            "gpt-4-turbo": "cl100k_base",
            "gpt-4": "cl100k_base",
            "gpt-3.5-turbo": "cl100k_base",
            "gpt-3.5": "cl100k_base",
            "gpt-2": "r50k_base",
            # Gemini models (use estimation)
            "models/gemini-2.0-flash": "estimation",
            "models/gemini-1.5-pro": "estimation",
            "models/gemini-1.5-flash": "estimation",
        }
    
    def count_tokens_openai(self, text: str, model: str = "gpt-3.5-turbo") -> int:
        """
        Count tokens for OpenAI models using tiktoken.
        
        Args:
            text: The text to count tokens for
            model: The OpenAI model name (default: gpt-3.5-turbo)
        
        Returns:
            Number of tokens
        """
        encoding_name = self.model_to_encoding.get(model, "cl100k_base")
        
        try:
            encoding = self.encoders[encoding_name]
            tokens = encoding.encode(text)
            return len(tokens)
        except Exception as e:
            print(f"Warning: Token counting failed for {model} ({e}), using estimation")
            return self._estimate_tokens(text)
    
    def count_tokens_gemini(self, text: str) -> int:
        """
        Count tokens for Gemini models.
        
        Gemini doesn't provide exact token counting, so we use estimation.
        Gemini uses a different tokenization: ~3-4 chars per token
        
        Args:
            text: The text to count tokens for
        
        Returns:
            Estimated number of tokens
        """
        # Gemini estimation: 1 token ≈ 3.5 characters
        return len(text) // 3 if len(text) > 0 else 0
    
    def count_tokens(self, text: str, provider: str = "openai", model: Optional[str] = None) -> int:
        """
        Count tokens for any supported provider and model.
        
        Args:
            text: The text to count tokens for
            provider: The API provider ('openai' or 'gemini')
            model: The model name (optional, uses default if not provided)
        
        Returns:
            Number of tokens
        """
        if provider == "openai":
            model = model or "gpt-3.5-turbo"
            return self.count_tokens_openai(text, model)
        elif provider == "gemini":
            return self.count_tokens_gemini(text)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate tokens using character-based heuristic.
        This is a fallback when tiktoken is not available.
        
        Args:
            text: The text to estimate tokens for
        
        Returns:
            Estimated number of tokens
        """
        # OpenAI approximation: 1 token ≈ 4 characters
        return len(text) // 4 if len(text) > 0 else 0


# Global instance for convenience
_token_counter = TokenCounter()


def count_tokens_openai(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Convenience function to count OpenAI tokens.
    
    Args:
        text: The text to count tokens for
        model: The OpenAI model name
    
    Returns:
        Number of tokens
    """
    return _token_counter.count_tokens_openai(text, model)


def count_tokens_gemini(text: str) -> int:
    """
    Convenience function to count Gemini tokens (estimated).
    
    Args:
        text: The text to count tokens for
    
    Returns:
        Estimated number of tokens
    """
    return _token_counter.count_tokens_gemini(text)


def count_tokens(text: str, provider: str = "openai", model: Optional[str] = None) -> int:
    """
    Convenience function to count tokens for any provider.
    
    Args:
        text: The text to count tokens for
        provider: The API provider ('openai' or 'gemini')
        model: The model name (optional)
    
    Returns:
        Number of tokens
    """
    return _token_counter.count_tokens(text, provider, model)


if __name__ == "__main__":
    # Example usage
    print("Token Counter Examples:\n")
    
    sample_text = "Hello, how many tokens does this text have? This is a sample for counting."
    
    # OpenAI
    print(f"OpenAI (gpt-3.5-turbo): {count_tokens_openai(sample_text)} tokens")
    print(f"OpenAI (gpt-4): {count_tokens_openai(sample_text, 'gpt-4')} tokens")
    print(f"OpenAI (gpt-5.2): {count_tokens_openai(sample_text, 'gpt-5.2')} tokens")
    
    # Gemini
    print(f"\nGemini (estimated): {count_tokens_gemini(sample_text)} tokens")
    
    # Generic
    print(f"\nGeneric (openai/gpt-3.5): {count_tokens(sample_text, 'openai')} tokens")
    print(f"Generic (gemini): {count_tokens(sample_text, 'gemini')} tokens")
    
    # Comparison
    print(f"\nText length: {len(sample_text)} characters")
    print(f"Char/token ratio OpenAI: {len(sample_text) / count_tokens_openai(sample_text):.2f}")
    print(f"Char/token ratio Gemini: {len(sample_text) / count_tokens_gemini(sample_text):.2f}")
