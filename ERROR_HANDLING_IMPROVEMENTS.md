# Error Handling Improvements - useStream Hook

## Summary of Changes

Comprehensive error handling improvements were implemented across the streaming infrastructure to handle network failures, timeouts, connection issues, and backend errors properly.

## Frontend Changes ([useStream.js](frontend/src/hooks/useStream.js))

### New Error Scenarios Handled

1. **EventSource Creation Failures**
   - Catches errors during EventSource instantiation (invalid URLs, browser restrictions)
   - Returns proper error callback with descriptive message

2. **Connection Timeouts**
   - Added configurable timeout (default: 300 seconds / 5 minutes)
   - Triggers timeout error if no data received within timeout period
   - Automatically aborts connection and cleans up resources

3. **Native EventSource Errors**
   - Implemented `es.onerror` handler for network-level failures
   - Distinguishes between connection failures and unexpected disconnections
   - Provides different error messages based on connection state (CONNECTING, OPEN, CLOSED)

4. **Race Condition Prevention**
   - Tracks timeout references to prevent orphaned timers
   - Ensures proper cleanup when multiple streams start/stop rapidly
   - Uses closure to verify EventSource instance before cleanup

### New Features

- **Timeout Configuration**: Pass `timeout` option in milliseconds (0 to disable)
  ```javascript
  start('/api/stream?...', {
    timeout: 60000, // 1 minute
    onError: (error) => { ... }
  });
  ```

- **Enhanced Error Payloads**: All errors include descriptive fields:
  ```javascript
  {
    message: "Human-readable error description",
    error: "error_type", // e.g., "timeout", "connection_error", "connection_failed"
    readyState: 2 // EventSource state when error occurred
  }
  ```

## Backend Changes

### [stream.py](backend/app/api/routes/stream.py)

**Problem**: HTTPExceptions caused EventSource connection failures with generic browser errors instead of descriptive SSE error events.

**Solution**: Validation errors now return StreamingResponse with SSE error events:

```python
# Before: raise HTTPException(status_code=400, detail="...")
# After:
return StreamingResponse(
    _error_stream(400, "OPENROUTER_API_KEY is not configured"),
    media_type="text/event-stream",
)
```

This ensures the frontend receives proper `event: error` SSE messages that can be parsed and displayed to users.

### [openrouter.py](backend/app/services/openrouter.py)

**Enhanced Error Logging**: All error paths now include structured logging with:
- `error_type` field for categorization
- `session_id` and `model` for traceability
- Proper exception logging with stack traces for internal errors

**Standardized Error Events**: All error SSE events include:
```json
{
  "status": 500,
  "message": "Detailed error description",
  "error": "error_type",
  "request_id": "unique-request-id"
}
```

## Testing

New test suite: [test_stream_errors.py](backend/tests/test_stream_errors.py)

Tests cover:
- Missing API key error
- Session not found error
- Profile not found error
- OpenRouter API errors (rate limits, etc.)
- Unexpected exceptions during streaming

Run tests:
```bash
cd backend
pytest tests/test_stream_errors.py -v
```

## Usage Examples

### Frontend Component

```javascript
import useStream from "../hooks/useStream.js";

function MyComponent() {
  const { start, abort, streaming } = useStream();
  const [error, setError] = useState(null);

  const handleStream = () => {
    setError(null);
    start('/api/stream?session_id=abc&model_id=xyz', {
      timeout: 120000, // 2 minutes
      onToken: (token) => {
        // Append token to UI
      },
      onDone: (payload) => {
        // Stream completed successfully
      },
      onError: (errorPayload) => {
        // Handle all error types
        const message = errorPayload.message || 
                       errorPayload.error || 
                       "Unknown error";
        setError(message);
        
        // Log for debugging
        console.error('Stream error:', errorPayload);
      }
    });
  };

  return (
    <div>
      {error && <div className="error">{error}</div>}
      <button onClick={handleStream} disabled={streaming}>
        Start Stream
      </button>
    </div>
  );
}
```

## Error Types Reference

| Error Type | Source | Description |
|------------|--------|-------------|
| `timeout` | Frontend | No data received within timeout period |
| `connection_error` | Frontend | Connection closed unexpectedly |
| `connection_failed` | Frontend | Unable to establish connection |
| `openrouter_error` | Backend | OpenRouter API returned error (rate limit, invalid model, etc.) |
| `internal_error` | Backend | Unexpected server-side exception |

## Migration Notes

Existing code using `useStream` will continue to work without changes. To benefit from new features:

1. **Add timeout handling**: Pass `timeout` option to `start()`
2. **Enhance error display**: Check for `error.error` field to show specific error types
3. **Update error messages**: Use `error.message` for user-friendly descriptions

## Monitoring & Debugging

### Backend Logs

All streaming errors are logged with structured JSON including:
- `request_id`: Unique identifier for request tracing
- `action`: Type of operation (`stream_error`, `stream_cancelled`, etc.)
- `error_type`: Categorized error type
- `session_id`, `model`: Context for debugging

### Frontend Console

In development, log error payloads to understand failure patterns:
```javascript
onError: (error) => {
  console.error('Stream error details:', {
    message: error.message,
    type: error.error,
    readyState: error.readyState,
    timestamp: new Date().toISOString()
  });
}
```
