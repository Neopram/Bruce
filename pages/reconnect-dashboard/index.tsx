
import React, { useEffect, useState } from "react";

export default function ReconnectDashboard() {
  const [functions, setFunctions] = useState<any[]>([]);
  const [status, setStatus] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/reconnect/functions`)
      .then((res) => res.json())
      .then((data) => {
        setFunctions(data.functions || []);
        const defaultState = {};
        (data.functions || []).forEach((f: any, idx: number) => {
          defaultState[`${f.file}_${f.function}`] = true;
        });
        setStatus(defaultState);
      });
  }, []);

  return (
    <div className="p-6 text-white bg-zinc-900 min-h-screen">
      <h1 className="text-3xl font-bold mb-4">🧠 Reconnect Dashboard</h1>
      <p className="text-sm text-gray-400 mb-6">Funciones simbióticas dormidas detectadas y controladas visualmente.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {functions.map((f, idx) => {
          const key = `${f.file}_${f.function}`;
          return (
            <div key={idx} className="bg-zinc-800 p-4 rounded-lg shadow">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-semibold">{f.function}</h2>
                  <p className="text-xs text-gray-400">{f.file}</p>
                </div>
                <label className="inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={status[key]}
                    onChange={() => setStatus({ ...status, [key]: !status[key] })}
                  />
                  <div className="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:bg-green-500 transition-all relative">
                    <div
                      className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${
                        status[key] ? "translate-x-5" : ""
                      }`}
                    />
                  </div>
                </label>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
