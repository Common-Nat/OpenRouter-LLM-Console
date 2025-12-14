# Rate Limiting Implementation

## Overview

Rate limiting has been implemented across all API endpoints to protect against abuse, DDoS attacks, and excessive resource consumption. The implementation uses [SlowAPI](https://github.com/laurentS/slowapi), a FastAPI extension that provides flexible, IP-based rate limiting.

## Architecture

### Components

1. **Rate Limiter** ([ratelimit.py](app/core/ratelimit.py))
   - Centralized rate limiting configuration
   - IP-based client identification via `get_remote_address()`
   - Configurable limits per endpoint type

2. **Middleware Integration** ([main.py](app/main.py))
   - `app.state.limiter` registers the limiter instance
   - Custom exception handler for `RateLimitExceeded` errors
   - Returns HTTP 429 (Too Many Requests) with retry info

3. **Endpoint Decorators**
   - `@limiter.limit()` decorator applied to individual routes
   - Requires `Request` parameter to access client IP

## Rate Limit Tiers

| Endpoint Category | Limit | Rationale |
|------------------|-------|-----------|
| **Stream** | 20/minute | Most expensive - calls OpenRouter API |
| **Model Sync** | 5/hour | External API call, infrequent operation |
| **Document Upload** | 30/minute | Resource intensive (file I/O, storage) |
| **Sessions** | 60/minute | Standard CRUD operations |
| **Messages** | 100/minute | High-frequency user interactions |
| **Profiles** | 60/minute | Standard CRUD operations |
| **Models List** | 120/minute | Read-heavy, cacheable |
| **Usage Logs** | 120/minute | Analytics queries |
| **Health Check** | 300/minute | Monitoring endpoints |

## Configuration

### Environment Variables

Add these to your `.env` file (optional - defaults shown):

```bash
# Enable/disable rate limiting
RATE_LIMIT_ENABLED=true

# Custom rate limits (override defaults)
RATE_LIMIT_STREAM=20 per minute
RATE_LIMIT_MODEL_SYNC=5 per hour
RATE_LIMIT_UPLOAD=30 per minute
```

### Format

Rate limit strings follow the pattern: `"X per Y"` where:
- `X` = number of requests
- `Y` = time period: `second`, `minute`, `hour`, `day`

Examples:
- `"10 per second"`
- `"100 per minute"`
- `"1000 per hour"`
- `"5000 per day"`

## How It Works

### Request Flow

1. **Client sends request** → FastAPI receives it
2. **SlowAPI checks limit** → Looks up client IP in memory store
3. **Under limit?** → Request proceeds normally
4. **Over limit?** → Returns HTTP 429 with headers:
   - `X-RateLimit-Limit`: Total requests allowed
   - `X-RateLimit-Remaining`: Requests left in window
   - `X-RateLimit-Reset`: Unix timestamp when limit resets
   - `Retry-After`: Seconds until client can retry

### Example Response (Rate Limited)

```json
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1702567890
Retry-After: 60

{
  "detail": "Rate limit exceeded: 20 per 1 minute"
}
```

## Adding Rate Limits to New Endpoints

When creating new routes, apply rate limiting:

```python
from fastapi import APIRouter, Request
from ...core.ratelimit import limiter, RATE_LIMITS

router = APIRouter(prefix="/my-route", tags=["my-tag"])

@router.post("/endpoint")
@limiter.limit(RATE_LIMITS["sessions"])  # Use existing tier
async def my_endpoint(request: Request, ...):
    # Route logic
    pass
```

**Important:** The `Request` parameter must be included for SlowAPI to extract the client IP.

## Testing Rate Limits

### Manual Testing

```bash
# Test streaming endpoint limit (20/minute)
for i in {1..25}; do
  curl "http://localhost:8000/api/stream?session_id=test&model_id=test" &
done

# Expected: First 20 succeed, remaining 5 return 429
```

### Python Test

```python
import httpx
import asyncio

async def test_rate_limit():
    async with httpx.AsyncClient() as client:
        for i in range(25):
            response = await client.get(
                "http://localhost:8000/api/stream",
                params={"session_id": "test", "model_id": "test"}
            )
            print(f"Request {i+1}: {response.status_code}")
            if response.status_code == 429:
                print(f"Rate limited! Retry after: {response.headers.get('Retry-After')}s")

asyncio.run(test_rate_limit())
```

## Backend Storage

SlowAPI uses an **in-memory** store by default:
- Fast, zero-config
- Resets when server restarts
- Per-process (doesn't share across workers)

### Production Considerations

For multi-worker deployments, consider using Redis:

```python
# In ratelimit.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"
)
```

## Security Benefits

1. **DDoS Protection** - Limits impact of automated attacks
2. **Cost Control** - Prevents runaway OpenRouter API costs
3. **Fair Usage** - Ensures equal access for all users
4. **Resource Protection** - Prevents database/CPU exhaustion

## Monitoring

Rate limit metrics are logged automatically:

```json
{
  "timestamp": "2024-12-14T10:30:00Z",
  "level": "WARNING",
  "message": "Rate limit exceeded",
  "path": "/api/stream",
  "client_ip": "192.168.1.100",
  "limit": "20 per minute"
}
```

## Disabling Rate Limits (Not Recommended)

For local development only:

```bash
# In .env
RATE_LIMIT_ENABLED=false
```

Then modify [main.py](app/main.py) to conditionally register the limiter:

```python
if settings.rate_limit_enabled:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

## References

- [SlowAPI Documentation](https://slowapi.readthedocs.io/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [HTTP 429 Status Code](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429)
