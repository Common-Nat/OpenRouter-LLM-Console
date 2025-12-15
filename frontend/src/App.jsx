import { useMemo, useState } from "react";
import ModelSelector from "./components/ModelSelector.jsx";
import ProfileManager from "./components/ProfileManager.jsx";
import SearchBar from "./components/SearchBar.jsx";
import ErrorBoundary from "./components/ErrorBoundary.jsx";
import ChatTab from "./tabs/ChatTab.jsx";
import CodeTab from "./tabs/CodeTab.jsx";
import DocumentsTab from "./tabs/DocumentsTab.jsx";
import PlaygroundTab from "./tabs/PlaygroundTab.jsx";
import UsageTab from "./tabs/UsageTab.jsx";

const TABS = ["Chat", "Code", "Documents", "Playground", "Usage"];

export default function App() {
  const [tab, setTab] = useState("Chat");
  const [modelId, setModelId] = useState("");
  const [profileId, setProfileId] = useState("");
  const [profiles, setProfiles] = useState([]);

  const selectedProfile = useMemo(() => profiles.find(p => String(p.id) === String(profileId)), [profiles, profileId]);

  const body = useMemo(() => {
    switch (tab) {
      case "Chat": return <ErrorBoundary context={{ tab: "Chat", modelId, profileId }}><ChatTab modelId={modelId} profileId={profileId} profiles={profiles} selectedProfile={selectedProfile} /></ErrorBoundary>;
      case "Code": return <ErrorBoundary context={{ tab: "Code", modelId }}><CodeTab modelId={modelId} profile={selectedProfile} /></ErrorBoundary>;
      case "Documents": return <ErrorBoundary context={{ tab: "Documents", modelId, profileId }}><DocumentsTab modelId={modelId} profileId={profileId} profiles={profiles} selectedProfile={selectedProfile} /></ErrorBoundary>;
      case "Playground": return <ErrorBoundary context={{ tab: "Playground" }}><PlaygroundTab /></ErrorBoundary>;
      case "Usage": return <ErrorBoundary context={{ tab: "Usage" }}><UsageTab /></ErrorBoundary>;
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

      <SearchBar onResultClick={(result) => {
        console.log("Search result clicked:", result);
        // TODO: Navigate to session or highlight message
      }} />

      {body}

      <div className="muted small" style={{marginTop: 18}}>
        Backend: <code>localhost:8000</code> • Frontend: <code>localhost:5173</code>
      </div>
    </div>
  );
}
