import { useState } from "react";

export default function DocumentsTab() {
  const [doc, setDoc] = useState("# Document\n\nWrite here…\n");
  return (
    <div className="card">
      <div style={{fontWeight:700, marginBottom: 8}}>Documents</div>
      <textarea className="input" style={{width:"100%", height:"70vh"}} value={doc} onChange={(e)=>setDoc(e.target.value)} />
      <div className="muted small" style={{marginTop: 8}}>Add persistence + versioning by storing docs in SQLite (same pattern as messages).</div>
    </div>
  );
}
