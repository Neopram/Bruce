
import React, { useState } from "react";
import axios from "axios";

export default function ArchetypeSelector() {
  const [nombre, setNombre] = useState("");
  const [respuesta, setRespuesta] = useState(null);

  const handleGetArchetype = async () => {
    const res = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/arquetipo`, { nombre });
    setRespuesta(res.data);
  };

  return (
    <div className="bg-white p-6 shadow rounded-xl space-y-4 max-w-xl mx-auto mt-6">
      <h2 className="text-lg font-bold">🎭 Selector de Arquetipo Cognitivo</h2>
      <input className="w-full border rounded p-2" placeholder="Ej: warren_buffett, scalper_ninja" value={nombre} onChange={(e) => setNombre(e.target.value)} />
      <button onClick={handleGetArchetype} className="bg-purple-600 text-white px-4 py-2 rounded">🔁 Activar Arquetipo</button>
      {respuesta && (
        <div className="bg-gray-100 p-3 rounded text-sm mt-2 space-y-1">
          {Object.entries(respuesta).map(([key, val], idx) => (
            <div key={idx}><b>{key}:</b> {val}</div>
          ))}
        </div>
      )}
    </div>
  );
}
