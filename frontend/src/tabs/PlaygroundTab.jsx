import { useState } from "react";

export default function PlaygroundTab() {
  const [json, setJson] = useState(JSON.stringify({ temperature: 0.7, max_tokens: 2048 }, null, 2));
  return (
    <div className="card">
      <div style={{fontWeight:700, marginBottom: 8}}>Playground</div>
      <div className="muted small" style={{marginBottom: 10}}>This is a placeholder for parameter presets, prompt templates, and quick experiments.</div>
      <textarea className="input" style={{width:"100%", height:"65vh", fontFamily:"ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace"}} value={json} onChange={(e)=>setJson(e.target.value)} />
    </div>
  );
}
