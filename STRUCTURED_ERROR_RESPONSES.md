# Structured Error Response Implementation

## Summary

Successfully implemented **Option 2: Structured Error Responses** with machine-readable error codes across all API endpoints.

## What Changed

### New Error Infrastructure

Created `backend/app/core/errors.py` with:
- **ErrorDetail** Pydantic model for structured error responses
- **APIError** class with standardized error codes and helper methods
- Consistent error creation patterns: `not_found()`, `bad_request()`, `internal_error()`

### Standardized Error Codes

All errors now include a machine-readable `error_code`:

**404 Not Found Errors:**
- `SESSION_NOT_FOUND`
- `PROFILE_NOT_FOUND`
- `DOCUMENT_NOT_FOUND`
- `MESSAGE_NOT_FOUND`
- `USAGE_LOG_NOT_FOUND`

**400 Bad Request Errors:**
- `MISSING_API_KEY`
- `MISSING_FILENAME`

**500 Internal Server Errors:**
- `FILE_SAVE_FAILED`
- `FILE_DELETE_FAILED`
- `OPENROUTER_ERROR`
- `STREAM_ERROR`

## Error Response Format

All errors now return consistent structured JSON:

```json
{
  "error_code": "SESSION_NOT_FOUND",
  "message": "Session not found",
  "resource_type": "session",
  "resource_id": "abc-123",
  "details": null
}
```

### Example Comparisons

**Before:**
```json
{"detail": "Session not found"}
{"detail": "Profile not found"}
{"detail": "OPENROUTER_API_KEY is not set"}
```

**After:**
```json
{
  "error_code": "SESSION_NOT_FOUND",
  "message": "Session not found",
  "resource_type": "session",
  "resource_id": "abc-123"
}

{
  "error_code": "PROFILE_NOT_FOUND",
  "message": "Profile not found",
  "resource_type": "profile",
  "resource_id": "42"
}

{
  "error_code": "MISSING_API_KEY",
  "message": "OpenRouter API key is not configured",
  "details": {"config_key": "OPENROUTER_API_KEY"}
}
```

## Files Modified

1. **Created:** [backend/app/core/errors.py](backend/app/core/errors.py)
2. **Updated:** [backend/app/api/routes/sessions.py](backend/app/api/routes/sessions.py)
3. **Updated:** [backend/app/api/routes/profiles.py](backend/app/api/routes/profiles.py)
4. **Updated:** [backend/app/api/routes/messages.py](backend/app/api/routes/messages.py)
5. **Updated:** [backend/app/api/routes/documents.py](backend/app/api/routes/documents.py)
6. **Updated:** [backend/app/api/routes/usage.py](backend/app/api/routes/usage.py)
7. **Updated:** [backend/app/api/routes/models.py](backend/app/api/routes/models.py)
8. **Updated:** [backend/app/api/routes/stream.py](backend/app/api/routes/stream.py) - Enhanced SSE error events

## Benefits

### 1. **Consistent API Experience**
All endpoints now return errors in the same predictable format

### 2. **Better Debugging**
- Resource IDs included in error responses
- Machine-readable error codes for programmatic handling
- Additional context via optional `details` field

### 3. **Frontend-Friendly**
- Error codes enable type-safe error handling
- Resource IDs help with user-friendly error messages
- Structured format simplifies error parsing

### 4. **Improved Logging**
- Structured errors with context for better traceability
- Error codes make log filtering and analysis easier

### 5. **SSE Error Handling**
Stream endpoint now returns structured errors in SSE format:
```javascript
event: error
data: {
  "error_code": "SESSION_NOT_FOUND",
  "status": 404,
  "message": "Session not found",
  "resource_type": "session",
  "resource_id": "abc-123",
  "request_id": "xyz-789"
}
```

## Frontend Integration

Update frontend error handling to leverage structured responses:

```javascript
// Before
if (response.status === 404) {
  alert('Not found');
}

// After
if (response.status === 404) {
  const error = await response.json();
  switch (error.error_code) {
    case 'SESSION_NOT_FOUND':
      alert(`Session ${error.resource_id} was deleted or expired`);
      break;
    case 'PROFILE_NOT_FOUND':
      alert(`Profile ${error.resource_id} not found`);
      break;
    default:
      alert(error.message);
  }
}
```

## Backward Compatibility

The `message` field contains human-readable text similar to the old `detail` field, ensuring existing error handlers continue to work while allowing gradual migration to error code-based handling.

## Testing

Verified structured error format with test script - all error codes return proper JSON structure with:
- ✅ Correct HTTP status codes
- ✅ Error code constants
- ✅ Human-readable messages
- ✅ Resource identifiers
- ✅ Optional additional details

## Next Steps

Consider updating frontend components to:
1. Display resource IDs in user-facing error messages
2. Implement retry logic based on error codes
3. Add error code translations for i18n
4. Create error logging/tracking based on error codes
