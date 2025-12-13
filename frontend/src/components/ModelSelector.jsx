import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "../api/client.js";

export default function ModelSelector({ value, onChange }) {
  const [models, setModels] = useState([]);
  const [reasoning, setReasoning] = useState(null);
  const [maxPrice, setMaxPrice] = useState("");
  const [minContext, setMinContext] = useState("");
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (reasoning !== null) params.set("reasoning", String(reasoning));
      if (maxPrice) params.set("max_price", maxPrice);
      if (minContext) params.set("min_context", minContext);
      const data = await apiGet(`/api/models?${params.toString()}`);
      setModels(data);
    } finally {
      setLoading(false);
    }
  }

  async function sync() {
    setLoading(true);
    try {
      await apiPost("/api/models/sync", {});
      await refresh();
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, [reasoning]);

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return models;
    return models.filter(m => (m.name || "").toLowerCase().includes(needle) || (m.openrouter_id || "").toLowerCase().includes(needle));
  }, [models, q]);

  return (
    <div className="card">
      <div className="topbar">
        <div>
          <div style={{fontWeight: 700}}>Model</div>
          <div className="muted small">Filter by price, context, reasoning, then pick a model.</div>
        </div>
        <button className="btn" onClick={sync} disabled={loading}>Sync</button>
      </div>

      <div className="row wrap">
        <select className="input" value={value} onChange={(e)=>onChange(e.target.value)} style={{minWidth: 320}}>
          <option value="">Select a model…</option>
          {filtered.map(m => (
            <option key={m.id} value={m.openrouter_id}>
              {m.name} ({m.openrouter_id})
            </option>
          ))}
        </select>

        <input className="input" placeholder="Search…" value={q} onChange={(e)=>setQ(e.target.value)} />

        <select className="input" value={reasoning === null ? "" : String(reasoning)} onChange={(e)=>{
          const v = e.target.value;
          setReasoning(v === "" ? null : v === "true");
        }}>
          <option value="">Reasoning: any</option>
          <option value="true">Reasoning: yes</option>
          <option value="false">Reasoning: no</option>
        </select>

        <input className="input" placeholder="Max price (e.g. 0.000002)" value={maxPrice} onChange={(e)=>setMaxPrice(e.target.value)} onBlur={refresh} />
        <input className="input" placeholder="Min context (e.g. 8192)" value={minContext} onChange={(e)=>setMinContext(e.target.value)} onBlur={refresh} />
      </div>

      <div className="hr" />
      <div className="muted small">
        Loaded <b>{models.length}</b> models{loading ? " (loading…)" : ""}.
      </div>
    </div>
  );
}
