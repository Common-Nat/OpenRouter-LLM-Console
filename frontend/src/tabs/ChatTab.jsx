import { useEffect, useMemo, useRef, useState } from "react";
import { apiGet, apiPost } from "../api/client.js";
import useStream from "../hooks/useStream.js";
import UsagePanel from "../components/UsagePanel.jsx";

function useAutoScroll(dep) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [dep]);
  return ref;
}

export default function ChatTab({ modelId, profileId, profiles = [], selectedProfile = null }) {
  const [sessionId, setSessionId] = useState("");
  const [sessions, setSessions] = useState([]);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");

  const resolvedProfile = useMemo(
    () => selectedProfile || profiles.find(p => String(p.id) === String(profileId)),
    [profiles, profileId, selectedProfile],
  );
  const presetLabel = useMemo(() => {
    if (!resolvedProfile?.openrouter_preset) return "";
    return resolvedProfile.openrouter_preset.startsWith("@preset/")
      ? resolvedProfile.openrouter_preset
      : `@preset/${resolvedProfile.openrouter_preset}`;
  }, [resolvedProfile]);
  const resolvedModelLabel = useMemo(() => {
    if (!modelId) return "none";
    return presetLabel ? `${modelId}${presetLabel}` : modelId;
  }, [modelId, presetLabel]);

  const logRef = useAutoScroll(messages.length);
  const { start: startStream, abort: abortStream, streaming } = useStream();

  async function loadSessions() {
    const data = await apiGet("/api/sessions?limit=50");
    setSessions(data.filter(s => s.session_type === "chat"));
  }

  function sessionLabel(session) {
    const p = profiles.find(x => String(x.id) === String(session.profile_id));
    const name = session.title || session.id;
    return p ? `${name} • ${p.name}` : name;
  }

  async function createSession() {
    const profilePayload = profileId ? Number(profileId) : null;
    const s = await apiPost("/api/sessions", { session_type: "chat", title: "New chat", profile_id: profilePayload });
    setSessionId(s.id);
    await loadSessions();
    setMessages([]);
    return s.id;
  }

  async function loadMessages(id) {
    const data = await apiGet(`/api/sessions/${id}/messages`);
    setMessages(data);
  }

  useEffect(() => { loadSessions(); }, []);
  useEffect(() => { if (sessionId) loadMessages(sessionId); }, [sessionId]);

  async function send() {
    setError("");
    if (!modelId) { setError("Pick a model first."); return; }
    const text = draft.trim();
    if (!text) return;

    let sid = sessionId;
    if (!sid) {
      sid = await createSession();
    }
    setSessionId(sid);

    const userMsg = await apiPost("/api/messages", { session_id: sid, role: "user", content: text });
    setMessages(m => [...m, userMsg]);
    setDraft("");

    // optimistic assistant bubble
    const tmpId = `tmp-${Date.now()}`;
    setMessages(m => [...m, { id: tmpId, session_id: sid, role: "assistant", content: "", created_at: new Date().toISOString() }]);

    const qs = new URLSearchParams({
      session_id: sid,
      model_id: modelId,
    });

    if (profileId !== undefined && profileId !== null) qs.set("profile_id", profileId);
    if (resolvedProfile?.temperature !== undefined && resolvedProfile?.temperature !== null) qs.set("temperature", String(resolvedProfile.temperature));
    if (resolvedProfile?.max_tokens !== undefined && resolvedProfile?.max_tokens !== null) qs.set("max_tokens", String(resolvedProfile.max_tokens));

    startStream(`/api/stream?${qs.toString()}`, {
      onToken: (token) => {
        setMessages(m => m.map(x => x.id === tmpId ? { ...x, content: x.content + token } : x));
      },
      onDone: () => {
        // refresh from DB to replace tmp with saved assistant message
        loadMessages(sid).catch(()=>{});
      },
      onError: (payload) => {
        const message = typeof payload === "object" && payload !== null
          ? payload.error || payload.message || JSON.stringify(payload)
          : payload || "Stream error. Check backend logs and OPENROUTER_API_KEY.";
        setError(message);
        loadMessages(sid).catch(()=>{});
      },
    });
  }

  useEffect(() => {
    return () => {
      abortStream();
    };
  }, [abortStream]);

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
              <option key={s.id} value={s.id}>{sessionLabel(s)}</option>
            ))}
          </select>

          <div className="hr" />
          <div className="muted small">Profile: <b>{resolvedProfile ? resolvedProfile.name : "none"}</b></div>
            <div className="muted small">Preset: <b>{presetLabel || "none"}</b></div>
            <div className="muted small">Model (with preset): <b>{resolvedModelLabel}</b></div>
        </div>

        <UsagePanel sessionId={sessionId} streaming={streaming} />
      </div>

      <div className="col" style={{flex: 2, minWidth: 360}}>
        <div className="card">
          <div className="topbar" style={{ marginBottom: 6 }}>
            <div>
              <div style={{fontWeight: 700}}>Chat</div>
              <div className="muted small">Using {resolvedModelLabel} {presetLabel ? "from profile" : "with no preset"}</div>
            </div>
            <div className="muted small" style={{ textAlign: "right" }}>
              <div>Profile: <b>{resolvedProfile?.name || "none"}</b></div>
              <div>Preset: <b>{presetLabel || "none"}</b></div>
            </div>
          </div>
          {error && (
            <div className="banner error" style={{ marginBottom: 10 }}>
              {error}
            </div>
          )}
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
            {streaming ? (
              <button className="btn" onClick={() => { setError(""); abortStream(); if (sessionId) loadMessages(sessionId).catch(()=>{}); }}>
                Stop generation
              </button>
            ) : (
              <button className="btn primary" onClick={send} disabled={streaming}>Send</button>
            )}
          </div>
          <div className="muted small" style={{marginTop: 8}}>
            Tip: press Enter to send. Streaming saves the final assistant message into SQLite automatically.
          </div>
        </div>
      </div>
    </div>
  );
}
