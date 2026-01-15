# Gemini Shopping Assistant - Architecture & Implementation Guide

## Overview

A complete Python implementation of a shopping assistant using Google's Gemini API. This system enables multi-turn product discovery conversations with full session management, persistent storage, and multi-tenant support.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│          User Interface / API Endpoints                     │
│  (Web API, CLI, Chat Interface, Mobile App, etc.)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│    IntegratedGeminiShoppingSystem                           │
│  - Orchestrates Assistant + Storage                         │
│  - Session Management                                       │
│  - Multi-tenant Support                                     │
│  - User Session Tracking                                    │
└───┬──────────────────────────────┬─────────────────────────┘
    │                              │
    ▼                              ▼
┌─────────────────────┐   ┌──────────────────────────┐
│ GeminiShoppingAssist│   │ GeminiSessionStorage     │
│                     │   │                          │
│ - Conversation mgmt │   │ - Memory Storage         │
│ - Product extraction│   │ - Redis Cache            │
│ - Multi-turn support│   │ - PostgreSQL Persistence│
│ - Message history   │   │ - Multi-tenant isolation │
└─────────────────────┘   └──────────────────────────┘
    │                              │
    ▼                              ▼
┌─────────────────────┐   ┌──────────────────────────┐
│ Google Gemini API   │   │ Backend Storage          │
│ (gemini-2.0-flash)  │   │ (Redis + PostgreSQL)     │
└─────────────────────┘   └──────────────────────────┘
```

## Component Breakdown

### 1. **GeminiShoppingAssistant** (`gemini_shopping_assistant.py`)

Core conversation manager interfacing with Google Gemini API.

**Responsibilities:**
- Manage multi-turn conversations
- Extract product information from responses
- Track conversation history
- Generate API calls to Gemini

**Key Classes:**

```python
class GeminiShoppingAssistant:
    """Main conversation orchestrator"""
    - __init__(api_key, model, temperature, max_tokens)
    - start_conversation(user_id, partner_id, metadata)
    - ask(question, conversation_id, user_id, partner_id)
    - get_conversation_history(conversation_id)
    - get_conversation_context(conversation_id)
    - end_conversation(conversation_id)
    - get_active_conversations(user_id)

class ConversationContext:
    """Maintains conversation state"""
    - conversation_id: str
    - user_id: str
    - partner_id: str
    - messages: List[ConversationMessage]
    - products_found: List[Product]
    - metrics: List[ResponseMetrics]

class Product:
    """Product information model"""
    - name: str
    - price: float
    - currency: str
    - url: str
    - image_url: str
    - description: str
    - rating: float
    - source: str

class ConversationMessage:
    """Message in conversation"""
    - role: ConversationRole (USER/ASSISTANT)
    - content: str
    - timestamp: datetime
    - products: List[Product]
```

**Product Extraction Flow:**
```
Gemini Response
    ↓
    ├─ Parse PRODUCT: blocks
    ├─ Extract PRICE, URL, IMAGE, DESCRIPTION, RATING
    ├─ Create Product objects
    └─ Return in response
```

### 2. **GeminiSessionStorage** (`gemini_session_storage.py`)

Persistent session storage with multiple backends.

**Storage Hierarchy:**
```
GeminiSessionStorageInterface (Abstract)
    ├─ GeminiMemoryStorage (In-memory, development)
    ├─ GeminiRedisCache (Caching layer)
    └─ GeminiHybridSessionStorage (Redis + PostgreSQL)
```

**Storage Methods:**
```python
create_conversation(conversation_data) -> bool
get_conversation(conversation_id, partner_id) -> Dict
update_conversation(conversation_id, partner_id, updates) -> bool
add_message(conversation_id, partner_id, message_data) -> bool
delete_conversation(conversation_id, partner_id) -> bool
list_conversations(partner_id, user_id) -> List[Dict]
```

**Database Schema:**

```sql
-- Conversations Table
CREATE TABLE gemini_conversations (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    partner_id VARCHAR(255) NOT NULL,     -- Multi-tenant key
    user_id VARCHAR(255) NOT NULL,        -- User identifier
    title VARCHAR(255),                   -- Session title
    metadata JSON,                        -- Custom metadata
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- Messages Table
CREATE TABLE gemini_messages (
    id VARCHAR(36) PRIMARY KEY,           -- UUID
    conversation_id VARCHAR(36) NOT NULL, -- FK to conversations
    partner_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,            -- 'user' or 'model'
    content TEXT NOT NULL,
    products JSON,                        -- Product array
    timestamp DATETIME NOT NULL
);
```

### 3. **IntegratedGeminiShoppingSystem** (`gemini_integrated_system.py`)

High-level orchestration combining assistant and storage.

**Responsibilities:**
- User session management
- Request routing to assistant
- Persistent storage coordination
- Multi-tenant isolation
- Error handling

**Key Methods:**
```python
class IntegratedGeminiShoppingSystem:
    - __init__(api_key, use_persistent_storage, redis_url, database_url)
    - start_shopping_session(user_id, partner_id, title, metadata)
    - ask_product_question(question, conversation_id, user_id, partner_id)
    - get_session_details(conversation_id, partner_id)
    - list_user_sessions(user_id, partner_id)
    - end_session(conversation_id, partner_id, save_transcript)
    - search_products(query, user_id, partner_id, max_results)
```

## Data Flow Examples

### Example 1: Simple Question

```
User Input: "Find noise-canceling headphones under $200"
    ↓
IntegratedGeminiShoppingSystem.start_shopping_session()
    ├─ Creates ConversationContext
    └─ Stores in persistent storage
    ↓
IntegratedGeminiShoppingSystem.ask_product_question()
    ├─ Adds message to context
    ├─ Calls GeminiShoppingAssistant.ask()
    │   ├─ Builds conversation history
    │   ├─ Calls Gemini API with prompt + history
    │   └─ Extracts products from response
    ├─ Stores messages in persistent storage
    └─ Updates conversation metadata
    ↓
Response: {
    "conversation_id": "...",
    "response": "Assistant's recommendation...",
    "products": [
        {"name": "Sony...", "price": 349.99, "url": "..."},
        {"name": "Apple...", "price": 399.99, "url": "..."}
    ]
}
```

### Example 2: Multi-Turn Conversation

```
Turn 1: User asks "Find headphones under $200"
    ├─ Context: [Message(role=user, content="Find headphones...")]
    ├─ Gemini receives: system_prompt + [Message]
    └─ Context updated: [Message(user), Message(assistant)]

Turn 2: User asks "Which is best for travel?"
    ├─ Context: [Message(user, "Find headphones..."), 
    │             Message(assistant, "Here are..."),
    │             Message(user, "Which is best?")]
    ├─ Gemini receives: system_prompt + [All 3 messages]
    └─ Gemini can reference previous products
    └─ Context updated: [4 messages, 6-8 products]
```

### Example 3: Multi-Tenant Isolation

```
User "alice" @ "electronics_store"
    ├─ start_shopping_session("alice", "electronics_store")
    │   └─ conv_id_1 created
    └─ Stored as: electronics_store:alice:conv_id_1

User "alice" @ "fashion_store"
    ├─ start_shopping_session("alice", "fashion_store")
    │   └─ conv_id_2 created
    └─ Stored as: fashion_store:alice:conv_id_2

Data is strictly separated:
- electronics_store cannot access fashion_store conversations
- Queries filtered by (partner_id, user_id)
- Index on (partner_id, user_id) for performance
```

## API Integration

### Google Gemini API Integration

```python
import google.generativeai as genai

# Configure
genai.configure(api_key=api_key)

# Create model
client = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=genai.types.GenerationConfig(
        temperature=0.7,
        max_output_tokens=2048
    )
)

# Generate content
response = client.generate_content(
    [
        {"text": system_prompt},
        {"role": "user", "parts": [{"text": "Turn 1 user message"}]},
        {"role": "model", "parts": [{"text": "Turn 1 assistant response"}]},
        {"text": "Turn 2 user message"}
    ]
)
```

**Response Structure:**
```
response.text -> Full response as string
response.usage -> Token usage info
response.candidates[0].content -> Content object
```

## Product Extraction Algorithm

```python
def _extract_products(response_text: str) -> List[Product]:
    """
    Algorithm:
    1. Split response by "PRODUCT:" markers
    2. For each product block:
       a. First line = product name
       b. Parse "KEY: value" lines
          - PRICE: Extract number, remove $, convert to float
          - URL: Extract URL
          - IMAGE: Extract image URL
          - DESCRIPTION: Extract features
          - RATING: Extract rating number
    3. Validate product has at least name and price
    4. Return Product objects
    """
    
    products = []
    blocks = response.split("PRODUCT:")
    
    for block in blocks[1:]:  # Skip pre-first block
        # Parse lines
        lines = block.strip().split("\n")
        product_data = {
            "name": lines[0].strip(),
            "price": 0.0,
            # ... parse other fields
        }
        # Create Product
        products.append(Product(**product_data))
    
    return products
```

## Session Lifecycle

```
CREATE SESSION
    ↓ start_shopping_session()
    ├─ Generate UUID
    ├─ Create ConversationContext in memory
    └─ Store in persistent storage
    ↓
ACTIVE SESSION
    ├─ ask_product_question() called multiple times
    ├─ Messages added to context
    ├─ Messages persisted to storage
    └─ Last accessed timestamp updated
    ↓
GET SESSION INFO
    ├─ Retrieve from memory (fast)
    ├─ Or from cache (Redis, ~1ms)
    └─ Or from database (PostgreSQL, ~10-50ms)
    ↓
END SESSION
    ├─ Save transcript (optional)
    ├─ Remove from memory
    └─ Mark as archived in storage
    ↓
CLEANUP
    └─ Delete old sessions (configurable TTL)
```

## Performance Characteristics

### Latency
```
Operation                    Latency
─────────────────────────────────────
Get conversation (memory)    <1ms
Get conversation (Redis)     ~1-5ms
Get conversation (DB)        ~10-50ms
Gemini API call             ~2-5 seconds
Extract products            ~10-50ms
Store message               ~5-20ms
```

### Scalability
```
In-Memory Storage:
  - Limited by RAM
  - Good for testing/dev
  - Not suitable for prod

Redis + PostgreSQL:
  - Redis: ~100k conversations/server
  - PostgreSQL: Unlimited (with proper indexes)
  - Can scale horizontally with load balancer
```

## Error Handling

```
Scenarios:
1. API Key Missing
   → Raise ValueError immediately
   → Clear error message

2. Gemini API Timeout
   → Catch in ask()
   → Return error response
   → Store error in context

3. Storage Connection Down
   → If Redis down: Fall back to memory
   → If DB down: Use Redis cache only
   → Log error for monitoring

4. Invalid Product Data
   → Skip malformed products
   → Log warning
   → Continue with valid products

5. Multi-tenant Access Violation
   → Filter by partner_id at storage layer
   → Return None if partner mismatch
   → Log security event
```

## Security Considerations

1. **API Key Protection**
   - Never log API keys
   - Use environment variables
   - Rotate keys regularly

2. **Multi-Tenant Isolation**
   - All queries filtered by partner_id
   - No cross-partner data access
   - Database indexes on partner_id

3. **User Data**
   - Delete conversations on request (GDPR)
   - Audit logging for compliance
   - Encryption at rest (optional)

4. **Rate Limiting**
   - Implement per-user limits
   - Implement per-API-key limits
   - Queue requests if needed

5. **Input Validation**
   - Sanitize user questions
   - Validate conversation IDs
   - Check partner_id matches

## Configuration Management

```python
# Environment-based config
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_CONVERSATION_LENGTH = int(os.getenv("MAX_CONVERSATION_LENGTH", "50"))
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "24"))
```

## Testing Strategy

```python
# Unit Tests
test_product_extraction()
test_message_formatting()
test_conversation_context()

# Integration Tests
test_multi_turn_conversation()
test_storage_persistence()
test_multi_tenant_isolation()

# End-to-End Tests
test_full_shopping_session()
test_error_handling()
test_concurrent_sessions()

# Performance Tests
test_large_conversation_history()
test_storage_throughput()
test_concurrent_users()
```

## Deployment Options

### Option 1: Standalone Python
```bash
pip install -r requirements.txt
export GEMINI_API_KEY="..."
python app.py
```

### Option 2: Docker
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV GEMINI_API_KEY=...
CMD ["python", "app.py"]
```

### Option 3: Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gemini-shopping-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: gemini-shopping:latest
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-secrets
              key: api-key
        - name: REDIS_URL
          value: redis://redis-service:6379
        - name: DATABASE_URL
          value: postgresql://postgres-service/gemini_shopping
```

## Monitoring & Observability

```python
# Metrics to track
- Total conversations created
- Average conversation length
- API response times
- Product extraction success rate
- Storage operation latencies
- Error rates by type
- Concurrent active sessions

# Logging
- DEBUG: Low-level API calls
- INFO: Session starts/ends
- WARNING: Slow operations
- ERROR: API failures
- CRITICAL: Data loss risks

# Alerts
- API latency > 10s
- Error rate > 5%
- Storage connection down
- API key expiration
```

## Future Enhancements

1. **Vector Embeddings**: Store product embeddings for semantic search
2. **Recommendation Engine**: ML model for personalized recommendations
3. **Async/Streaming**: Stream responses as Gemini generates them
4. **Image Generation**: Generate product comparison images
5. **Multi-language**: Support conversations in multiple languages
6. **Product Verification**: Verify products are real (price checking)
7. **User Preferences**: Learn user preferences over time
8. **Browsing Integration**: Fetch real product data from web

---

**Last Updated**: January 2025
**Status**: Production Ready
