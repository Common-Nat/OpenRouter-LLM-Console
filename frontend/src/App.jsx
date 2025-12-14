import { useMemo, useState } from "react";
import ModelSelector from "./components/ModelSelector.jsx";
import ProfileManager from "./components/ProfileManager.jsx";
import ChatTab from "./tabs/ChatTab.jsx";
import CodeTab from "./tabs/CodeTab.jsx";
import DocumentsTab from "./tabs/DocumentsTab.jsx";
import PlaygroundTab from "./tabs/PlaygroundTab.jsx";

const TABS = ["Chat", "Code", "Documents", "Playground"];

export default function App() {
  const [tab, setTab] = useState("Chat");
  const [modelId, setModelId] = useState("");
  const [profileId, setProfileId] = useState("");
  const [profiles, setProfiles] = useState([]);

  const selectedProfile = useMemo(() => profiles.find(p => String(p.id) === String(profileId)), [profiles, profileId]);

  const body = useMemo(() => {
    switch (tab) {
      case "Chat": return <ChatTab modelId={modelId} profileId={profileId} profiles={profiles} selectedProfile={selectedProfile} />;
      case "Code": return <CodeTab modelId={modelId} profile={selectedProfile} />;
      case "Documents": return <DocumentsTab />;
      case "Playground": return <PlaygroundTab />;
      default: return null;
    }
  }, [tab, modelId, profileId, profiles, selectedProfile]);

  return (
    <div className="container">
      <div className="topbar">
        <div>
          <div style={{fontSize: 18, fontWeight: 800}}>OpenRouter LLM Console</div>
          <div className="muted small">FastAPI + SQLite + React. Streaming via SSE.</div>
        </div>
        <div className="tabs">
          {TABS.map(t => (
            <button key={t} className={`tab ${tab === t ? "active" : ""}`} onClick={()=>setTab(t)}>{t}</button>
          ))}
        </div>
      </div>

      <div style={{marginBottom: 12}}>
        <ModelSelector value={modelId} onChange={setModelId} />
      </div>

      <ProfileManager value={profileId} onChange={setProfileId} onProfilesChange={setProfiles} />

      {body}

      <div className="muted small" style={{marginTop: 18}}>
        Backend: <code>localhost:8000</code> • Frontend: <code>localhost:5173</code>
      </div>
    </div>
  );
}
