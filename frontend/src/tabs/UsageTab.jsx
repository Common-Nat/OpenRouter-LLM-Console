import { useState, useEffect, useMemo, useCallback } from "react";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { format, subDays, startOfDay, endOfDay, differenceInDays } from "date-fns";
import { getUsageTimeline, getUsageStats, apiGet } from "../api/client.js";

const DATE_PRESETS = {
  today: { label: "Today", days: 0 },
  week: { label: "7 Days", days: 7 },
  month: { label: "30 Days", days: 30 },
  all: { label: "All Time", days: null }
};

export default function UsageTab() {
  // Date range state
  const [preset, setPreset] = useState("month");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  
  // Data state
  const [timeline, setTimeline] = useState([]);
  const [stats, setStats] = useState(null);
  const [modelUsage, setModelUsage] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Budget state (localStorage)
  const [budgets, setBudgets] = useState(() => {
    const saved = localStorage.getItem("usage_budgets");
    return saved ? JSON.parse(saved) : { daily: 1.0, weekly: 5.0, monthly: 20.0 };
  });
  const [showBudgetSettings, setShowBudgetSettings] = useState(false);

  // Calculate date range based on preset
  const dateRange = useMemo(() => {
    const today = new Date();
    if (preset === "today") {
      return {
        start: format(startOfDay(today), "yyyy-MM-dd"),
        end: format(endOfDay(today), "yyyy-MM-dd")
      };
    } else if (preset === "week") {
      return {
        start: format(subDays(today, 6), "yyyy-MM-dd"),
        end: format(today, "yyyy-MM-dd")
      };
    } else if (preset === "month") {
      return {
        start: format(subDays(today, 29), "yyyy-MM-dd"),
        end: format(today, "yyyy-MM-dd")
      };
    } else if (preset === "custom") {
      return { start: startDate, end: endDate };
    }
    return { start: null, end: null }; // all time
  }, [preset, startDate, endDate]);

  // Auto-select granularity based on date range
  const granularity = useMemo(() => {
    if (!dateRange.start || !dateRange.end) return "day";
    const days = differenceInDays(new Date(dateRange.end), new Date(dateRange.start));
    if (days <= 14) return "day";
    if (days <= 90) return "week";
    return "month";
  }, [dateRange]);

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [timelineData, statsData, modelData] = await Promise.all([
        getUsageTimeline(dateRange.start, dateRange.end, granularity),
        getUsageStats(dateRange.start, dateRange.end),
        apiGet("/api/usage/models")
      ]);
      setTimeline(timelineData || []);
      setStats(statsData);
      setModelUsage(modelData || []);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, [dateRange, granularity]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Save budgets to localStorage
  useEffect(() => {
    localStorage.setItem("usage_budgets", JSON.stringify(budgets));
  }, [budgets]);

  // Calculate budget alerts
  const budgetAlerts = useMemo(() => {
    if (!stats || !timeline.length) return [];
    
    const alerts = [];
    const today = format(new Date(), "yyyy-MM-dd");
    
    // Daily budget check
    const todayUsage = timeline.find(t => t.period === today);
    if (todayUsage && budgets.daily > 0) {
      const percent = (todayUsage.total_cost / budgets.daily) * 100;
      if (percent >= 100) {
        alerts.push({ type: "critical", period: "daily", percent: percent.toFixed(0), cost: todayUsage.total_cost, limit: budgets.daily });
      } else if (percent >= 80) {
        alerts.push({ type: "warning", period: "daily", percent: percent.toFixed(0), cost: todayUsage.total_cost, limit: budgets.daily });
      }
    }
    
    // Weekly budget check (last 7 days)
    const weekCost = timeline.slice(-7).reduce((sum, t) => sum + (t.total_cost || 0), 0);
    if (budgets.weekly > 0) {
      const percent = (weekCost / budgets.weekly) * 100;
      if (percent >= 100) {
        alerts.push({ type: "critical", period: "weekly", percent: percent.toFixed(0), cost: weekCost, limit: budgets.weekly });
      } else if (percent >= 80) {
        alerts.push({ type: "warning", period: "weekly", percent: percent.toFixed(0), cost: weekCost, limit: budgets.weekly });
      }
    }
    
    // Monthly budget check (last 30 days)
    const monthCost = timeline.slice(-30).reduce((sum, t) => sum + (t.total_cost || 0), 0);
    if (budgets.monthly > 0) {
      const percent = (monthCost / budgets.monthly) * 100;
      if (percent >= 100) {
        alerts.push({ type: "critical", period: "monthly", percent: percent.toFixed(0), cost: monthCost, limit: budgets.monthly });
      } else if (percent >= 80) {
        alerts.push({ type: "warning", period: "monthly", percent: percent.toFixed(0), cost: monthCost, limit: budgets.monthly });
      }
    }
    
    return alerts;
  }, [stats, timeline, budgets]);

  // Export to CSV
  const exportCSV = useCallback(async () => {
    try {
      // Fetch detailed usage logs for the date range
      const response = await fetch(`/api/usage/sessions/${dateRange.start || "all"}`);
      const logs = await response.json();
      
      const csv = [
        ["Date", "Session ID", "Model", "Prompt Tokens", "Completion Tokens", "Total Tokens", "Cost (USD)"],
        ...logs.map(log => [
          log.created_at,
          log.session_id,
          log.model_name || log.openrouter_id || "Unknown",
          log.prompt_tokens || 0,
          log.completion_tokens || 0,
          log.total_tokens || 0,
          (log.cost_usd || 0).toFixed(6)
        ])
      ].map(row => row.join(",")).join("\n");
      
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const filename = `usage_${dateRange.start || "all"}_to_${dateRange.end || "today"}.csv`;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(`Export failed: ${e}`);
    }
  }, [dateRange]);

  // Chart data formatting
  const chartData = useMemo(() => {
    return timeline.map(t => ({
      date: format(new Date(t.period), granularity === "month" ? "MMM yyyy" : "MMM dd"),
      cost: Number(t.total_cost || 0),
      tokens: Number(t.total_tokens || 0),
      requests: Number(t.request_count || 0)
    }));
  }, [timeline, granularity]);

  const modelChartData = useMemo(() => {
    return modelUsage.slice(0, 10).map(m => ({
      name: (m.model_name || m.openrouter_id || "Unknown").substring(0, 30),
      cost: Number(m.cost_usd || 0),
      tokens: Number(m.total_tokens || 0)
    }));
  }, [modelUsage]);

  return (
    <div className="col" style={{ gap: 12 }}>
      {/* Header with controls */}
      <div className="card">
        <div className="topbar">
          <div>
            <div style={{ fontWeight: 700, fontSize: 18 }}>Usage Dashboard</div>
            <div className="muted small">Cost tracking, model comparison, and budget monitoring</div>
          </div>
          <div className="row" style={{ gap: 8 }}>
            <button className="btn" onClick={fetchData} disabled={loading}>
              {loading ? "Loading..." : "Refresh"}
            </button>
            <button className="btn" onClick={exportCSV}>
              Export CSV
            </button>
            <button className="btn" onClick={() => setShowBudgetSettings(!showBudgetSettings)}>
              {showBudgetSettings ? "Hide" : "Budget Settings"}
            </button>
          </div>
        </div>

        {/* Date range selector */}
        <div className="row wrap" style={{ gap: 8, marginTop: 12 }}>
          {Object.entries(DATE_PRESETS).map(([key, { label }]) => (
            <button
              key={key}
              className={`btn ${preset === key ? "active" : ""}`}
              onClick={() => setPreset(key)}
              style={{ fontSize: 13 }}
            >
              {label}
            </button>
          ))}
          <button
            className={`btn ${preset === "custom" ? "active" : ""}`}
            onClick={() => setPreset("custom")}
            style={{ fontSize: 13 }}
          >
            Custom
          </button>
        </div>

        {/* Custom date inputs */}
        {preset === "custom" && (
          <div className="row" style={{ gap: 8, marginTop: 8 }}>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              style={{ padding: "6px 10px", borderRadius: 4, border: "1px solid #444" }}
            />
            <span className="muted">to</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              style={{ padding: "6px 10px", borderRadius: 4, border: "1px solid #444" }}
            />
          </div>
        )}

        {/* Budget settings panel */}
        {showBudgetSettings && (
          <div className="card" style={{ marginTop: 12, padding: 12, background: "#1a1a1a" }}>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>Budget Limits (USD)</div>
            <div className="row wrap" style={{ gap: 16 }}>
              <div>
                <label className="muted small">Daily</label>
                <input
                  type="number"
                  step="0.10"
                  min="0"
                  value={budgets.daily}
                  onChange={(e) => setBudgets({ ...budgets, daily: parseFloat(e.target.value) || 0 })}
                  style={{ width: 100, padding: "4px 8px", marginTop: 4 }}
                />
              </div>
              <div>
                <label className="muted small">Weekly</label>
                <input
                  type="number"
                  step="0.50"
                  min="0"
                  value={budgets.weekly}
                  onChange={(e) => setBudgets({ ...budgets, weekly: parseFloat(e.target.value) || 0 })}
                  style={{ width: 100, padding: "4px 8px", marginTop: 4 }}
                />
              </div>
              <div>
                <label className="muted small">Monthly</label>
                <input
                  type="number"
                  step="1.00"
                  min="0"
                  value={budgets.monthly}
                  onChange={(e) => setBudgets({ ...budgets, monthly: parseFloat(e.target.value) || 0 })}
                  style={{ width: 100, padding: "4px 8px", marginTop: 4 }}
                />
              </div>
            </div>
            <div className="muted small" style={{ marginTop: 8 }}>
              Alerts trigger at 80% (warning) and 100% (critical) of each limit
            </div>
          </div>
        )}
      </div>

      {error && <div className="card" style={{ color: "#ffb4b4" }}>{error}</div>}

      {/* Budget alerts */}
      {budgetAlerts.map((alert, idx) => (
        <div
          key={idx}
          className="card"
          style={{
            background: alert.type === "critical" ? "#3d1f1f" : "#3d2f1f",
            borderLeft: `4px solid ${alert.type === "critical" ? "#ff4444" : "#ffaa44"}`
          }}
        >
          <div style={{ fontWeight: 600 }}>
            {alert.type === "critical" ? "⛔ Budget Exceeded" : "⚠️ Budget Warning"}
          </div>
          <div className="muted small">
            {alert.period.charAt(0).toUpperCase() + alert.period.slice(1)} usage: ${alert.cost.toFixed(4)} / ${alert.limit.toFixed(2)} ({alert.percent}%)
          </div>
        </div>
      ))}

      {/* Summary stats */}
      {stats && (
        <div className="card">
          <div style={{ fontWeight: 700, marginBottom: 12 }}>Summary Statistics</div>
          <div className="row wrap" style={{ gap: 12 }}>
            <StatCard label="Total Cost" value={`$${(stats.total_cost || 0).toFixed(4)}`} />
            <StatCard label="Total Requests" value={stats.total_requests || 0} />
            <StatCard label="Total Tokens" value={(stats.total_tokens || 0).toLocaleString()} />
            <StatCard label="Avg Cost/Request" value={`$${(stats.avg_cost_per_request || 0).toFixed(6)}`} />
            <StatCard label="Unique Models" value={stats.unique_models || 0} />
            <StatCard label="Unique Sessions" value={stats.unique_sessions || 0} />
          </div>
        </div>
      )}

      {/* Cost over time chart */}
      {chartData.length > 0 && (
        <div className="card">
          <div style={{ fontWeight: 700, marginBottom: 12 }}>Cost Over Time</div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="date" stroke="#888" style={{ fontSize: 12 }} />
              <YAxis stroke="#888" style={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{ background: "#1a1a1a", border: "1px solid #444", borderRadius: 4 }}
                labelStyle={{ color: "#aaa" }}
              />
              <Legend />
              <Line type="monotone" dataKey="cost" stroke="#4a9eff" strokeWidth={2} name="Cost (USD)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Token usage chart */}
      {chartData.length > 0 && (
        <div className="card">
          <div style={{ fontWeight: 700, marginBottom: 12 }}>Token Usage Over Time</div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="date" stroke="#888" style={{ fontSize: 12 }} />
              <YAxis stroke="#888" style={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{ background: "#1a1a1a", border: "1px solid #444", borderRadius: 4 }}
                labelStyle={{ color: "#aaa" }}
              />
              <Legend />
              <Line type="monotone" dataKey="tokens" stroke="#44ff88" strokeWidth={2} name="Tokens" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Model comparison chart */}
      {modelChartData.length > 0 && (
        <div className="card">
          <div style={{ fontWeight: 700, marginBottom: 12 }}>Model Cost Comparison (Top 10)</div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={modelChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis type="number" stroke="#888" style={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="name" stroke="#888" style={{ fontSize: 11 }} width={150} />
              <Tooltip
                contentStyle={{ background: "#1a1a1a", border: "1px solid #444", borderRadius: 4 }}
                labelStyle={{ color: "#aaa" }}
              />
              <Legend />
              <Bar dataKey="cost" fill="#ff6b6b" name="Cost (USD)" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Model usage table */}
      {modelUsage.length > 0 && (
        <div className="card">
          <div style={{ fontWeight: 700, marginBottom: 12 }}>Model Usage Details</div>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #333" }}>
                  <th style={{ textAlign: "left", padding: "8px 4px" }}>Model</th>
                  <th style={{ textAlign: "right", padding: "8px 4px" }}>Prompt Tokens</th>
                  <th style={{ textAlign: "right", padding: "8px 4px" }}>Completion Tokens</th>
                  <th style={{ textAlign: "right", padding: "8px 4px" }}>Total Tokens</th>
                  <th style={{ textAlign: "right", padding: "8px 4px" }}>Cost (USD)</th>
                </tr>
              </thead>
              <tbody>
                {modelUsage.map((m, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #222" }}>
                    <td style={{ padding: "8px 4px" }}>{m.model_name || m.openrouter_id || "Unknown"}</td>
                    <td style={{ textAlign: "right", padding: "8px 4px" }}>{(m.prompt_tokens || 0).toLocaleString()}</td>
                    <td style={{ textAlign: "right", padding: "8px 4px" }}>{(m.completion_tokens || 0).toLocaleString()}</td>
                    <td style={{ textAlign: "right", padding: "8px 4px" }}>{(m.total_tokens || 0).toLocaleString()}</td>
                    <td style={{ textAlign: "right", padding: "8px 4px" }}>${(m.cost_usd || 0).toFixed(6)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!loading && timeline.length === 0 && (
        <div className="card">
          <div className="muted">No usage data found for the selected date range.</div>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="card" style={{ flex: 1, minWidth: 140, padding: 12 }}>
      <div className="muted small">{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{value}</div>
    </div>
  );
}
