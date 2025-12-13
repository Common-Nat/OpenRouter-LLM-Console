# Manual check: profile system prompt applied to streaming

Use this checklist to confirm that switching profiles updates the streaming request so the backend uses the new system prompt and parameters.

1. Start the backend (`uvicorn main:app --reload --host 0.0.0.0 --port 8000`) and frontend (`npm run dev`) normally.
2. Create two profiles in the UI with distinct system prompts (for example, "System A" and "System B") and different temperature/max tokens values.
3. Select Profile A, open the Chat tab, and send a short message to start a stream. Note the assistant response and the profile badge in the Sessions panel.
4. Switch to Profile B without changing sessions and send another message. The response should reflect Profile B's system prompt (e.g., mention "System B") and its temperature/max token behavior.
5. Optional: open browser devtools Network tab and inspect the `/api/stream` request query string; it should include `profile_id`, `temperature`, and `max_tokens` matching Profile B.

If the response content still reflects the old profile or the request lacks the new profile parameters, the regression is present.
