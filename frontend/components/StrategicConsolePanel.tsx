
"use client";
import { useEffect, useState } from "react";

export default function StrategicConsolePanel() {
  const [strategy, setStrategy] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<string>("");

  const fetchStrategy = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/strategic-intent");
      const data = await res.json();
      setStrategy(data);
    } catch {
      setStrategy(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch("/api/strategic-log");
      const data = await res.text();
      setLogs(data);
    } catch {
      setLogs("Error retrieving logs.");
    }
  };

  useEffect(() => {
    fetchStrategy();
    fetchLogs();
  }, []);

  return (
    <div className="bg-slate-900 text-white p-6 rounded-xl shadow-xl max-w-5xl mx-auto mt-10">
      <h2 className="text-2xl font-bold mb-4">🧭 Bruce Strategic Console</h2>
      {loading && <p>Loading strategic intent...</p>}
      {strategy && (
        <>
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-2">📌 Priorities</h3>
            <ul className="list-disc list-inside text-green-400">
              {strategy.priorities.map((item: string, index: number) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-2">📄 Self-Directives</h3>
            <ul className="list-disc list-inside text-blue-300">
              {strategy.self_directives.map((item: any, index: number) => (
                <li key={index}>
                  [{item.timestamp}] {item.action} → {item.target} ({item.purpose})
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-xl font-semibold mb-2">🧠 Last Reflection</h3>
            <p className="text-yellow-300">{strategy.last_reflection}</p>
          </div>
        </>
      )}
      <div className="mt-6">
        <h3 className="text-xl font-semibold mb-2">📓 Strategic Log</h3>
        <pre className="text-sm bg-black p-3 rounded overflow-auto max-h-96 border border-gray-600">
          {logs}
        </pre>
      </div>
    </div>
  );
}
