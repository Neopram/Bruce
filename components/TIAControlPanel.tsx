import React, { useState, useCallback } from "react";

interface Task {
  id: string;
  description: string;
  status: "queued" | "planning" | "executing" | "done" | "failed";
  createdAt: string;
  completedAt?: string;
  result?: string;
}

const STATUS_STYLES: Record<Task["status"], { bg: string; text: string; label: string }> = {
  queued:    { bg: "bg-gray-700",   text: "text-gray-300",  label: "Queued" },
  planning:  { bg: "bg-blue-900/50",  text: "text-blue-400",  label: "Planning" },
  executing: { bg: "bg-yellow-900/50", text: "text-yellow-400", label: "Executing" },
  done:      { bg: "bg-green-900/50", text: "text-green-400", label: "Done" },
  failed:    { bg: "bg-red-900/50",   text: "text-red-400",   label: "Failed" },
};

let _id = 0;

export default function TIAControlPanel() {
  const [input, setInput] = useState("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeTask = useCallback(async (description: string) => {
    const id = `tia-${++_id}`;
    const newTask: Task = { id, description, status: "queued", createdAt: new Date().toISOString() };
    setTasks((prev) => [newTask, ...prev]);

    setTasks((prev) => prev.map((t) => t.id === id ? { ...t, status: "planning" } : t));

    try {
      setLoading(true);
      setError(null);

      setTasks((prev) => prev.map((t) => t.id === id ? { ...t, status: "executing" } : t));

      const res = await fetch("/api/v1/tia/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: description }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      setTasks((prev) =>
        prev.map((t) =>
          t.id === id ? { ...t, status: "done", completedAt: new Date().toISOString(), result: data.result } : t
        )
      );
    } catch (e: any) {
      setError(e.message);
      setTasks((prev) => prev.map((t) => t.id === id ? { ...t, status: "failed" } : t));
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSubmit = () => {
    if (!input.trim()) return;
    executeTask(input.trim());
    setInput("");
  };

  const activeTasks = tasks.filter((t) => t.status !== "done" && t.status !== "failed");
  const history = tasks.filter((t) => t.status === "done" || t.status === "failed");

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <h2 className="text-xl font-bold">TIA Control Panel</h2>
      <p className="text-sm text-gray-400">Task Intelligence &amp; Autonomy Engine</p>

      {/* Input */}
      <div className="flex gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder="Describe a task for Bruce..."
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-cyan-500" />
        <button onClick={handleSubmit} disabled={loading || !input.trim()}
          className="px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:bg-gray-700 disabled:text-gray-500 font-semibold transition text-sm">
          Execute
        </button>
      </div>

      {error && (
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-3 text-sm">{error}</div>
      )}

      {/* Task Queue */}
      {activeTasks.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-gray-400">Active Tasks</h3>
          {activeTasks.map((t) => {
            const s = STATUS_STYLES[t.status];
            return (
              <div key={t.id} className={`${s.bg} border border-gray-700 rounded-lg p-3 flex items-center gap-3`}>
                {(t.status === "planning" || t.status === "executing") && (
                  <div className="animate-spin h-4 w-4 border-2 border-cyan-400 border-t-transparent rounded-full" />
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">{t.description}</p>
                  <p className="text-xs text-gray-500">{new Date(t.createdAt).toLocaleTimeString()}</p>
                </div>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded ${s.text} ${s.bg}`}>{s.label}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* History */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-gray-400">History ({history.length})</h3>
        {history.length === 0 ? (
          <p className="text-sm text-gray-600">No completed tasks yet.</p>
        ) : (
          <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
            {history.map((t) => {
              const s = STATUS_STYLES[t.status];
              return (
                <div key={t.id} className="bg-gray-800 border border-gray-700/50 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium truncate flex-1">{t.description}</p>
                    <span className={`text-xs font-semibold ml-2 ${s.text}`}>{s.label}</span>
                  </div>
                  {t.result && <p className="text-xs text-gray-400 mt-1">{t.result}</p>}
                  {t.completedAt && (
                    <p className="text-xs text-gray-600 mt-1">{new Date(t.completedAt).toLocaleString()}</p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
