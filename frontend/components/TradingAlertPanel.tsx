import React, { useState, useEffect } from "react";
import axios from "axios";

interface TradingAlert {
  id: string;
  symbol: string;
  condition: "above" | "below" | "change_pct";
  threshold: number;
  enabled: boolean;
  priority: "high" | "medium" | "low";
  triggered: boolean;
  createdAt: string;
  message?: string;
}

const PRIORITY_STYLES: Record<string, string> = {
  high: "bg-red-600 text-white",
  medium: "bg-yellow-600 text-white",
  low: "bg-green-600 text-white",
};

const TradingAlertPanel: React.FC = () => {
  const [alerts, setAlerts] = useState<TradingAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formSymbol, setFormSymbol] = useState("BTC/USDT");
  const [formCondition, setFormCondition] = useState<"above" | "below" | "change_pct">("above");
  const [formThreshold, setFormThreshold] = useState("");
  const [formPriority, setFormPriority] = useState<"high" | "medium" | "low">("medium");

  const fetchAlerts = async () => {
    try {
      const res = await axios.get("/api/trading/alerts");
      setAlerts(res.data?.alerts || []);
      setError(null);
    } catch (err: any) {
      setError(err?.response?.data?.error || "Failed to load alerts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAlerts(); }, []);

  const toggleAlert = async (id: string, enabled: boolean) => {
    try {
      await axios.patch(`/api/trading/alerts/${id}`, { enabled: !enabled });
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, enabled: !a.enabled } : a)));
    } catch { /* silent */ }
  };

  const deleteAlert = async (id: string) => {
    try {
      await axios.delete(`/api/trading/alerts/${id}`);
      setAlerts((prev) => prev.filter((a) => a.id !== id));
    } catch { /* silent */ }
  };

  const createAlert = async () => {
    if (!formThreshold) return;
    try {
      const res = await axios.post("/api/trading/alerts", {
        symbol: formSymbol,
        condition: formCondition,
        threshold: parseFloat(formThreshold),
        priority: formPriority,
      });
      setAlerts((prev) => [...prev, res.data?.alert || {
        id: `alert-${Date.now()}`, symbol: formSymbol, condition: formCondition,
        threshold: parseFloat(formThreshold), priority: formPriority, enabled: true,
        triggered: false, createdAt: new Date().toISOString(),
      }]);
      setShowForm(false);
      setFormThreshold("");
    } catch (err: any) {
      setError(err?.response?.data?.error || "Failed to create alert");
    }
  };

  const conditionLabel = (c: string) => {
    if (c === "above") return "Price Above";
    if (c === "below") return "Price Below";
    return "Change %";
  };

  return (
    <div className="bg-gray-900 text-white rounded-xl border border-gray-700 overflow-hidden">
      <div className="px-4 py-3 bg-gray-800 border-b border-gray-700 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Trading Alerts</h2>
        <button onClick={() => setShowForm(!showForm)}
          className="text-xs bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded transition">
          {showForm ? "Cancel" : "+ New Alert"}
        </button>
      </div>

      <div className="p-4 space-y-3">
        {error && <div className="bg-red-900/40 border border-red-700 text-red-300 px-3 py-2 rounded text-xs">{error}</div>}

        {/* Create Form */}
        {showForm && (
          <div className="bg-gray-800 rounded-lg p-3 space-y-3 border border-gray-600">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Symbol</label>
                <select value={formSymbol} onChange={(e) => setFormSymbol(e.target.value)}
                  className="w-full bg-gray-700 text-white text-xs rounded px-2 py-1.5 border border-gray-600">
                  {["BTC/USDT","ETH/USDT","SOL/USDT","BNB/USDT"].map((s) => <option key={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Condition</label>
                <select value={formCondition} onChange={(e) => setFormCondition(e.target.value as any)}
                  className="w-full bg-gray-700 text-white text-xs rounded px-2 py-1.5 border border-gray-600">
                  <option value="above">Price Above</option>
                  <option value="below">Price Below</option>
                  <option value="change_pct">Change %</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Threshold</label>
                <input type="number" value={formThreshold} onChange={(e) => setFormThreshold(e.target.value)}
                  placeholder="e.g. 50000" className="w-full bg-gray-700 text-white text-xs rounded px-2 py-1.5 border border-gray-600" />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Priority</label>
                <select value={formPriority} onChange={(e) => setFormPriority(e.target.value as any)}
                  className="w-full bg-gray-700 text-white text-xs rounded px-2 py-1.5 border border-gray-600">
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>
            <button onClick={createAlert} className="w-full bg-green-600 hover:bg-green-700 py-1.5 rounded text-xs font-medium transition">
              Create Alert
            </button>
          </div>
        )}

        {/* Alerts List */}
        {loading ? (
          <div className="text-center text-gray-500 text-sm py-8">Loading alerts...</div>
        ) : alerts.length === 0 ? (
          <div className="text-center text-gray-500 text-sm py-8">No alerts configured</div>
        ) : (
          <div className="space-y-2">
            {alerts.map((alert) => (
              <div key={alert.id} className={`flex items-center justify-between bg-gray-800 rounded-lg px-3 py-2 border ${alert.triggered ? "border-yellow-600" : "border-gray-700"}`}>
                <div className="flex items-center gap-2 min-w-0">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${PRIORITY_STYLES[alert.priority]}`}>
                    {alert.priority.toUpperCase()}
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{alert.symbol} - {conditionLabel(alert.condition)} ${alert.threshold}</p>
                    <p className="text-[10px] text-gray-500">{new Date(alert.createdAt).toLocaleString()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button onClick={() => toggleAlert(alert.id, alert.enabled)}
                    className={`w-8 h-4 rounded-full transition relative ${alert.enabled ? "bg-green-600" : "bg-gray-600"}`}>
                    <span className={`absolute top-0.5 w-3 h-3 bg-white rounded-full transition-all ${alert.enabled ? "left-4" : "left-0.5"}`} />
                  </button>
                  <button onClick={() => deleteAlert(alert.id)} className="text-gray-500 hover:text-red-400 transition text-sm">X</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TradingAlertPanel;
