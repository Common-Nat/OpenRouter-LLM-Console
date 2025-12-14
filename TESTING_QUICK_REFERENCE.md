# 🧪 Testing Quick Reference

## Frontend Tests

### Run Tests
```bash
cd frontend
npm test              # Run once
npm run test:watch    # Watch mode (recommended)
npm run test:ui       # Visual UI
npm run test:coverage # With coverage
```

### Test Files
- `tests/logger.test.js` - Logger service (30+ tests)
- `tests/ErrorBoundary.test.jsx` - Error boundary (25+ tests)

### Coverage
- Logger: 95%+ target
- ErrorBoundary: 90%+ target

---

## Backend Tests

### Run Tests
```bash
cd backend
pytest                              # All tests
pytest -v                           # Verbose
pytest tests/test_migrations.py     # Migration tests only
pytest -k "test_logger"             # Filter by name
pytest --cov=app tests/             # With coverage
```

### Test Files
- `tests/test_migrations.py` - Forward/backward migrations (10+ tests)
- `tests/test_health.py` - Health endpoint
- `tests/test_sessions.py` - Session CRUD
- `tests/test_messages.py` - Message operations
- `tests/test_documents.py` - Document upload
- `tests/test_stream_errors.py` - Streaming errors

---

## Migration Testing

### Test Migration Forward
```bash
pytest tests/test_migrations.py::test_001_initial_schema_forward -v
```

### Test Migration Rollback
```bash
pytest tests/test_migrations.py::test_001_initial_schema_rollback -v
```

### Manual Rollback
```bash
# CAUTION: This deletes data!
sqlite3 console.db < migrations/002_add_openrouter_preset_down.sql
```

---

## First Time Setup

### Frontend
```bash
cd frontend
npm install
npm test
```

### Backend
```bash
cd backend
pip install -r requirements.txt
pytest
```

---

## Coverage Reports

### Frontend
```bash
cd frontend
npm run test:coverage
# Opens: coverage/index.html
```

### Backend
```bash
cd backend
pytest --cov=app --cov-report=html tests/
# Opens: htmlcov/index.html
```

---

## Documentation

- `TESTING_GUIDE.md` - Complete testing guide
- `TESTING_IMPLEMENTATION_SUMMARY.md` - What was implemented
- `frontend/tests/README.md` - Frontend test details
- `backend/migrations/README.md` - Migration guide

---

## Test Counts

| Category | Files | Tests | Lines |
|----------|-------|-------|-------|
| Frontend Unit | 1 | 30+ | 450+ |
| Frontend Integration | 1 | 25+ | 350+ |
| Backend Migration | 1 | 10+ | 400+ |
| **Total** | **3** | **65+** | **1200+** |

---

## Common Commands

```bash
# Run everything
cd frontend && npm test && cd ../backend && pytest

# Watch frontend tests while developing
cd frontend && npm run test:watch

# Test specific migration
cd backend && pytest tests/test_migrations.py::test_001_initial_schema_forward -v

# Generate all coverage reports
cd frontend && npm run test:coverage && cd ../backend && pytest --cov=app --cov-report=html tests/
```
