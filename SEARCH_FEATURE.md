# Search Feature Implementation

## Overview
Full-text search across all messages using SQLite FTS5 with advanced filtering and ranking capabilities.

## Backend Implementation

### Database (Migration 003)
- **FTS5 virtual table**: `messages_fts` with automatic sync via triggers
- **Indexed field**: `content` (full-text searchable)
- **Metadata fields**: `role`, `session_id`, `created_at` (filterable, not indexed)
- **Auto-sync**: INSERT/UPDATE/DELETE triggers keep FTS table in sync

### API Endpoint
```
GET /api/messages/search
```

**Query Parameters:**
- `query` (required): Search text with FTS5 syntax support
- `session_id` (optional): Filter by specific session
- `session_type` (optional): Filter by type (chat/code/documents/playground)
- `model_id` (optional): Filter by model used
- `start_date` (optional): ISO date string (YYYY-MM-DD)
- `end_date` (optional): ISO date string (YYYY-MM-DD)
- `limit` (optional): Max results (default: 50, max: 200)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
[
  {
    "id": "msg-uuid",
    "session_id": "session-uuid",
    "role": "assistant",
    "content": "Full message content...",
    "created_at": "2025-12-14T10:30:00",
    "session_type": "chat",
    "session_title": "Debug Session",
    "snippet": "...context <mark>highlighted</mark> match...",
    "rank": -2.5
  }
]
```

## Frontend Implementation

### Components
1. **SearchBar.jsx**: Main search UI with filters
2. **useSearch.js**: Custom hook with debouncing (300ms)

### Usage Example
```jsx
import SearchBar from './components/SearchBar';

<SearchBar onResultClick={(result) => {
  // Handle result selection
  console.log(result.session_id, result.id);
}} />
```

## Search Syntax (FTS5)

### Basic Search
- `error` - Find messages containing "error"
- `api error` - Find messages with both "api" AND "error"

### Phrase Search
- `"connection timeout"` - Exact phrase match
- `"api error"` - Both words in exact order

### Exclude Terms
- `error -python` - Messages with "error" but NOT "python"
- `bug -fixed` - Bugs that aren't fixed

### Prefix Matching
- `test*` - Matches: test, testing, tested, tester
- `api*` - Matches: api, apis, apiKey, etc.

### Boolean Operators
- `python OR javascript` - Either term
- `"node.js" OR "nodejs"` - Phrase alternatives

### Complex Queries
- `(python OR javascript) error -timeout` - Python/JS errors, no timeout
- `"database" connection*` - Database with any connection variant

## Performance Considerations

### Optimizations
- BM25 ranking algorithm for relevance scoring
- Indexed on `(session_id, created_at)` for filtered queries
- Results limited to 200 max per request
- Debounced input (300ms) reduces server load

### Benchmarks (approximate)
- 1,000 messages: <10ms
- 10,000 messages: ~50ms
- 100,000 messages: ~200ms

## Testing

Run backend tests:
```bash
cd backend
pytest tests/test_search.py -v
```

Test cases cover:
- Basic keyword search
- Phrase matching
- Filters (type, date)
- Exclusion operators
- Prefix matching
- Result ranking
- Pagination
- Snippet highlighting

## Troubleshooting

### Common Issues

**1. "FTS5 syntax error"**
- Check for unescaped special characters: `"` `*` `-`
- Wrap complex queries in quotes
- Backend catches and returns validation error

**2. No results found**
- Check date filters (ISO format required: YYYY-MM-DD)
- Verify session_type spelling (chat/code/documents/playground)
- Try simpler query first

**3. Slow searches**
- Reduce limit if fetching too many results
- Add more specific filters
- Use prefix matching sparingly (can be slow)

**4. Missing highlights**
- Verify `<mark>` tags in snippet field
- Check CSS for `.search-result-snippet mark` styles

## Future Enhancements

### Potential additions:
- [ ] Save search queries as filters
- [ ] Recent searches dropdown
- [ ] Export search results to JSON/CSV
- [ ] Search suggestions/autocomplete
- [ ] Fuzzy matching for typos
- [ ] Search within specific date ranges (UI picker)
- [ ] Keyboard shortcuts (Ctrl+K, Cmd+K)
- [ ] Search result grouping by session

## Files Modified

### Backend
- `backend/migrations/003_add_fts_search.sql` - FTS5 table + triggers
- `backend/migrations/003_add_fts_search_down.sql` - Rollback script
- `backend/app/repo.py` - `search_messages()` function
- `backend/app/schemas.py` - Search request/response models
- `backend/app/api/routes/messages.py` - `/search` endpoint
- `backend/tests/test_search.py` - Test suite

### Frontend
- `frontend/src/components/SearchBar.jsx` - Search UI component
- `frontend/src/hooks/useSearch.js` - Search hook with debouncing
- `frontend/src/styles/SearchBar.css` - Component styles
- `frontend/src/api/client.js` - `searchMessages()` API call
- `frontend/src/App.jsx` - SearchBar integration

## Migration Instructions

1. **Stop backend** (if running)
2. **Backup database**: `cp console.db console.db.backup`
3. **Start backend**: Migration runs automatically on startup
4. **Verify migration**: Check logs for "Applied migration 003"
5. **Test search**: Use frontend or curl:

```bash
curl "http://localhost:8000/api/messages/search?query=test"
```

## Rollback

If issues occur:
```bash
cd backend
sqlite3 console.db < migrations/003_add_fts_search_down.sql
```

This removes FTS table and triggers, reverting to pre-search state.
