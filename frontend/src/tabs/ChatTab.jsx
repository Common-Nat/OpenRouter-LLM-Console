import { useEffect, useMemo, useRef, useState } from "react";
import { apiGet, apiPost } from "../api/client.js";

function useAutoScroll(dep) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [dep]);
  return ref;
}

export default function ChatTab({ modelId }) {
  const [sessionId, setSessionId] = useState("");
  const [sessions, setSessions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState("");

  const logRef = useAutoScroll(messages.length);

  async function loadSessions() {
    const data = await apiGet("/api/sessions?limit=50");
    setSessions(data.filter(s => s.session_type === "chat"));
  }

  async function createSession() {
    const s = await apiPost("/api/sessions", { session_type: "chat", title: "New chat" });
    setSessionId(s.id);
    await loadSessions();
    setMessages([]);
  }

  async function loadMessages(id) {
    const data = await apiGet(`/api/sessions/${id}/messages`);
    setMessages(data);
  }

  useEffect(() => { loadSessions(); }, []);
  useEffect(() => { if (sessionId) loadMessages(sessionId); }, [sessionId]);

  async function send() {
    setError("");
    if (!sessionId) await createSession();
    if (!modelId) { setError("Pick a model first."); return; }
    const text = draft.trim();
    if (!text) return;

    const sid = sessionId || (await apiPost("/api/sessions", { session_type: "chat", title: "New chat" })).id;
    setSessionId(sid);

    const userMsg = await apiPost("/api/messages", { session_id: sid, role: "user", content: text });
    setMessages(m => [...m, userMsg]);
    setDraft("");

    // optimistic assistant bubble
    const tmpId = `tmp-${Date.now()}`;
    setMessages(m => [...m, { id: tmpId, session_id: sid, role: "assistant", content: "", created_at: new Date().toISOString() }]);

    const es = new EventSource(`/api/stream?session_id=${encodeURIComponent(sid)}&model_id=${encodeURIComponent(modelId)}`);
    setStreaming(true);

    es.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === "token") {
          setMessages(m => m.map(x => x.id === tmpId ? { ...x, content: x.content + msg.token } : x));
        }
      } catch { /* ignore */ }
    };

    es.addEventListener("error", (e) => {
      setError("Stream error. Check backend logs and OPENROUTER_API_KEY.");
    });

    es.onerror = () => {
      es.close();
      setStreaming(false);
      // refresh from DB to replace tmp with saved assistant message
      loadMessages(sid).catch(()=>{});
    };

    es.addEventListener("message", (e)=>{ /* already handled */ });
  }

  return (
    <div className="row wrap">
      <div className="col">
        <div className="card">
          <div className="topbar">
            <div>
              <div style={{fontWeight: 700}}>Sessions</div>
              <div className="muted small">Chat sessions stored in SQLite.</div>
            </div>
            <button className="btn" onClick={createSession}>New</button>
          </div>

          <select className="input" value={sessionId} onChange={(e)=>setSessionId(e.target.value)} style={{width:"100%"}}>
            <option value="">Select a session…</option>
            {sessions.map(s => (
              <option key={s.id} value={s.id}>{s.title || s.id}</option>
            ))}
          </select>

          <div className="hr" />
          <div className="muted small">Model: <b>{modelId || "none"}</b></div>
          {error && <div style={{marginTop: 10, color:"#ffb4b4"}}>{error}</div>}
        </div>
      </div>

      <div className="col" style={{flex: 2, minWidth: 360}}>
        <div className="card">
          <div className="chatlog" ref={logRef}>
            {messages.map(m => (
              <div key={m.id} className={`bubble ${m.role === "user" ? "user" : "assistant"}`}>
                <div className="muted small" style={{marginBottom: 6}}>{m.role}</div>
                {m.content}
              </div>
            ))}
          </div>

          <div className="hr" />
          <div className="toolbar">
            <input className="input" style={{flex:1, minWidth: 220}} placeholder="Type a message…" value={draft} onChange={(e)=>setDraft(e.target.value)} onKeyDown={(e)=>{ if (e.key==="Enter" && !e.shiftKey){ e.preventDefault(); if(!streaming) send(); } }} />
            <button className="btn primary" onClick={send} disabled={streaming}>Send</button>
          </div>
          <div className="muted small" style={{marginTop: 8}}>
            Tip: press Enter to send. Streaming saves the final assistant message into SQLite automatically.
          </div>
        </div>
      </div>
    </div>
  );
}
