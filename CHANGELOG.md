# Changelog

All notable changes to the OpenRouter LLM Console project are documented here.

## [Unreleased]

### Added
- Documentation reorganization with `docs/` directory structure

---

## December 14, 2025

### Rate Limiting Improvements

**Added:**
- `X-RateLimit-Limit` response headers on all endpoints
- All 9 rate limits now configurable via environment variables
- Comprehensive rate limiting documentation

**Changed:**
- Model Sync limit increased: `5 per hour` → `60 per hour` (12x)
- Document Upload limit increased: `30 per minute` → `50 per minute` (66%)

**Environment Variables Added:**
- `RATE_LIMIT_SESSIONS`
- `RATE_LIMIT_MESSAGES`
- `RATE_LIMIT_PROFILES`
- `RATE_LIMIT_MODELS_LIST`
- `RATE_LIMIT_USAGE_LOGS`
- `RATE_LIMIT_HEALTH_CHECK`

---

## December 2025 - Feature Implementations

### Full-Text Search (FTS5)

**Added:**
- SQLite FTS5-powered message search across all history
- Advanced query syntax: exact phrases, exclusions, prefix matching
- Smart filtering: by session, date range, model, session type
- BM25 relevance ranking with highlighted snippets
- Debounced search with 300ms delay
- SearchBar component with real-time filtering
- Migration 003: `messages_fts` virtual table with auto-sync triggers

**Files:**
- `backend/migrations/003_add_fts_search.sql`
- `backend/migrations/003_add_fts_search_down.sql`
- `frontend/src/components/SearchBar.jsx`
- `frontend/src/hooks/useSearch.js`

**Performance:**
- <10ms for 1,000 messages
- ~50ms for 10,000 messages
- ~200ms for 100,000 messages

---

### Error Handling Improvements

**Added:**
- Frontend timeout handling (configurable, default 5 minutes)
- EventSource error catching with proper cleanup
- Connection state tracking and descriptive error messages
- Race condition prevention in useStream hook

**Changed:**
- Backend validation errors now return SSE events instead of HTTPException
- All error paths include structured logging with request IDs
- Standardized error event format with error types

**Files:**
- `frontend/src/hooks/useStream.js` - Enhanced error handling
- `backend/app/api/routes/stream.py` - SSE error events
- `backend/app/services/openrouter.py` - Structured error logging
- `backend/tests/test_stream_errors.py` - Comprehensive test suite

---

### Structured Error Responses

**Added:**
- `backend/app/core/errors.py` - Error infrastructure with ErrorDetail model
- Machine-readable error codes across all endpoints
- Consistent error response format with resource context

**Error Codes:**
- 404: `SESSION_NOT_FOUND`, `PROFILE_NOT_FOUND`, `DOCUMENT_NOT_FOUND`, etc.
- 400: `MISSING_API_KEY`, `MISSING_FILENAME`
- 500: `FILE_SAVE_FAILED`, `OPENROUTER_ERROR`, `STREAM_ERROR`

**Response Format:**
```json
{
  "error_code": "SESSION_NOT_FOUND",
  "message": "Session not found",
  "resource_type": "session",
  "resource_id": "abc-123",
  "details": null
}
```

---

### Caching Implementation

**Added:**
- Thread-safe in-memory cache with TTL support
- `SimpleCache` class with pattern-based invalidation
- Cache management API endpoints

**Cached Data:**
- Profile lookups (TTL: 60 seconds)
- Profile list (TTL: 60 seconds)
- Model queries (TTL: 300 seconds)

**Endpoints:**
- `GET /api/cache/stats` - View cache statistics
- `POST /api/cache/clear` - Clear all caches
- `POST /api/cache/clear/profiles` - Clear profile cache only
- `POST /api/cache/clear/models` - Clear model cache only

**Performance Impact:**
- 70-90% cache hit rate for typical usage
- Significant reduction in database queries

**Files:**
- `backend/app/core/cache.py`
- `backend/app/api/routes/cache.py`
- `backend/tests/test_cache.py`
- `backend/tests/test_cache_integration.py`

---

### Rate Limiting Implementation

**Added:**
- SlowAPI library integration for FastAPI
- IP-based rate limiting across all endpoints
- 9 preconfigured rate limit tiers
- HTTP 429 responses with retry information
- Rate limit middleware and exception handler

**Rate Limits:**
- Stream: 20/minute
- Model Sync: 5/hour (later increased to 60/hour)
- Document Upload: 30/minute (later increased to 50/minute)
- Sessions: 60/minute
- Messages: 100/minute
- Profiles: 60/minute
- Models List: 120/minute
- Usage Logs: 120/minute
- Health Check: 300/minute

**Configuration:**
- `RATE_LIMIT_ENABLED` - Enable/disable toggle
- Per-endpoint environment variables
- In-memory storage (Redis option for production)

**Files:**
- `backend/app/core/ratelimit.py`
- Rate limiting decorators in all route files

---

### Security Fixes

#### Path Traversal Protection

**Fixed:**
- Path traversal vulnerability in document handling
- Attack vectors: `../`, absolute paths, symbolic links

**Solution:**
- Path resolution with `.resolve()`
- Boundary checking with `.relative_to()`
- Consistent error messages

**Files:**
- `backend/app/services/documents.py`
- `backend/tests/test_documents.py`

---

### Testing Coverage

#### Frontend Tests

**Added:**
- Vitest configuration with jsdom environment
- Logger service unit tests (30+ tests, 13 suites)
- ErrorBoundary integration tests (25+ tests, 10 suites)
- Test commands: `npm test`, `npm run test:watch`, `npm run test:ui`

**Coverage:**
- Session ID management
- Data sanitization
- Log level filtering
- Batch queuing
- Rate limiting handling
- Exponential backoff
- localStorage persistence
- Error boundary lifecycle

**Files:**
- `frontend/tests/logger.test.js`
- `frontend/tests/ErrorBoundary.test.jsx`
- `frontend/tests/setup.js`
- `frontend/vitest.config.js`

#### Backend Tests

**Added:**
- Migration forward/rollback tests
- Comprehensive streaming error tests
- Cache integration tests
- Search functionality tests

**Files:**
- `backend/tests/test_migrations.py`
- `backend/tests/test_stream_errors.py`
- `backend/tests/test_cache.py`
- `backend/tests/test_cache_integration.py`
- `backend/tests/test_search.py`

---

### Documentation Updates

**Updated:**
- Main README.md with all current features
- Backend README.md with comprehensive architecture
- Testing guides and quick references
- Manual testing checklists

**Added:**
- TESTING_GUIDE.md - Comprehensive test documentation
- TESTING_QUICK_REFERENCE.md - Quick command reference
- frontend/MANUAL_CHECKS.md - Expanded testing checklist
- backend/RATE_LIMITING.md - Detailed rate limiting docs

---

## Project Initialization (Pre-December 2025)

### Core Features

**Backend:**
- FastAPI 0.115+ application
- SQLite database with aiosqlite
- Server-Sent Events (SSE) streaming
- OpenRouter API integration
- Model catalog synchronization
- Profile management (reusable presets)
- Session management (chat, code, documents, playground)
- Message history
- Token usage tracking with cost calculation
- Document upload and Q&A

**Frontend:**
- React 18 single-page application
- Vite 5 development server
- Four tabs: Chat, Code, Documents, Playground
- Model selector with filters
- Profile manager
- Streaming chat interface
- Usage panel with cost tracking
- Session history

**Database Schema:**
- `models` - Cached OpenRouter model catalog
- `profiles` - Reusable configuration presets
- `sessions` - User sessions by type
- `messages` - Message history
- `usage_logs` - Token usage and costs

---

## Version Information

**Python:** 3.10+
**Node.js:** 18+
**FastAPI:** 0.115+
**React:** 18
**Vite:** 5

---

## Links

- [Main README](README.md)
- [Testing Guide](TESTING_GUIDE.md)
- [Backend Documentation](backend/README.md)
- [Rate Limiting](backend/RATE_LIMITING.md)
