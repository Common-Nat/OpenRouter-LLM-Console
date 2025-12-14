import { useCallback, useEffect, useMemo, useState } from "react";
import { apiGet } from "../api/client.js";

export default function UsagePanel({ sessionId, streaming }) {
  const [sessionUsage, setSessionUsage] = useState([]);
  const [modelUsage, setModelUsage] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const totals = useMemo(() => {
    return sessionUsage.reduce(
      (acc, u) => ({
        prompt: acc.prompt + Number(u.prompt_tokens || 0),
        completion: acc.completion + Number(u.completion_tokens || 0),
        total: acc.total + Number(u.total_tokens || 0),
        cost: acc.cost + Number(u.cost_usd || 0),
      }),
      { prompt: 0, completion: 0, total: 0, cost: 0 },
    );
  }, [sessionUsage]);

  const perModel = useMemo(() => {
    const map = new Map();
    sessionUsage.forEach((u) => {
      const key = u.model_id || u.openrouter_id || "unknown";
      const existing = map.get(key) || {
        model_id: u.model_id,
        openrouter_id: u.openrouter_id,
        model_name: u.model_name,
        prompt: 0,
        completion: 0,
        total: 0,
        cost: 0,
      };
      map.set(key, {
        ...existing,
        prompt: existing.prompt + Number(u.prompt_tokens || 0),
        completion: existing.completion + Number(u.completion_tokens || 0),
        total: existing.total + Number(u.total_tokens || 0),
        cost: existing.cost + Number(u.cost_usd || 0),
      });
    });
    return Array.from(map.values()).sort((a, b) => b.cost - a.cost || b.total - a.total);
  }, [sessionUsage]);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [sessionData, modelData] = await Promise.all([
        sessionId ? apiGet(`/api/usage/sessions/${sessionId}`) : Promise.resolve([]),
        apiGet("/api/usage/models"),
      ]);
      setSessionUsage(sessionData || []);
      setModelUsage(modelData || []);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    refresh();
  }, [streaming, refresh]);

  return (
    <div className="card" style={{ marginTop: 12 }}>
      <div className="topbar">
        <div>
          <div style={{ fontWeight: 700 }}>Usage</div>
          <div className="muted small">Session totals and model breakdown from usage logs.</div>
        </div>
        <button className="btn" onClick={refresh} disabled={loading}>
          Refresh
        </button>
      </div>

      {error && <div style={{ color: "#ffb4b4", marginBottom: 8 }}>{error}</div>}

      <div className="muted small" style={{ marginBottom: 6 }}>
        Session: {sessionId ? sessionId : "none selected"}
        {streaming && " (streaming…)"}
      </div>

      {sessionId ? (
        <>
          <div className="row wrap" style={{ gap: 12 }}>
            <Stat label="Prompt tokens" value={totals.prompt} />
            <Stat label="Completion tokens" value={totals.completion} />
            <Stat label="Total tokens" value={totals.total} />
            <Stat label="Cost (USD)" value={totals.cost.toFixed(6)} />
          </div>

          <div className="hr" />
          <div className="muted small" style={{ marginBottom: 6 }}>Session usage by model</div>
          {perModel.length ? (
            <div className="muted small" style={{ display: "grid", gridTemplateColumns: "1.5fr repeat(4, 1fr)", gap: 6 }}>
              <div style={{ fontWeight: 600 }}>Model</div>
              <div style={{ fontWeight: 600 }}>Prompt</div>
              <div style={{ fontWeight: 600 }}>Completion</div>
              <div style={{ fontWeight: 600 }}>Total</div>
              <div style={{ fontWeight: 600 }}>Cost</div>
              {perModel.map((m, idx) => (
                <Row key={`${m.model_id || m.openrouter_id || idx}`} values={[
                  m.model_name || m.openrouter_id || "Unknown model",
                  m.prompt,
                  m.completion,
                  m.total,
                  m.cost.toFixed(6),
                ]} />
              ))}
            </div>
          ) : (
            <div className="muted small">No usage logs for this session yet.</div>
          )}
        </>
      ) : (
        <div className="muted small">Select or start a session to view usage.</div>
      )}

      <div className="hr" />
      <div className="muted small" style={{ marginBottom: 6 }}>Overall usage by model</div>
      {modelUsage.length ? (
        <div className="muted small" style={{ display: "grid", gridTemplateColumns: "1.5fr repeat(4, 1fr)", gap: 6 }}>
          <div style={{ fontWeight: 600 }}>Model</div>
          <div style={{ fontWeight: 600 }}>Prompt</div>
          <div style={{ fontWeight: 600 }}>Completion</div>
          <div style={{ fontWeight: 600 }}>Total</div>
          <div style={{ fontWeight: 600 }}>Cost</div>
          {modelUsage.map((m, idx) => (
            <Row key={`${m.model_id || m.openrouter_id || idx}`} values={[
              m.model_name || m.openrouter_id || "Unknown model",
              m.prompt_tokens,
              m.completion_tokens,
              m.total_tokens,
              Number(m.cost_usd || 0).toFixed(6),
            ]} />
          ))}
        </div>
      ) : (
        <div className="muted small">No usage logs stored.</div>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="card" style={{ flex: 1, minWidth: 160 }}>
      <div className="muted small">{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

function Row({ values }) {
  return values.map((v, i) => (
    <div key={i} style={{ padding: "4px 0" }}>
      {v}
    </div>
  ));
}
