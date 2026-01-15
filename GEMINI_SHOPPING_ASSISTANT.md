# Google Gemini Shopping Assistant

A production-ready shopping assistant implementation using Google's Gemini API for multi-turn product discovery conversations. This system supports product recommendations with links, images, and pricing information.

## Features

✅ **Multi-Turn Conversations** - Maintain context across multiple questions  
✅ **Product Discovery** - Find products with detailed information (name, price, links, images)  
✅ **Session Management** - Persistent conversation storage with Redis/PostgreSQL  
✅ **Multi-Tenant Support** - Isolate conversations by store/partner  
✅ **Conversation History** - Access full message history and product recommendations  
✅ **Production Ready** - Error handling, logging, and enterprise features  

## Components

### 1. **gemini_shopping_assistant.py**
Core shopping assistant class using Google Gemini API.

**Main Classes:**
- `GeminiShoppingAssistant` - Main conversation manager
- `ConversationContext` - Manages conversation state and history
- `Product` - Represents product with details
- `ConversationMessage` - Message data model
- `ResponseMetrics` - Tracks API usage

**Key Methods:**
```python
# Initialize
assistant = GeminiShoppingAssistant(api_key="your-gemini-api-key")

# Start conversation
conversation_id = assistant.start_conversation(user_id="user123")

# Ask question
response = assistant.ask("Find noise-canceling headphones under $200", 
                        conversation_id=conversation_id)

# Get history
history = assistant.get_conversation_history(conversation_id)

# Get context
context = assistant.get_conversation_context(conversation_id)
```

### 2. **gemini_session_storage.py**
Session storage layer with Redis caching and PostgreSQL persistence.

**Storage Options:**
- `GeminiMemoryStorage` - In-memory storage (development/testing)
- `GeminiRedisCache` - Redis caching layer
- `GeminiHybridSessionStorage` - Redis cache + PostgreSQL database (production)

**Key Methods:**
```python
storage = GeminiHybridSessionStorage()

# Create conversation
storage.create_conversation({
    'conversation_id': '...',
    'user_id': 'user123',
    'partner_id': 'store1'
})

# Get conversation
conversation = storage.get_conversation(conv_id, partner_id)

# Add message
storage.add_message(conv_id, partner_id, {
    'role': 'user',
    'content': 'Find headphones'
})

# List user conversations
conversations = storage.list_conversations(partner_id, user_id)
```

### 3. **gemini_integrated_system.py**
Complete integration combining assistant and storage.

**Main Class:**
- `IntegratedGeminiShoppingSystem` - Orchestrates assistant + storage

**Key Methods:**
```python
system = IntegratedGeminiShoppingSystem(gemini_api_key="...")

# Start shopping session
conv_id = system.start_shopping_session(
    user_id="user123",
    partner_id="electronics_store",
    session_title="Headphones Shopping"
)

# Ask product question
response = system.ask_product_question(
    question="Which one is best for travel?",
    conversation_id=conv_id,
    user_id="user123"
)

# Get session details
session = system.get_session_details(conv_id, "electronics_store")

# List user sessions
sessions = system.list_user_sessions("user123", "electronics_store")

# End session
system.end_session(conv_id, "electronics_store")

# Quick search
products = system.search_products(
    query="Gaming laptops under $1500",
    user_id="user123"
)
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `google-generativeai` - Google Gemini API
- `openai` - OpenAI API (existing)
- `redis` - Optional, for caching
- `sqlalchemy` - Optional, for PostgreSQL
- `psycopg2-binary` - Optional, for PostgreSQL
- `requests` - HTTP client

### 2. Get Gemini API Key

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Click "Get API Key"
3. Create new API key for your project
4. Set environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

### 3. Optional: Setup Database

For production persistence, setup PostgreSQL:

```bash
# Create database
createdb gemini_shopping

# Update database_url in your code
database_url = "postgresql://user:password@localhost/gemini_shopping"
```

For caching, setup Redis:

```bash
# Start Redis (if using Docker)
docker run -d -p 6379:6379 redis:latest

# Or use your existing Redis instance
redis_url = "redis://localhost:6379/0"
```

## Usage Examples

### Example 1: Simple Product Discovery

```python
from gemini_shopping_assistant import GeminiShoppingAssistant

assistant = GeminiShoppingAssistant()

# Start conversation
conv_id = assistant.start_conversation(user_id="user123")

# Find products
response = assistant.ask(
    "Find noise-canceling headphones under $200",
    conversation_id=conv_id
)

print(response['response'])
# Products with links, images, and prices are included in response['products']
```

### Example 2: Multi-Turn Conversation

```python
from gemini_integrated_system import IntegratedGeminiShoppingSystem

system = IntegratedGeminiShoppingSystem()

# Start session
conv_id = system.start_shopping_session(
    user_id="customer_001",
    partner_id="electronics_store"
)

# Question 1
response1 = system.ask_product_question(
    "Find noise-canceling headphones under $200",
    conv_id,
    "customer_001"
)

# Question 2 (maintains context from Q1)
response2 = system.ask_product_question(
    "Which one is best for travel?",
    conv_id,
    "customer_001"
)

# Get full session
session = system.get_session_details(conv_id, "electronics_store")
print(f"Total messages: {len(session['messages'])}")
print(f"Products found: {len(session['products_found'])}")
```

### Example 3: Multi-Tenant Support

```python
# Same user, different stores
user_id = "shared_customer"

# Session 1: Electronics
conv1 = system.start_shopping_session(user_id, partner_id="electronics_store")
system.ask_product_question(
    "Show me budget smartphones",
    conv1,
    user_id,
    "electronics_store"
)

# Session 2: Fashion (data isolated)
conv2 = system.start_shopping_session(user_id, partner_id="fashion_store")
system.ask_product_question(
    "Show me winter jackets",
    conv2,
    user_id,
    "fashion_store"
)

# List sessions per store
electronics_sessions = system.list_user_sessions(user_id, "electronics_store")
fashion_sessions = system.list_user_sessions(user_id, "fashion_store")
```

### Example 4: Quick Search

```python
# One-shot product search (creates and closes session)
products = system.search_products(
    query="Gaming laptops under $1500",
    user_id="user123",
    max_results=5
)

for product in products:
    print(f"{product['name']}: ${product['price']}")
    print(f"Link: {product['url']}")
```

## Data Models

### Product
```python
@dataclass
class Product:
    name: str              # Product name
    price: float          # Price in USD
    currency: str         # Currency (default: USD)
    url: Optional[str]    # Direct product link
    image_url: Optional[str]  # Product image URL
    description: Optional[str]  # Key features
    rating: Optional[float]     # Customer rating (0-5)
    source: Optional[str]       # Product source/store
```

### ConversationContext
```python
@dataclass
class ConversationContext:
    conversation_id: str  # Unique conversation ID
    user_id: str         # User identifier
    partner_id: str      # Multi-tenant partner ID
    messages: List       # Conversation messages
    products_found: List # All products mentioned
    metrics: List        # API usage metrics
    created_at: datetime # Session start
    updated_at: datetime # Last update
    metadata: Dict       # Custom metadata
```

## API Response Format

```python
{
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "response": "Based on your requirements, here are the best noise-canceling headphones...",
    "products": [
        {
            "name": "Sony WH-1000XM5",
            "price": 399.99,
            "currency": "USD",
            "url": "https://...",
            "image_url": "https://...",
            "description": "Industry-leading noise cancellation",
            "rating": 4.8,
            "source": "Amazon"
        },
        # ... more products
    ],
    "all_products": [...],  # All products found in conversation
    "message_count": 2,
    "timestamp": "2025-01-11T10:30:45.123456"
}
```

## Configuration

### Model Selection

```python
from gemini_shopping_assistant import ModelConfig

# Available models
ModelConfig.GEMINI_2_FLASH        # Latest, fastest (recommended)
ModelConfig.GEMINI_1_5_PRO        # Most capable
ModelConfig.GEMINI_1_5_FLASH      # Balanced
```

### Temperature Settings

```python
# Temperature controls randomness (0.0-1.0)
assistant = GeminiShoppingAssistant(
    temperature=0.7  # More creative recommendations
)
# Lower (0.3) = More focused/deterministic
# Higher (0.9) = More creative/diverse
```

### Max Tokens

```python
assistant = GeminiShoppingAssistant(
    max_tokens=2048  # Maximum response length
)
```

## Persistent Storage

### Using Redis Only (Caching)

```python
from gemini_session_storage import GeminiMemoryStorage

storage = GeminiMemoryStorage()  # Development
# or
system = IntegratedGeminiShoppingSystem(
    use_persistent_storage=True
    # Uses Redis by default if available
)
```

### Using PostgreSQL (Production)

```python
from gemini_session_storage import GeminiHybridSessionStorage

storage = GeminiHybridSessionStorage(
    redis_url="redis://localhost:6379/0",
    database_url="postgresql://user:password@localhost/gemini_shopping",
    enable_cache=True,
    enable_db=True
)
```

### Using Docker

```bash
# Redis
docker run -d -p 6379:6379 --name redis redis:latest

# PostgreSQL
docker run -d -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=gemini_shopping \
  --name postgres postgres:latest

# Or use docker-compose (see docker-compose.yml)
docker-compose up -d
```

## Error Handling

```python
response = assistant.ask("Find headphones", conversation_id=conv_id)

if 'error' in response:
    print(f"API Error: {response['error']}")
    # Handle error appropriately
else:
    products = response['products']
    # Process products
```

## Best Practices

1. **API Key Security**
   - Never hardcode API keys
   - Use environment variables
   - Rotate keys periodically

2. **Conversation Management**
   - Always store conversation IDs
   - Clean up ended conversations
   - Implement conversation timeout

3. **Error Handling**
   - Implement retry logic
   - Log errors for monitoring
   - Provide fallback responses

4. **Performance**
   - Use Redis for active conversations
   - Archive old conversations to database
   - Implement rate limiting

5. **Multi-Tenant**
   - Always scope by partner_id
   - Never mix tenant data
   - Use database for audit trail

## Monitoring & Logging

```python
# Track API usage
context = assistant.get_conversation_context(conv_id)
metrics = context['metrics']
for metric in metrics:
    print(f"Model: {metric['model']}")
    print(f"Tokens: {metric['total_tokens']}")

# Monitor conversations
sessions = system.list_user_sessions(user_id)
print(f"Active sessions: {len(sessions)}")
```

## Performance Tips

1. **Batch Operations**: Group multiple requests
2. **Caching**: Use Redis for frequently accessed data
3. **Model Selection**: Use gemini-2.0-flash for speed
4. **Async Processing**: Consider async for multiple users
5. **Database Indexing**: Index partner_id and user_id columns

## Limitations & Considerations

- Gemini API token limits apply
- Product information extracted from LLM (may need verification)
- Internet availability required for real product data
- Rate limiting depends on your API plan

## Support

For issues with:
- **Gemini API**: Visit [Google AI Documentation](https://ai.google.dev/gemini-api/docs)
- **Storage**: See configuration section above
- **This implementation**: Check GitHub issues or documentation

## License

Based on existing project structure. See LICENSE file.
