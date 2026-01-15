# Gemini Shopping Assistant - Quick Reference

## 📦 Files Created

### Core Implementation
| File | Purpose |
|------|---------|
| `gemini_shopping_assistant.py` | Main Gemini API shopping assistant class |
| `gemini_session_storage.py` | Session storage with Redis/PostgreSQL backends |
| `gemini_integrated_system.py` | Complete integration combining assistant + storage |

### Documentation
| File | Purpose |
|------|---------|
| `GEMINI_SHOPPING_ASSISTANT.md` | Complete user guide and API reference |
| `ARCHITECTURE.md` | System architecture and design details |
| `QUICK_REFERENCE.md` | This file |

### Examples & Demo
| File | Purpose |
|------|---------|
| `gemini_demo.py` | Interactive demo with multiple examples |

### Configuration
| File | Purpose |
|------|---------|
| `requirements.txt` | Updated with google-generativeai dependency |

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set API Key
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 3. Run Demo
```bash
python gemini_demo.py
```

### 4. Try in Code
```python
from gemini_shopping_assistant import GeminiShoppingAssistant

assistant = GeminiShoppingAssistant()
conv_id = assistant.start_conversation(user_id="user123")

response = assistant.ask(
    "Find noise-canceling headphones under $200",
    conversation_id=conv_id
)

print(response['response'])
for product in response['products']:
    print(f"- {product['name']}: ${product['price']}")
```

## 📚 Key Classes

### GeminiShoppingAssistant
Main conversation manager with Gemini API.

```python
# Initialize
assistant = GeminiShoppingAssistant(
    api_key="...",  # or env GEMINI_API_KEY
    model="gemini-2.0-flash",
    temperature=0.7,
    max_tokens=2048
)

# Start conversation
conv_id = assistant.start_conversation(user_id="user123")

# Ask question
response = assistant.ask("Find...", conversation_id=conv_id)

# Get history
history = assistant.get_conversation_history(conv_id)

# Get context
context = assistant.get_conversation_context(conv_id)
```

### IntegratedGeminiShoppingSystem
High-level orchestration class.

```python
system = IntegratedGeminiShoppingSystem()

# Start session
conv_id = system.start_shopping_session(
    user_id="user123",
    partner_id="store1"
)

# Ask question (auto-manages storage)
response = system.ask_product_question(
    "Find headphones",
    conv_id,
    "user123"
)

# Get session
session = system.get_session_details(conv_id, "store1")

# List sessions
sessions = system.list_user_sessions("user123", "store1")

# Quick search
products = system.search_products("Gaming laptops", "user123")
```

### Session Storage Options

```python
# Development (in-memory)
from gemini_session_storage import GeminiMemoryStorage
storage = GeminiMemoryStorage()

# Production (Redis + PostgreSQL)
from gemini_session_storage import GeminiHybridSessionStorage
storage = GeminiHybridSessionStorage(
    redis_url="redis://localhost:6379/0",
    database_url="postgresql://localhost/gemini_shopping",
    enable_cache=True,
    enable_db=True
)
```

## 💬 Example Conversations

### Example 1: Finding Products
```
User: "Find noise-canceling headphones under $200"

Assistant Response:
"Here are some excellent options for you:

1. **Sony WH-1000XM5** - $349.99
   - Industry-leading noise cancellation
   - 8-hour battery life
   - Link: https://...

2. **Apple AirPods Max** - $549
   - Spatial audio
   - 20-hour battery life
   - Link: https://..."

Products Extracted:
✓ Sony WH-1000XM5: $349.99
✓ Apple AirPods Max: $549
```

### Example 2: Multi-Turn
```
Turn 1:
User: "Find gaming laptops under $1500"
Assistant: "Here are top gaming options..."
→ 5 products extracted

Turn 2:
User: "Which one has the best thermals?"
Assistant: "Based on the previous options, the ASUS ROG..."
→ References Turn 1 products, provides comparison

Turn 3:
User: "Show me alternatives in that price range"
Assistant: "Building on our previous discussion..."
→ Context maintained, previous recommendations available
```

## 🔧 Configuration Options

### Gemini Model Selection
```python
from gemini_shopping_assistant import ModelConfig

# Fast & efficient (recommended)
ModelConfig.GEMINI_2_FLASH

# Most capable but slower
ModelConfig.GEMINI_1_5_PRO

# Balanced
ModelConfig.GEMINI_1_5_FLASH
```

### Temperature Settings
```python
# More deterministic (0.0-0.3)
assistant = GeminiShoppingAssistant(temperature=0.3)

# Balanced (0.5-0.7) - default 0.7
assistant = GeminiShoppingAssistant(temperature=0.7)

# More creative (0.8-1.0)
assistant = GeminiShoppingAssistant(temperature=0.9)
```

### Storage Configuration
```python
# Development
system = IntegratedGeminiShoppingSystem(
    use_persistent_storage=False  # In-memory only
)

# Production with cache
system = IntegratedGeminiShoppingSystem(
    use_persistent_storage=True,
    redis_url="redis://redis-server:6379/0"
)

# Production with cache + database
system = IntegratedGeminiShoppingSystem(
    use_persistent_storage=True,
    redis_url="redis://redis-server:6379/0",
    database_url="postgresql://user:pass@postgres-server/db"
)
```

## 🔍 API Response Format

All responses follow this structure:

```python
{
    # Basic info
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-01-11T10:30:45.123456",
    
    # Content
    "response": "Assistant's full recommendation text...",
    
    # Products from this response
    "products": [
        {
            "name": "Sony WH-1000XM5",
            "price": 349.99,
            "currency": "USD",
            "url": "https://amazon.com/...",
            "image_url": "https://...",
            "description": "Industry-leading noise cancellation",
            "rating": 4.8,
            "source": "Amazon"
        },
        # ... more products
    ],
    
    # All products found in entire conversation
    "all_products": [...],
    
    # Conversation stats
    "message_count": 5,
    
    # Error info (if any)
    "error": None  # or error message
}
```

## 📊 Use Cases

### 1. E-commerce Shopping Assistant
```python
# User browsing products
response = system.ask_product_question(
    "Show me running shoes for marathon training under $150",
    conv_id,
    user_id
)
# Assistant provides product recommendations with links
```

### 2. B2B Procurement
```python
# Buying for business
response = system.ask_product_question(
    "Find industrial IoT sensors with Ethernet connectivity",
    conv_id,
    buyer_id
)
# Assistant provides technical specs and supplier links
```

### 3. Price Comparison
```python
# Comparing options
response = system.ask_product_question(
    "Compare prices for this laptop across different retailers",
    conv_id,
    user_id
)
# Assistant shows same product at different prices
```

### 4. Product Discovery
```python
# Exploring alternatives
response = system.ask_product_question(
    "Show me alternatives to MacBook Pro in the same price range",
    conv_id,
    user_id
)
# Assistant recommends competitive products
```

## 🐛 Troubleshooting

### Issue: "GEMINI_API_KEY not provided or set in environment"
**Solution:**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Issue: "ModuleNotFoundError: No module named 'google.generativeai'"
**Solution:**
```bash
pip install google-generativeai
```

### Issue: No products extracted from response
**Solution:**
- Assistant may not have formatted response with PRODUCT: blocks
- Verify system prompt is being used
- Check response text for "PRICE:", "URL:", etc. format
- Try a different question or model

### Issue: Redis connection refused
**Solution:**
```bash
# Start Redis
docker run -d -p 6379:6379 redis:latest

# Or use in-memory storage
system = IntegratedGeminiShoppingSystem(
    use_persistent_storage=False
)
```

### Issue: Slow API responses
**Solution:**
- Use `gemini-2.0-flash` model (faster)
- Reduce `max_tokens` parameter
- Use shorter questions
- Check internet connection

## 📈 Performance Tips

1. **Use Flash Model**: `gemini-2.0-flash` is faster than `gemini-1.5-pro`
2. **Cache Sessions**: Redis caching reduces latency to <5ms
3. **Batch Queries**: Process multiple conversations in parallel
4. **Index Database**: Index `partner_id`, `user_id`, `conversation_id`
5. **Clean Old Data**: Implement conversation TTL/archival

## 🔐 Security Checklist

- [ ] API key stored in environment variable
- [ ] No API keys in code or logs
- [ ] Multi-tenant isolation by partner_id
- [ ] HTTPS/TLS for all API calls
- [ ] Input validation on user questions
- [ ] Rate limiting implemented
- [ ] Conversation deletion on user request
- [ ] Audit logging enabled
- [ ] Regular key rotation

## 📖 Documentation Files

| Document | Content |
|----------|---------|
| `GEMINI_SHOPPING_ASSISTANT.md` | Full API reference, installation, examples |
| `ARCHITECTURE.md` | System design, data flow, deployment |
| `QUICK_REFERENCE.md` | This file - quick lookup |

## 🎯 Common Patterns

### Pattern 1: Simple Q&A
```python
assistant = GeminiShoppingAssistant()
conv_id = assistant.start_conversation()
response = assistant.ask("Find X", conversation_id=conv_id)
```

### Pattern 2: Multi-Turn with Context
```python
system = IntegratedGeminiShoppingSystem()
conv_id = system.start_shopping_session(user_id)

response1 = system.ask_product_question("Find X", conv_id, user_id)
response2 = system.ask_product_question("Which is best?", conv_id, user_id)
# Response2 has context from Response1
```

### Pattern 3: Multi-Tenant
```python
# User shops at multiple stores
conv1 = system.start_shopping_session(user_id, "store_a")
conv2 = system.start_shopping_session(user_id, "store_b")
# Completely isolated - user can have different products in each
```

### Pattern 4: Quick Search
```python
products = system.search_products(
    query="What I'm looking for",
    user_id=user_id,
    max_results=5
)
# One-shot search, auto-manages session lifecycle
```

## 🚀 Next Steps

1. **Try the Demo**: `python gemini_demo.py`
2. **Read Full Docs**: `GEMINI_SHOPPING_ASSISTANT.md`
3. **Understand Architecture**: `ARCHITECTURE.md`
4. **Integrate into App**: Use `IntegratedGeminiShoppingSystem` in your code
5. **Setup Production**: Configure Redis/PostgreSQL for persistence
6. **Monitor & Scale**: Implement logging and horizontal scaling

## 📞 Support Resources

- **Google Gemini API**: https://ai.google.dev/gemini-api/docs
- **API Reference**: https://ai.google.dev/api/python/google/generativeai
- **Models**: https://ai.google.dev/models

---

**Version**: 1.0  
**Last Updated**: January 2025  
**Status**: Production Ready
