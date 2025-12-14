import { useEffect, useMemo, useState } from "react";
import { apiDelete, apiGet, apiPost, apiPut } from "../api/client.js";

const BLANK_FORM = { name: "", system_prompt: "", temperature: "0.7", max_tokens: "2048", openrouter_preset: "" };

export default function ProfileManager({ value, onChange, onProfilesChange }) {
  const [profiles, setProfiles] = useState([]);
  const [form, setForm] = useState(BLANK_FORM);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const selectedProfile = useMemo(() => profiles.find(p => String(p.id) === String(value)), [profiles, value]);
  const presetShortcuts = useMemo(() => {
    const presets = profiles
      .map(p => p.openrouter_preset)
      .filter(Boolean);
    return Array.from(new Set(presets));
  }, [profiles]);

  useEffect(() => { refresh(); }, []);
  useEffect(() => { onProfilesChange?.(profiles); }, [profiles, onProfilesChange]);
  useEffect(() => {
    if (value && !profiles.some(p => String(p.id) === String(value))) {
      onChange?.("");
    }
  }, [value, profiles, onChange]);

  async function refresh() {
    setLoading(true);
    setError("");
    try {
      const data = await apiGet("/api/profiles");
      setProfiles(data);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  function startCreate() {
    setEditingId(null);
    setForm(BLANK_FORM);
  }

  function startEdit(profile) {
    setEditingId(profile.id);
    setForm({
      name: profile.name || "",
      system_prompt: profile.system_prompt || "",
      temperature: String(profile.temperature ?? ""),
      max_tokens: String(profile.max_tokens ?? ""),
      openrouter_preset: profile.openrouter_preset || "",
    });
  }

  function parseForm() {
    return {
      name: form.name.trim(),
      system_prompt: form.system_prompt.trim() || null,
      temperature: parseFloat(form.temperature || "0.7"),
      max_tokens: parseInt(form.max_tokens || "2048", 10),
      openrouter_preset: form.openrouter_preset.trim() || null,
    };
  }

  async function saveProfile() {
    setLoading(true);
    setError("");
    try {
      const payload = parseForm();
      if (editingId) {
        await apiPut(`/api/profiles/${editingId}`, payload);
        await refresh();
        onChange?.(String(editingId));
      } else {
        const created = await apiPost("/api/profiles", payload);
        await refresh();
        onChange?.(String(created.id));
      }
      setEditingId(null);
      setForm(BLANK_FORM);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function deleteProfile(id) {
    if (!window.confirm("Delete this profile?")) return;
    setLoading(true);
    setError("");
    try {
      await apiDelete(`/api/profiles/${id}`);
      if (String(value) === String(id)) {
        onChange?.("");
      }
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card" style={{ marginTop: 12 }}>
      <div className="topbar">
        <div>
          <div style={{ fontWeight: 700 }}>Profile</div>
          <div className="muted small">Create, update, and reuse prompts + parameters.</div>
        </div>
        <button className="btn" onClick={startCreate} disabled={loading}>New</button>
      </div>

      <div className="row wrap" style={{ gap: 12 }}>
        <select
          className="input"
          style={{ minWidth: 280 }}
          value={value || ""}
          onChange={(e) => onChange?.(e.target.value)}
        >
          <option value="">Select a profile…</option>
          {profiles.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <div className="muted small" style={{ minWidth: 200 }}>
          {selectedProfile ? (
            <>
              <div><b>{selectedProfile.name}</b></div>
              <div>Temp {selectedProfile.temperature} • Max tokens {selectedProfile.max_tokens}</div>
              <div className="muted small">
                {selectedProfile.openrouter_preset ? (
                  <>Preset: {selectedProfile.openrouter_preset.startsWith("@preset/") ? selectedProfile.openrouter_preset : `@preset/${selectedProfile.openrouter_preset}`}</>
                ) : (
                  <>No preset (uses base model)</>
                )}
              </div>
            </>
          ) : (
            <div>No profile selected.</div>
          )}
        </div>
      </div>

      <div className="hr" />

      <div className="muted small" style={{ marginBottom: 8 }}>Existing profiles</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12 }}>
        {profiles.map((p) => (
          <div key={p.id} className="card" style={{ flex: 1, minWidth: 240 }}>
            <div style={{ fontWeight: 600 }}>{p.name}</div>
            <div className="muted small" style={{ margin: "6px 0" }}>
              Temp {p.temperature} • Max tokens {p.max_tokens}
            </div>
            <div className="muted small" style={{ margin: "6px 0" }}>
              {p.openrouter_preset ? (
                <>Preset: {p.openrouter_preset.startsWith("@preset/") ? p.openrouter_preset : `@preset/${p.openrouter_preset}`}</>
              ) : (
                <>No preset set</>
              )}
            </div>
            {p.system_prompt ? (
              <div className="muted small" style={{ whiteSpace: "pre-wrap" }}>
                {p.system_prompt}
              </div>
            ) : (
              <div className="muted small">(No system prompt)</div>
            )}
            <div className="row" style={{ marginTop: 10, gap: 8 }}>
              <button className="btn" onClick={() => startEdit(p)} disabled={loading}>Edit</button>
              <button className="btn" onClick={() => deleteProfile(p.id)} disabled={loading}>Delete</button>
            </div>
          </div>
        ))}
        {!profiles.length && <div className="muted small">No profiles yet.</div>}
      </div>

      <div className="hr" />

      <div className="muted small" style={{ marginBottom: 6 }}>
        {editingId ? `Editing profile #${editingId}` : "Create a new profile"}
      </div>
      <div className="row wrap" style={{ gap: 12 }}>
        <input
          className="input"
          style={{ minWidth: 200 }}
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
        <input
          className="input"
          style={{ minWidth: 120 }}
          placeholder="Temperature"
          value={form.temperature}
          onChange={(e) => setForm({ ...form, temperature: e.target.value })}
        />
        <input
          className="input"
          style={{ minWidth: 120 }}
          placeholder="Max tokens"
          value={form.max_tokens}
          onChange={(e) => setForm({ ...form, max_tokens: e.target.value })}
        />
        <input
          className="input"
          style={{ minWidth: 200 }}
          placeholder="OpenRouter preset (optional)"
          value={form.openrouter_preset}
          onChange={(e) => setForm({ ...form, openrouter_preset: e.target.value })}
        />
      </div>
      {presetShortcuts.length > 0 && (
        <div className="row wrap" style={{ gap: 8, marginTop: 6, alignItems: "center" }}>
          <div className="muted small">Quick-select preset:</div>
          {presetShortcuts.map(preset => (
            <button
              key={preset}
              className="btn"
              type="button"
              onClick={() => setForm({ ...form, openrouter_preset: preset })}
            >
              {preset.startsWith("@preset/") ? preset : `@preset/${preset}`}
            </button>
          ))}
          <button className="btn" type="button" onClick={() => setForm({ ...form, openrouter_preset: "" })}>
            Clear preset
          </button>
        </div>
      )}
      <textarea
        className="input"
        style={{ marginTop: 10, minHeight: 80 }}
        placeholder="System prompt (optional)"
        value={form.system_prompt}
        onChange={(e) => setForm({ ...form, system_prompt: e.target.value })}
      />
      <div className="row" style={{ marginTop: 10, gap: 8 }}>
        <button className="btn primary" onClick={saveProfile} disabled={loading}>
          {editingId ? "Save" : "Create"}
        </button>
        {editingId && <button className="btn" onClick={startCreate} disabled={loading}>Cancel</button>}
      </div>

      {error && <div style={{ marginTop: 10, color: "#ffb4b4" }}>{error}</div>}
      {loading && <div className="muted small" style={{ marginTop: 6 }}>Working…</div>}
    </div>
  );
}
