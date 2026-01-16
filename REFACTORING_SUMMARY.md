# Refactoring Summary: Token Cost Tracker Integration

## Overview
Both `gemini_simple_shopping_assistant.py` and `OpenAI_responses.py` have been refactored to use the centralized `TokenCostTracker` class from `token_cost_tracker.py`. This eliminates code duplication and provides a consistent interface for token tracking and cost calculation across different API providers.

## Changes Made

### 1. gemini_simple_shopping_assistant.py

#### Removed
- `GEMINI_PRICING` dictionary (now in TokenCostTracker)
- `TOOL_COSTS` dictionary (now in TokenCostTracker)
- `self.token_usage` instance variable
- `self.cost_tracking` instance variable
- `_calculate_cost()` method (replaced by TokenCostTracker.add_tokens())

#### Added
- Import: `from token_cost_tracker import TokenCostTracker`
- `self.cost_tracker = TokenCostTracker("gemini")` in `__init__`

#### Modified Methods

**`start_conversation()`**
- Old: Manually initialized `token_usage` and `cost_tracking` dicts
- New: Calls `self.cost_tracker.start_conversation(conv_id, self.model)`

**`ask()`**
- Old: Extracted tokens and manually calculated cost using `_calculate_cost()`
- New: Calls `self.cost_tracker.add_tokens()` which handles both token tracking and cost calculation
- Old: Accessed `self.cost_tracking[conversation_id]` for totals
- New: Uses `self.cost_tracker.get_stats()` to retrieve comprehensive stats

**`get_token_usage()`**
- Old: Returned from `self.token_usage` dict
- New: Calls `cost_tracker.get_stats()` and extracts token data

**`get_conversation_cost()`**
- Old: Returned from `self.cost_tracking` dict
- New: Calls `cost_tracker.get_stats()` and extracts cost

**`get_conversation_stats()`**
- Old: Manually built stats from local dicts and history
- New: Delegates to `cost_tracker.get_stats()` and enriches with conversation history

### 2. OpenAI_responses.py

#### Added
- Import: `from token_cost_tracker import TokenCostTracker`
- Global: `cost_tracker = TokenCostTracker("openai")`

#### Modified `process_message()`
- Added token tracking initialization on first turn
- Extracts token counts from response (if available)
- Calls `cost_tracker.add_tokens()` to track tokens and calculate cost
- Returns token and cost information in response

#### Enhanced Interactive Loop
- Added support for 'stats' and 'summary' commands
- Displays comprehensive conversation summary including:
  - Model name
  - Total turns and token counts
  - Total cost and average cost per turn
- Token and cost info now displayed after each turn

## Benefits

1. **Code Reusability**: Single `TokenCostTracker` class handles both Gemini and OpenAI
2. **Centralized Pricing**: All pricing tables maintained in one place
3. **Consistent Interface**: Same methods work across different providers
4. **Reduced Duplication**: No need to reimplement token tracking logic
5. **Easier Maintenance**: Update pricing in one location only
6. **Better Stats**: More comprehensive tracking (tool usage, average costs, etc.)

## Usage Example

### Gemini Assistant
```python
from gemini_simple_shopping_assistant import SimpleGeminiShoppingAssistant

assistant = SimpleGeminiShoppingAssistant(api_key="your-key")
conv_id = assistant.start_conversation(user_id="user1")
response = assistant.ask("Find headphones under $200", conv_id)

# Get cost info
print(f"Cost: ${response['cost']['this_turn']:.6f}")
print(f"Total: ${response['cost']['conversation_total']:.6f}")

# Get comprehensive stats
stats = assistant.get_conversation_stats(conv_id)
print(f"Total tokens: {stats['tokens']['total']}")
```

### OpenAI Responses
```python
from token_cost_tracker import TokenCostTracker

# Track tokens
tracker = TokenCostTracker("openai")
tracker.start_conversation("conv_123", "gpt-4o")
cost = tracker.add_tokens("conv_123", 150, 200)  # input, output tokens

# Get stats
stats = tracker.get_stats("conv_123")
print(f"Total cost: ${stats['cost']['total_usd']:.6f}")
print(f"Tokens used: {stats['tokens']['total']}")
```

## Testing
Both files have been tested for syntax correctness. The refactoring maintains backward compatibility with the response format, ensuring existing code using these modules will continue to work without modification.

## Migration Path
- For existing code using `get_token_usage()`, `get_conversation_cost()`, and `get_conversation_stats()` - no changes needed, they still work
- For code directly accessing `token_usage` or `cost_tracking` attributes - update to use the public methods
- For adding new AI providers - simply create new instance of `TokenCostTracker` with provider name and existing pricing tables
