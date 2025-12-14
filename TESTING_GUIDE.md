# Testing Guide

Comprehensive testing coverage for the OpenRouter LLM Console.

## Quick Start

### Frontend Tests
```bash
cd frontend
npm install
npm test              # Run once
npm run test:watch    # Watch mode
npm run test:ui       # Visual UI
npm run test:coverage # With coverage report
```

### Backend Tests
```bash
cd backend
pytest                # Run all tests
pytest -v             # Verbose
pytest tests/test_migrations.py  # Specific test file
pytest -k "test_logger"          # Filter by name
```

---

## Frontend Testing

### Test Stack
- **Vitest**: Fast unit test runner (Vite-native)
- **React Testing Library**: Component testing
- **jsdom**: DOM environment for tests
- **@testing-library/user-event**: User interaction simulation

### Test Files

#### `tests/logger.test.js` - Logger Service Unit Tests
**Coverage:**
- ✅ Session ID generation and persistence
- ✅ Data sanitization (redacts API keys, tokens, passwords)
- ✅ Log level filtering (dev vs production)
- ✅ Batch queuing and size limits
- ✅ Backend communication (fetch API)
- ✅ Rate limiting handling (429 responses)
- ✅ Retry logic with exponential backoff
- ✅ localStorage persistence and restoration
- ✅ Synchronous flush with sendBeacon
- ✅ Context enrichment (route, timestamp, session)
- ✅ Convenience methods (debug, info, warn, error, critical)

**Key Tests:**
```javascript
// Sanitization
expect(logger.sanitize({ apiKey: 'secret' })).toEqual({ apiKey: '[REDACTED]' });

// Batch flushing
logger.critical('Error'); // Flushes immediately
for (let i = 0; i < 50; i++) logger.info('msg'); // Flushes at batch size

// Retry with backoff
// 1st retry: 1s, 2nd: 2s, 3rd: 4s, 4th: 8s, 5th: 16s
```

#### `tests/ErrorBoundary.test.jsx` - Error Boundary Integration Tests
**Coverage:**
- ✅ Normal rendering (no errors)
- ✅ Error catching from child components
- ✅ Logger integration (calls logger.componentError)
- ✅ Custom context passing to logger
- ✅ Fallback UI display
- ✅ Recovery actions (Try Again, Reload)
- ✅ GitHub issue link generation
- ✅ Development mode error details
- ✅ Multiple error handling
- ✅ Nested error boundaries

**Key Tests:**
```javascript
// Error catching
<ErrorBoundary>
  <ThrowError shouldThrow={true} />
</ErrorBoundary>
// → Shows "Something went wrong"
// → Calls logger.componentError(error, errorInfo)

// Recovery
user.click(tryAgainButton);
// → Resets error state, re-renders children
```

### Running Specific Tests
```bash
# Single file
npm test logger.test.js

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
# → Opens html report in coverage/index.html
```

---

## Backend Testing

### Test Stack
- **pytest**: Python test framework
- **httpx**: Async HTTP client for FastAPI testing
- **aiosqlite**: Async SQLite for DB tests
- **pytest.ini**: Configures asyncio mode

### Test Files

#### `tests/test_migrations.py` - Migration Test Harness
**Coverage:**
- ✅ Forward migrations create correct schema
- ✅ Rollback migrations clean up properly
- ✅ Data preservation during rollbacks (where applicable)
- ✅ Full migration cycle (forward → rollback → empty DB)
- ✅ Idempotent migrations
- ✅ Foreign key constraints

**Key Tests:**
```python
# Forward migration
async def test_001_initial_schema_forward():
    # Applies 001_initial_schema.sql
    # Verifies all tables exist
    # Checks column structure

# Rollback migration
async def test_001_initial_schema_rollback():
    # Applies 001 forward, then 001 down
    # Verifies all tables removed

# Data preservation
async def test_002_rollback_preserves_data():
    # Insert profile with openrouter_preset
    # Rollback 002 (removes column)
    # Verify other profile data still exists

# Foreign keys
async def test_foreign_key_constraints():
    # Delete profile → session.profile_id = NULL (SET NULL)
    # Delete session → messages deleted (CASCADE)
```

#### Existing Backend Tests
- `test_health.py` - Health endpoint
- `test_sessions.py` - Session CRUD
- `test_messages.py` - Message operations
- `test_documents.py` - Document upload/retrieval
- `test_stream_errors.py` - Streaming error handling
- `test_db_init.py` - Database initialization

### Running Specific Tests
```bash
# All tests
pytest

# Verbose with output
pytest -v -s

# Specific file
pytest tests/test_migrations.py

# Specific test
pytest tests/test_migrations.py::test_001_initial_schema_forward

# Failed tests only
pytest --lf
```

---

## Migration Testing Workflow

### Testing a New Migration

1. **Create migration files:**
   ```bash
   migrations/003_add_tags_table.sql      # Forward
   migrations/003_add_tags_table_down.sql # Rollback
   ```

2. **Write tests:**
   ```python
   # tests/test_migrations.py
   
   @pytest.mark.asyncio
   async def test_003_add_tags_forward():
       async with aiosqlite.connect(":memory:") as db:
           # Apply 001, 002, 003
           await apply_migration(db, "001_initial_schema.sql")
           await apply_migration(db, "002_add_openrouter_preset.sql")
           await apply_migration(db, "003_add_tags_table.sql")
           
           # Verify tags table exists
           tables = await get_table_list(db)
           assert 'tags' in tables
           
           # Verify columns
           cols = await get_table_columns(db, 'tags')
           assert 'id' in [c[0] for c in cols]
           assert 'name' in [c[0] for c in cols]
   
   @pytest.mark.asyncio
   async def test_003_add_tags_rollback():
       async with aiosqlite.connect(":memory:") as db:
           # Apply forward
           await apply_migration(db, "001_initial_schema.sql")
           await apply_migration(db, "002_add_openrouter_preset.sql")
           await apply_migration(db, "003_add_tags_table.sql")
           
           # Apply rollback
           await apply_migration(db, "003_add_tags_table_down.sql")
           
           # Verify tags table removed
           tables = await get_table_list(db)
           assert 'tags' not in tables
   ```

3. **Run tests:**
   ```bash
   pytest tests/test_migrations.py::test_003_add_tags_forward -v
   pytest tests/test_migrations.py::test_003_add_tags_rollback -v
   ```

4. **Test with real DB:**
   ```bash
   # Backup first!
   cp console.db console.db.backup
   
   # Apply migration
   sqlite3 console.db < migrations/003_add_tags_table.sql
   
   # Verify
   sqlite3 console.db "SELECT name FROM sqlite_master WHERE type='table';"
   
   # Rollback if needed
   sqlite3 console.db < migrations/003_add_tags_table_down.sql
   ```

---

## Test Coverage Summary

### ✅ Fully Covered
- Frontend logger service (100% coverage)
- ErrorBoundary component
- Migration forward/backward cycles
- Backend API routes (health, sessions, messages, documents)

### ⚠️ Partial Coverage
- React components (only ErrorBoundary)
- Frontend utils (errorHandling.js, client.js)
- Backend streaming logic (basic tests exist)

### 🚧 Missing Coverage
- E2E tests (browser → backend → OpenRouter)
- Frontend tab components (ChatTab, CodeTab, etc.)
- Rate limiting integration tests
- CORS configuration tests

---

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: cd frontend && npm ci
      - run: cd frontend && npm test
  
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: 3.9
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && pytest -v
```

---

## Best Practices

### Frontend Testing
1. **Mock external dependencies** (fetch, localStorage, logger)
2. **Test user interactions** with `userEvent` not `fireEvent`
3. **Query by accessibility** (`getByRole`, `getByLabelText`)
4. **Suppress expected errors** in error boundary tests
5. **Use fake timers** for batching/retry tests

### Backend Testing
1. **Use in-memory DB** (`:memory:`) for unit tests
2. **Test with real DB** for integration tests
3. **Always test rollbacks** for schema migrations
4. **Verify foreign keys** work correctly
5. **Test idempotency** (run migrations twice)

### Migration Testing
1. **Test forward AND backward** for every migration
2. **Verify data preservation** when applicable
3. **Test full cycle** (empty → forward → rollback → empty)
4. **Check constraints** (foreign keys, indexes)
5. **Handle SQLite limitations** (DROP COLUMN requires table recreation)

---

## Troubleshooting

### Frontend Tests Failing
```bash
# Clear cache
rm -rf node_modules .vite coverage
npm install

# Run with verbose output
npm test -- --reporter=verbose

# Check for mock issues
# Ensure setup.js is configuring mocks correctly
```

### Backend Tests Failing
```bash
# Check Python version (requires 3.9+)
python --version

# Reinstall dependencies
pip install -r requirements.txt

# Run single test with output
pytest tests/test_migrations.py::test_001_initial_schema_forward -v -s

# Check aiosqlite
python -c "import aiosqlite; print(aiosqlite.__version__)"
```

### Migration Tests Failing
```bash
# Verify migration files exist
ls migrations/*_down.sql

# Test SQL syntax
sqlite3 :memory: < migrations/001_initial_schema.sql

# Check for duplicate column errors
# If 002 fails with "duplicate column", ensure idempotency
```

---

## Next Steps

**Recommended additions:**
1. **E2E tests** with Playwright/Cypress
2. **Frontend component tests** for tabs
3. **Rate limiting integration tests**
4. **Performance tests** for large message history
5. **Security tests** for API authentication
