# Manual Testing Checklist

Use these checklists to verify critical functionality after making changes.

## Profile System Prompt and Parameter Application

Verify that switching profiles updates the streaming request with the new system prompt and parameters.

**Steps:**
1. Start the backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Create test profiles**:
   - Click "Manage Profiles" in the UI
   - Create Profile A:
     - Name: "Profile A"
     - System Prompt: "You are a helpful assistant named System A. Always mention your name."
     - Temperature: 0.3
     - Max Tokens: 1000
   - Create Profile B:
     - Name: "Profile B"
     - System Prompt: "You are a creative writer named System B. Always mention your name."
     - Temperature: 0.9
     - Max Tokens: 2000

4. **Test profile switching**:
   - Go to Chat tab
   - Select Profile A from the profile dropdown
   - Send message: "What's your name and purpose?"
   - Verify response mentions "System A" and behaves conservatively (low temp)
   - Select Profile B from the profile dropdown
   - Send message: "What's your name and purpose?"
   - Verify response mentions "System B" and is more creative (high temp)

5. **Verify network request** (optional):
   - Open Browser DevTools → Network tab
   - Send another message with Profile B selected
   - Find the `/api/stream` request
   - Verify query string includes:
     - `profile_id` matching Profile B's ID
     - `temperature=0.9`
     - `max_tokens=2000`

**Expected Results:**
- ✅ Each profile's system prompt is applied to the assistant responses
- ✅ Temperature and max_tokens parameters are reflected in the stream request
- ✅ Switching profiles updates subsequent messages without page reload

**If test fails:**
- Check that profile ID is being passed to the stream endpoint
- Verify backend applies profile system prompt to message history
- Check backend logs for profile resolution

---

## Document Upload and Q&A

Verify document upload, security, and Q&A functionality.

**Steps:**
1. Start backend and frontend (see above)

2. **Test successful upload**:
   - Go to Documents tab
   - Click "Upload Document"
   - Select a `.txt`, `.md`, or `.py` file (under 10MB)
   - Verify file appears in the document list
   - Note the filename and size

3. **Test file type validation**:
   - Try uploading an `.exe` or `.dll` file
   - Verify error message about invalid file type
   - Verify file is NOT added to the list

4. **Test size limit**:
   - Try uploading a file larger than 10MB
   - Verify error message about file too large

5. **Test Q&A**:
   - Select an uploaded document
   - Choose a model from the dropdown
   - Ask a question about the document content
   - Verify response includes information from the document

6. **Test document deletion**:
   - Click delete button on a document
   - Verify document is removed from the list
   - Verify file is deleted from `backend/uploads/` directory

7. **Test path traversal protection**:
   - Open Browser DevTools → Console
   - Try to access: `GET /api/documents/../../../backend/app/db.py/qa`
   - Verify 404 error (document not found)
   - No file content should be returned

**Expected Results:**
- ✅ Valid files upload successfully
- ✅ Invalid file types and oversized files are rejected
- ✅ Q&A provides accurate responses based on document content
- ✅ Documents can be deleted
- ✅ Path traversal attempts are blocked

---

## Streaming Error Handling

Verify graceful error handling for various failure scenarios.

**Steps:**
1. **Test with missing API key**:
   - Stop backend
   - Remove or comment out `OPENROUTER_API_KEY` in `.env`
   - Start backend
   - Go to Chat tab and send a message
   - Verify error message displayed to user
   - Verify no uncaught exceptions in console

2. **Test with invalid session**:
   - Using browser DevTools, modify the request URL to use a non-existent session ID
   - Or delete the session from database while keeping it open in UI
   - Send a message
   - Verify error message displayed

3. **Test connection timeout**:
   - Block OpenRouter API at firewall/hosts level (optional)
   - Or disconnect internet
   - Send a message
   - Verify timeout error after configured period (default 5 minutes)
   - Verify "Abort" button works during streaming

4. **Test network interruption**:
   - Start streaming a message
   - Disconnect internet mid-stream
   - Verify error message displayed
   - Verify no infinite loading state

5. **Test rapid profile switching**:
   - Start streaming with Profile A
   - Immediately switch to Profile B and start another stream
   - Verify first stream is aborted properly
   - Verify second stream uses Profile B

**Expected Results:**
- ✅ All errors display user-friendly messages (not just "Error" or stack traces)
- ✅ No uncaught exceptions in browser console
- ✅ Streaming can be aborted cleanly
- ✅ UI returns to ready state after errors
- ✅ Request IDs logged for debugging

---

## Session and Message History

Verify session management and message persistence.

**Steps:**
1. **Create multiple sessions**:
   - Create a Chat session with title "Test Chat"
   - Create a Code session with title "Test Code"
   - Create a Documents session
   - Verify all appear in session list

2. **Test message persistence**:
   - Send 3-5 messages in "Test Chat" session
   - Refresh the browser page
   - Verify all messages are still visible
   - Verify message order is preserved

3. **Test session switching**:
   - Switch between "Test Chat" and "Test Code" sessions
   - Verify message history updates correctly
   - Verify profile settings are maintained per session

4. **Test session deletion**:
   - Delete "Test Code" session
   - Verify session removed from list
   - Verify messages are deleted (check database or try to access via API)

**Expected Results:**
- ✅ Sessions persist across page reloads
- ✅ Messages persist and display in correct order
- ✅ Switching sessions updates UI correctly
- ✅ Deleting session removes all associated messages

---

## Usage Tracking

Verify token usage and cost tracking.

**Steps:**
1. **Sync models** (if not already done):
   - Click "Sync Models" button
   - Wait for sync to complete

2. **Generate usage data**:
   - Send 2-3 messages in Chat tab
   - Use different models if possible
   - Note which models were used

3. **Check usage panel**:
   - Go to Usage Panel (if visible in UI)
   - Or check via API: `GET http://localhost:8000/api/usage`
   - Verify usage logs show:
     - Session ID
     - Model name
     - Prompt tokens
     - Completion tokens
     - Total tokens
     - Cost in USD

4. **Check usage summary**:
   - API: `GET http://localhost:8000/api/usage/summary`
   - Verify summary groups by model
   - Verify totals are accurate

**Expected Results:**
- ✅ Usage is tracked for each streaming request
- ✅ Token counts are recorded
- ✅ Costs are calculated based on model pricing
- ✅ Summary accurately aggregates usage by model

---

## General UI/UX

Quick checks for overall application health.

**Checklist:**
- ✅ All tabs (Chat, Code, Documents, Playground) are accessible
- ✅ Model selector loads models and filters work
- ✅ Profile manager opens and profiles can be created/edited/deleted
- ✅ Temperature and max tokens sliders work
- ✅ No console errors on page load
- ✅ Responsive layout works on different window sizes
- ✅ Loading states display during async operations
- ✅ Success/error messages are clear and helpful
- ✅ Backend logs show structured JSON with request IDs
