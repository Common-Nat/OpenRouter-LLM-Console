import { useMemo, useState } from "react";

export default function CodeTab({ modelId, profile }) {
  const [code, setCode] = useState("// Paste code here…\n");
  const [notes, setNotes] = useState("");

  const presetLabel = useMemo(() => {
    if (!profile?.openrouter_preset) return "";
    return profile.openrouter_preset.startsWith("@preset/")
      ? profile.openrouter_preset
      : `@preset/${profile.openrouter_preset}`;
  }, [profile]);
  const resolvedModelLabel = useMemo(() => {
    if (!modelId) return "none";
    return presetLabel ? `${modelId}${presetLabel}` : modelId;
  }, [modelId, presetLabel]);

  return (
    <>
      <div className="card" style={{ marginBottom: 12 }}>
        <div className="topbar">
          <div>
            <div style={{fontWeight: 700}}>Code</div>
            <div className="muted small">Profile context for code experiments.</div>
          </div>
          <div className="muted small" style={{ textAlign: "right" }}>
            <div>Profile: <b>{profile?.name || "none"}</b></div>
            <div>Preset: <b>{presetLabel || "none"}</b></div>
            <div>Model (with preset): <b>{resolvedModelLabel}</b></div>
          </div>
        </div>
      </div>
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
    </>
  );
}
