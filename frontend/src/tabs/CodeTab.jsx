import { useState } from "react";

export default function CodeTab() {
  const [code, setCode] = useState("// Paste code here…\n");
  const [notes, setNotes] = useState("");

  return (
    <div className="row wrap">
      <div className="col" style={{flex: 2, minWidth: 360}}>
        <div className="card">
          <div style={{fontWeight: 700, marginBottom: 8}}>Scratchpad</div>
          <textarea className="input" style={{width:"100%", height:"55vh", fontFamily:"ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace"}} value={code} onChange={(e)=>setCode(e.target.value)} />
          <div className="muted small" style={{marginTop: 8}}>This tab is intentionally local-only; integrate with chat sessions if you want code-specific history.</div>
        </div>
      </div>
      <div className="col">
        <div className="card">
          <div style={{fontWeight: 700, marginBottom: 8}}>Notes</div>
          <textarea className="input" style={{width:"100%", height:"55vh"}} value={notes} onChange={(e)=>setNotes(e.target.value)} />
        </div>
      </div>
    </div>
  );
}
