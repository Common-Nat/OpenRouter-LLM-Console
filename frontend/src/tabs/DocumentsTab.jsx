import { useEffect, useMemo, useRef, useState } from "react";
import { apiGet, apiDelete } from "../api/client.js";

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return "-";
  const units = ["B", "KB", "MB", "GB"];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size.toFixed(size < 10 && unitIndex > 0 ? 1 : 0)} ${units[unitIndex]}`;
}

function parseEventStream(chunk, onEvent) {
  const lines = chunk.split(/\n/);
  let eventName = "message";
  const dataLines = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line.replace("event:", "").trim();
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
  }

  if (!dataLines.length) return;
  const dataStr = dataLines.join("\n");
  let payload = dataStr;
  try { payload = JSON.parse(dataStr); } catch { /* no-op */ }
  onEvent(eventName, payload);
}

export default function DocumentsTab({ modelId, profileId, profiles = [], selectedProfile = null }) {
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [streaming, setStreaming] = useState(false);
  const controllerRef = useRef(null);

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

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    try {
      const data = await apiGet("/api/documents");
      setDocuments(data);
    } catch (e) {
      setError(e.message || "Failed to load documents.");
    }
  }

  async function deleteDocument(docId) {
    if (!docId) return;
    if (!confirm(`Delete "${docId}"? This cannot be undone.`)) return;
    
    try {
      await apiDelete(`/api/documents/${encodeURIComponent(docId)}`);
      setError("");
      if (selectedDoc === docId) {
        setSelectedDoc("");
        resetSession();
      }
      await loadDocuments();
    } catch (e) {
      setError(e.message || "Failed to delete document.");
    }
  }

  function resetSession() {
    setSessionId("");
    setAnswer("");
  }

  function onSelectDocument(id) {
    setSelectedDoc(id);
    resetSession();
  }

  function stopStream() {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
    }
    setStreaming(false);
  }

  async function ask() {
    setError("");
    setAnswer("");

    if (!selectedDoc) { setError("Select a document first."); return; }
    if (!modelId) { setError("Pick a model first."); return; }
    const q = question.trim();
    if (!q) return;

    const payload = {
      question: q,
      model_id: modelId,
      session_id: sessionId || undefined,
      profile_id: profileId ? Number(profileId) : null,
      temperature: resolvedProfile?.temperature ?? undefined,
      max_tokens: resolvedProfile?.max_tokens ?? undefined,
    };

    const controller = new AbortController();
    controllerRef.current = controller;
    setStreaming(true);

    try {
      const response = await fetch(`/api/documents/${selectedDoc}/qa`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(await response.text() || "Failed to start stream.");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      const handleEvent = (eventName, payload) => {
        if (eventName === "start" && payload?.session_id) {
          setSessionId(payload.session_id);
        }
        if (eventName === "token") {
          const token = typeof payload === "object" && payload !== null
            ? payload.token ?? payload.data ?? payload.raw
            : payload;
          if (token) setAnswer((prev) => prev + token);
        }
        if (eventName === "done") {
          if (payload?.assistant) {
            setAnswer(payload.assistant);
          }
          setStreaming(false);
        }
        if (eventName === "error") {
          const message = typeof payload === "object" && payload !== null
            ? payload.error || payload.message || JSON.stringify(payload)
            : payload;
          setError(message || "Stream error.");
          setStreaming(false);
        }
      };
 
      while (reader) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let sepIndex = buffer.indexOf("\n\n");
        while (sepIndex !== -1) {
          const chunk = buffer.slice(0, sepIndex);
          buffer = buffer.slice(sepIndex + 2);
          if (chunk.trim()) parseEventStream(chunk, handleEvent);
          sepIndex = buffer.indexOf("\n\n");
        }
      }

      if (buffer.trim()) {
        parseEventStream(buffer, handleEvent);
      }
    } catch (e) {
      if (e.name === "AbortError") return;
      setError(e.message || "Stream failed.");
      setStreaming(false);
    } finally {
      controllerRef.current = null;
    }
  }

  useEffect(() => () => stopStream(), []);

  const selectedDocMeta = documents.find(d => d.id === selectedDoc);

  return (
    <div className="row wrap">
      <div className="col">
            <div className="toolbar" style={{ marginTop: 10 }}>
              <button 
                className="btn" 
                onClick={() => deleteDocument(selectedDocMeta.id)}
                style={{ color: "#d9534f" }}
              >
                Delete
              </button>
            </div>
          )}

          {selectedDocMeta && (
        <div className="card">
          <div className="topbar">
            <div>
              <div style={{fontWeight: 700}}>Documents</div>
              <div className="muted small">Select an uploaded document to ask questions.</div>
            </div>
            <button className="btn" onClick={loadDocuments}>Refresh</button>
          </div>

          <select className="input" value={selectedDoc} onChange={(e)=>onSelectDocument(e.target.value)} style={{width:"100%"}}>
            <option value="">Select a document…</option>
            {documents.map(d => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>

          {selectedDocMeta && (
            <div className="muted small" style={{marginTop: 8, lineHeight: 1.5}}>
              <div><b>{selectedDocMeta.name}</b></div>
              <div>Size: {formatBytes(selectedDocMeta.size)}</div>
              <div>Uploaded: {new Date(selectedDocMeta.created_at).toLocaleString()}</div>
              {sessionId && <div>Session: <code>{sessionId}</code></div>}
            </div>
          )}

          <div className="hr" />
          <div className="muted small">Profile: <b>{resolvedProfile ? resolvedProfile.name : "none"}</b></div>
          <div className="muted small">Preset: <b>{presetLabel || "none"}</b></div>
          <div className="muted small">Model (with preset): <b>{resolvedModelLabel}</b></div>
        </div>
      </div>
 
      <div className="col" style={{flex: 2, minWidth: 360}}>
        <div className="card">
          <div className="topbar" style={{ marginBottom: 6 }}>
            <div>
              <div style={{fontWeight: 700}}>Document Q&A</div>
              <div className="muted small">Asks questions about the selected document using streaming responses.</div>
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

          <label className="muted small" style={{ display: "block", marginBottom: 6 }}>Question</label>
          <textarea
            className="input"
            style={{width:"100%", minHeight:"120px"}}
            placeholder="What do you want to know about this document?"
            value={question}
            onChange={(e)=>setQuestion(e.target.value)}
            onKeyDown={(e)=>{ if (e.key === "Enter" && e.metaKey) ask(); }}
          />

          <div className="hr" />

          <div className="topbar" style={{ marginBottom: 10 }}>
            <div className="muted small">Answer</div>
            <div className="muted small" style={{ textAlign: "right" }}>
              {streaming ? "Streaming…" : ""}
            </div>
          </div>

          <div className="bubble assistant" style={{ minHeight: 160 }}>
            {answer || <span className="muted small">The assistant will stream the answer here.</span>}
          </div>

          <div className="toolbar" style={{ marginTop: 10 }}>
            <button className="btn" onClick={stopStream} disabled={!streaming}>Stop</button>
            <button className="btn primary" onClick={ask} disabled={streaming}>Ask</button>
          </div>
          <div className="muted small" style={{marginTop: 8}}>
            Uses the document-aware backend endpoint at <code>/api/documents/&lt;id&gt;/qa</code> with SSE streaming.
          </div>
        </div>
      </div>
     </div>
   );
 }
