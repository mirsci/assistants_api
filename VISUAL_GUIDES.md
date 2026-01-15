# Gemini Shopping Assistant - Visual Guides

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          END USERS                                  │
│  (Web Browser, Mobile App, CLI, Chatbot Interface, etc.)           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Your API/Web  │
                    │   Application   │
                    └────────┬────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│         IntegratedGeminiShoppingSystem                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ • Session management                                         │  │
│  │ • User tracking                                              │  │
│  │ • Multi-tenant isolation                                     │  │
│  │ • Orchestration                                              │  │
│  └──────────┬──────────────────────────────┬────────────────────┘  │
└─────────────┼──────────────────────────────┼──────────────────────┘
              │                              │
    ┌─────────▼────────┐          ┌──────────▼──────────┐
    │  GeminiShopping  │          │ GeminiSessionStorage│
    │   Assistant      │          │                     │
    │                  │          │ ┌─────────────────┐ │
    │ • Conversations  │          │ │ MemoryStorage   │ │
    │ • Product        │          │ │ (Development)   │ │
    │   extraction     │          │ └─────────────────┘ │
    │ • Message mgmt   │          │ ┌─────────────────┐ │
    │ • History        │          │ │ RedisCache      │ │
    │ • API calls      │          │ │ (Active cache)  │ │
    └────────┬─────────┘          │ └─────────────────┘ │
             │                    │ ┌─────────────────┐ │
             │                    │ │PostgreSQL       │ │
             │                    │ │(Persistence)    │ │
             │                    │ └─────────────────┘ │
             │                    └──────────────────────┘
    ┌────────▼─────────┐
    │ Google Gemini    │
    │ API              │
    │                  │
    │ gemini-2.0-flash │
    │ (or other model) │
    └──────────────────┘
```

## Data Flow Diagram

### Single Question
```
User Input
    │
    ▼
┌─────────────────────────┐
│  ask_product_question() │
└─────────────────────────┘
    │
    ├─→ Add message to context
    │
    ├─→ Build conversation history
    │
    ├─→ Call Gemini API ──────────┐
    │                             │
    │                             ▼
    │                      Gemini API
    │                             │
    │                             ▼
    │                      AI Response
    │◀────────────────────────────┘
    │
    ├─→ Extract products
    │   ├─ Parse PRODUCT: blocks
    │   ├─ Extract PRICE, URL, IMAGE, etc.
    │   └─ Create Product objects
    │
    ├─→ Store in context
    │
    ├─→ Store in persistent storage
    │
    └─→ Return response
        ├─ conversation_id
        ├─ response text
        ├─ products array
        └─ metadata
```

### Multi-Turn Conversation
```
Turn 1: "Find headphones under $200"
    ├─ Create conversation
    ├─ Send: [system_prompt, user_msg]
    ├─ Receive: assistant_response
    ├─ Extract: [product1, product2, product3]
    └─ Store: context=[msg1, msg2], products=[p1,p2,p3]

Turn 2: "Which is best for travel?"
    ├─ Load conversation history: [msg1, msg2]
    ├─ Send: [system_prompt, msg1, msg2, user_query]
    ├─ Gemini sees: previous Q&A + product info
    ├─ Receive: comparative response
    ├─ Extract: [product2, product3 details]
    └─ Store: context=[msg1,msg2,msg3,msg4], products=[p1,p2,p3]

Turn 3: "Show alternatives in the $150-250 range"
    ├─ Load conversation history: [msg1, msg2, msg3, msg4]
    ├─ Send: [system_prompt, msg1, msg2, msg3, msg4, user_query]
    ├─ Gemini sees: all previous context
    ├─ Receive: alternative options response
    ├─ Extract: [product4, product5, product6]
    └─ Store: context=[msg1-6], products=[p1-p6]
```

## Multi-Tenant Isolation

```
Database Structure:
┌────────────────────────────────────────────────┐
│        gemini_conversations table              │
├────────────────────────────────────────────────┤
│ id  │partner_id│user_id│title│created_at      │
├─────┼──────────┼───────┼─────┼─────────────────┤
│uuid1│store_a   │user1  │...  │2025-01-11      │
│uuid2│store_b   │user1  │...  │2025-01-11      │ Same user
│uuid3│store_a   │user2  │...  │2025-01-11      │ Different stores
│uuid4│store_a   │user1  │...  │2025-01-11      │ Multiple sessions
└─────┴──────────┴───────┴─────┴─────────────────┘

Query Examples:
┌─────────────────────────────────────────────────┐
│ Get user1's sessions at store_a                │
│ WHERE partner_id='store_a' AND user_id='user1' │
│ Result: [uuid1, uuid4]                          │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Get user1's all sessions                        │
│ WHERE user_id='user1'                           │
│ Result: [uuid1, uuid2, uuid4]                   │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ Get store_a's conversations                     │
│ WHERE partner_id='store_a'                      │
│ Result: [uuid1, uuid3, uuid4]                   │
└─────────────────────────────────────────────────┘
```

## Product Extraction Process

```
Assistant Response:
────────────────────────────────────────────────────────────────
"Here are excellent noise-canceling headphones under $200:

PRODUCT: Sony WH-1000XM4
PRICE: $348
URL: https://amazon.com/Sony-WH-1000XM4
IMAGE: https://cdn.com/sony-wh.jpg
DESCRIPTION: Industry-leading noise cancellation, 8hr battery
RATING: 4.8

PRODUCT: Apple AirPods Pro
PRICE: $249
URL: https://apple.com/airpods-pro
IMAGE: https://cdn.com/airpods.jpg
DESCRIPTION: Spatial audio, H1 chip
RATING: 4.6"
────────────────────────────────────────────────────────────────
    │
    ▼
Parse and Extract:
────────────────────────────────────────────────────────────────
1. Split by "PRODUCT:"
   ├─ Block 1: "Sony WH-1000XM4\nPRICE: $348\nURL:..."
   └─ Block 2: "Apple AirPods Pro\nPRICE: $249\nURL:..."

2. Parse each block
   ├─ Line 1 = name
   ├─ Find PRICE, extract number (348 → 348.0)
   ├─ Find URL, extract link
   ├─ Find IMAGE, extract URL
   ├─ Find DESCRIPTION, extract text
   └─ Find RATING, extract number (4.8 → 4.8)

3. Create Product objects
   ├─ Product(name="Sony WH-1000XM4", price=348.0, ...)
   └─ Product(name="Apple AirPods Pro", price=249.0, ...)

4. Return as list of Product objects
────────────────────────────────────────────────────────────────
    │
    ▼
Response Object:
────────────────────────────────────────────────────────────────
{
    "products": [
        {
            "name": "Sony WH-1000XM4",
            "price": 348.0,
            "url": "https://amazon.com/...",
            "image_url": "https://cdn.com/sony-wh.jpg",
            "description": "Industry-leading...",
            "rating": 4.8
        },
        {
            "name": "Apple AirPods Pro",
            "price": 249.0,
            "url": "https://apple.com/...",
            "image_url": "https://cdn.com/airpods.jpg",
            "description": "Spatial audio...",
            "rating": 4.6
        }
    ]
}
────────────────────────────────────────────────────────────────
```

## Storage Decision Tree

```
                    Need to store sessions?
                            │
                ┌───────────┴───────────┐
                │                       │
               NO                      YES
                │                       │
                ▼                       ▼
         Use Memory Only        Multi-instance app?
         (Development only)             │
                              ┌─────────┴─────────┐
                              │                   │
                             NO                  YES
                              │                   │
                              ▼                   ▼
                       Single Instance      Multiple Instances
                              │                   │
                              ├─ Use Redis   Use Redis Cache
                              │  (optional)   (required)
                              │                   │
                              └─ Archive old  ├─ Use PostgreSQL
                                 sessions        for persistence
                                              │
                                              └─ Scale horizontally
```

## Session Lifecycle

```
CREATE
    │
    ├─ Generate UUID for conversation_id
    ├─ Create ConversationContext in memory
    ├─ Store in persistent storage
    └─ Return conversation_id
    │
    ▼
ACTIVE (Using)
    │
    ├─ ask() called multiple times
    ├─ Messages added to context
    ├─ Products extracted and stored
    ├─ Storage updated with each turn
    └─ Last accessed timestamp refreshed
    │
    ├─────────────────────────┐
    │                         │
    ▼                         ▼
Get Session Details    List Sessions
    │                        │
    ├─ Load from memory  └─ Query storage
    ├─ Check Redis cache     by user_id
    └─ Fall back to DB       or partner_id
    │
    ▼
ARCHIVE/DELETE
    │
    ├─ Optional: Save transcript
    ├─ Remove from memory
    ├─ Mark/delete in storage
    └─ Free resources
    │
    ▼
CLEANUP
    │
    └─ Delete old sessions (TTL)
       or on demand (GDPR)
```

## Error Handling Flow

```
User Request
    │
    ▼
Try to process
    │
    ├─────────────────────┐
    │                     │
Success               Error
    │                     │
    ▼                     ▼
Return Response    What went wrong?
                        │
        ┌───────────────┼───────────────┐
        │               │               │
    API Error        Storage Down     Input Invalid
        │               │               │
        ▼               ▼               ▼
Return error msg   Use fallback    Return validation
with details       (memory/cache)   error message
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
                Log error for debugging
                        │
                        ▼
                Return to user gracefully
```

## Performance Characteristics

```
Operation Timeline (single user):
────────────────────────────────────

User Types Question
    │ (0ms - human input)
    │
    ▼
Request hits API (1-2ms)
    │
    ├─→ Add message to context (1-5ms)
    │
    ├─→ Build conversation history (2-10ms)
    │
    ├─→ Call Gemini API (2000-5000ms) ◄─ Slowest step
    │   │ (Time spent in Gemini processing)
    │
    ├─→ Extract products (10-50ms)
    │
    ├─→ Store in context (1-5ms)
    │
    ├─→ Store in Redis cache (1-5ms)
    │
    ├─→ Store in DB (10-50ms)
    │
    └─→ Return response (1-2ms)

Total: 2030-5117ms ≈ 2-5 seconds

Subsequent access of same conversation:
    ├─→ Load from memory (0-1ms) ◄─ Fastest
    │ OR
    ├─→ Load from Redis (1-5ms) ◄─ Fast
    │ OR
    └─→ Load from PostgreSQL (10-50ms) ◄─ Slowest but durable
```

## Scalability Model

```
DEVELOPMENT
├─ Single instance
├─ In-memory storage only
└─ Works for 1-10 users

PRODUCTION (1000+ users)
├─ Load Balancer
│   ├─ API Instance 1 ──┐
│   ├─ API Instance 2 ──┼─→ Redis Cache ──→ PostgreSQL DB
│   ├─ API Instance 3 ──┤   (Shared)       (Shared)
│   └─ API Instance N ──┘

Features:
├─ Horizontal scaling (add instances)
├─ Shared Redis for consistency
├─ Shared PostgreSQL for persistence
├─ Each instance has local memory
└─ Conversations can move between instances
```

---

These diagrams help visualize:
- System architecture and components
- Data flow through multi-turn conversations
- Multi-tenant isolation mechanisms
- Product extraction process
- Storage options and decision tree
- Session lifecycle management
- Error handling paths
- Performance bottlenecks
- Scalability approach
