# API Documentation

## Authentication

BruceWayneV1 uses JWT (JSON Web Token) for authentication. All protected endpoints require a valid Bearer token in the `Authorization` header.

### Authentication Flow

```
1. Client sends credentials to POST /auth/login
2. Server validates credentials and returns access + refresh tokens
3. Client includes access token in subsequent requests:
   Authorization: Bearer <access_token>
4. When the access token expires, client calls POST /auth/refresh
   with the refresh token to obtain a new access token
5. Refresh tokens have a longer TTL and are single-use
```

### Token Structure

```json
{
  "sub": "user_id",
  "role": "admin",
  "exp": 1700000000,
  "iat": 1699996400,
  "jti": "unique-token-id"
}
```

---

## Endpoints

### Authentication

#### POST /auth/login

Authenticate a user and receive tokens.

**Request:**
```json
{
  "username": "operator",
  "password": "secure_password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### POST /auth/register

Register a new user account.

**Request:**
```json
{
  "username": "new_user",
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "username": "new_user",
  "email": "user@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### POST /auth/refresh

Refresh an expired access token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### System

#### GET /health

Health check endpoint (no authentication required).

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 86400,
  "services": {
    "database": "connected",
    "redis": "connected",
    "ai_engine": "ready"
  }
}
```

#### GET /api/v1/status

Detailed system status (requires authentication).

**Response (200):**
```json
{
  "environment": "production",
  "active_model": "deepseek",
  "memory_usage_mb": 1024,
  "active_connections": 12,
  "uptime_seconds": 86400
}
```

---

### Chat and Interaction

#### POST /api/v1/chat

Send a message and receive an AI response.

**Request:**
```json
{
  "message": "Analyze the current market conditions",
  "context": "trading",
  "session_id": "optional-session-uuid"
}
```

**Response (200):**
```json
{
  "response": "Based on current data...",
  "session_id": "session-uuid",
  "model_used": "deepseek",
  "emotion_state": "analytical",
  "tokens_used": 350,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

### Trading

#### GET /api/v1/trading/positions

List current trading positions.

**Response (200):**
```json
{
  "positions": [
    {
      "id": "pos-uuid",
      "symbol": "BTC/USD",
      "side": "long",
      "size": 0.5,
      "entry_price": 42000.00,
      "current_price": 43500.00,
      "pnl": 750.00,
      "opened_at": "2024-01-01T10:00:00Z"
    }
  ],
  "total_pnl": 750.00
}
```

#### POST /api/v1/trading/execute

Execute a trade order.

**Request:**
```json
{
  "symbol": "BTC/USD",
  "side": "buy",
  "size": 0.1,
  "order_type": "market",
  "strategy": "momentum"
}
```

**Response (201):**
```json
{
  "order_id": "order-uuid",
  "status": "filled",
  "symbol": "BTC/USD",
  "side": "buy",
  "size": 0.1,
  "fill_price": 43500.00,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### GET /api/v1/trading/strategies

List available trading strategies.

**Response (200):**
```json
{
  "strategies": [
    {
      "id": "momentum",
      "name": "Momentum Strategy",
      "status": "active",
      "win_rate": 0.62,
      "sharpe_ratio": 1.8
    }
  ]
}
```

---

### AI and Cognitive

#### POST /api/v1/ai/infer

Run inference with a specified or auto-selected model.

**Request:**
```json
{
  "prompt": "What are the risks of this position?",
  "model": "deepseek",
  "max_tokens": 500,
  "temperature": 0.7
}
```

**Response (200):**
```json
{
  "result": "The primary risks include...",
  "model": "deepseek",
  "tokens_used": 280,
  "latency_ms": 450
}
```

#### GET /api/v1/ai/models

List available AI models and their status.

**Response (200):**
```json
{
  "models": [
    {
      "id": "deepseek",
      "name": "DeepSeek Engine",
      "status": "loaded",
      "memory_mb": 4096
    },
    {
      "id": "phi3",
      "name": "Phi-3 Kernel",
      "status": "available",
      "memory_mb": 2048
    }
  ]
}
```

#### POST /api/v1/cognitive/reflect

Trigger a self-reflection cycle.

**Request:**
```json
{
  "depth": "deep",
  "focus": "recent_decisions"
}
```

**Response (200):**
```json
{
  "reflection": "Upon reviewing recent actions...",
  "insights": ["insight_1", "insight_2"],
  "confidence": 0.85,
  "duration_ms": 1200
}
```

---

## WebSocket Protocol

### Connection

```
ws://host:8000/ws?token=<jwt_access_token>
```

### Message Format

All messages use JSON with a `type` field for routing:

**Client to Server:**
```json
{
  "type": "chat",
  "payload": {
    "message": "Hello Bruce"
  }
}
```

```json
{
  "type": "subscribe",
  "payload": {
    "channel": "market:BTC/USD"
  }
}
```

**Server to Client:**
```json
{
  "type": "chat_response",
  "payload": {
    "message": "Greetings. How can I assist?",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

```json
{
  "type": "market_update",
  "payload": {
    "symbol": "BTC/USD",
    "price": 43500.00,
    "change_24h": 2.5,
    "timestamp": "2024-01-01T12:00:01Z"
  }
}
```

```json
{
  "type": "system_alert",
  "payload": {
    "level": "warning",
    "message": "High volatility detected",
    "timestamp": "2024-01-01T12:00:02Z"
  }
}
```

### Message Types

| Type              | Direction       | Description                    |
|-------------------|-----------------|--------------------------------|
| `chat`            | Client -> Server| Send chat message              |
| `chat_response`   | Server -> Client| AI response                    |
| `subscribe`       | Client -> Server| Subscribe to data channel      |
| `unsubscribe`     | Client -> Server| Unsubscribe from channel       |
| `market_update`   | Server -> Client| Real-time price update         |
| `system_alert`    | Server -> Client| System notification            |
| `ping`            | Bidirectional   | Keep-alive                     |
| `pong`            | Bidirectional   | Keep-alive response            |

---

## Error Codes

All error responses follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {}
  }
}
```

### HTTP Status Codes

| Code | Error Code              | Description                          |
|------|-------------------------|--------------------------------------|
| 400  | `INVALID_REQUEST`       | Malformed request body or parameters |
| 401  | `UNAUTHORIZED`          | Missing or invalid authentication    |
| 401  | `TOKEN_EXPIRED`         | JWT access token has expired         |
| 403  | `FORBIDDEN`             | Insufficient permissions             |
| 404  | `NOT_FOUND`             | Resource does not exist              |
| 409  | `CONFLICT`              | Resource conflict (duplicate, etc.)  |
| 422  | `VALIDATION_ERROR`      | Request validation failed            |
| 429  | `RATE_LIMITED`          | Too many requests                    |
| 500  | `INTERNAL_ERROR`        | Unexpected server error              |
| 503  | `SERVICE_UNAVAILABLE`   | Dependency unavailable               |
| 503  | `MODEL_UNAVAILABLE`     | Requested AI model not loaded        |

### WebSocket Close Codes

| Code | Description                     |
|------|---------------------------------|
| 1000 | Normal closure                  |
| 1008 | Authentication failed           |
| 1011 | Internal server error           |
| 4000 | Invalid message format          |
| 4001 | Rate limited                    |
| 4002 | Session expired                 |
