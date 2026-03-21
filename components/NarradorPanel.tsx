
import React, { useState } from "react";
import axios from "axios";

export default function NarradorPanel() {
  const [razon, setRazon] = useState("");
  const [modelo, setModelo] = useState("PPO");
  const [resultado, setResultado] = useState("");
  const [respuesta, setRespuesta] = useState("");

  const handleExplicar = async () => {
    const operacion = {
      razon,
      modelo,
      resultado,
      fecha: new Date().toISOString(),
      decision: "ejecutar",
      alternativa: "esperar"
    };
    const res = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/explicar`, operacion);
    setRespuesta(res.data.response);
  };

  const handleContrafactual = async () => {
    const operacion = {
      razon,
      modelo,
      resultado,
      fecha: new Date().toISOString(),
      decision: "ejecutar",
      alternativa: "esperar"
    };
    const res = await axios.post(`${process.env.NEXT_PUBLIC_API_URL}/contrafactual`, operacion);
    setRespuesta(res.data.response);
  };

  return (
    <div className="bg-white p-6 shadow rounded-xl space-y-4 max-w-xl mx-auto mt-6">
      <h2 className="text-lg font-bold">🧠 Narrador Cognitivo + Pensamiento Contrafactual</h2>
      <input className="w-full border rounded p-2" placeholder="Razón de la operación" value={razon} onChange={(e) => setRazon(e.target.value)} />
      <input className="w-full border rounded p-2" placeholder="Resultado obtenido" value={resultado} onChange={(e) => setResultado(e.target.value)} />
      <div className="flex space-x-2">
        <button onClick={handleExplicar} className="bg-blue-600 text-white px-4 py-2 rounded">🧠 Explicar</button>
        <button onClick={handleContrafactual} className="bg-indigo-600 text-white px-4 py-2 rounded">🤔 Contrafactual</button>
      </div>
      {respuesta && <div className="bg-gray-100 p-3 rounded text-sm">{respuesta}</div>}
    </div>
  );
}
