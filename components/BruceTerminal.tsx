
"use client";

import React, { useState, useEffect, useRef } from "react";
import Button from "@/components/ui/button";
import Textarea from "@/components/ui/textarea";
import { toast } from "react-hot-toast";

const BruceTerminal: React.FC = () => {
  const [history, setHistory] = useState<{ role: string; message: string }[]>(
    () => JSON.parse(localStorage.getItem("bruce_chat_history") || "[]")
  );
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [activeModel, setActiveModel] = useState("deepseek");
  const recognitionRef = useRef<any>(null);

  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  const synth = window.speechSynthesis;

  useEffect(() => {
    localStorage.setItem("bruce_chat_history", JSON.stringify(history));
  }, [history]);

  const speak = (text: string) => {
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = "es-ES";
    synth.speak(utter);
  };

  const sendPrompt = async (text: string) => {
    if (!text.trim()) return;
    setLoading(true);
    setHistory((prev) => [...prev, { role: "user", message: text }]);

    try {
      const res = await fetch("/api/terminal/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: text }),
      });
      const data = await res.json();
      setHistory((prev) => [...prev, { role: "bruce", message: data.output || "Sin respuesta." }]);
      speak(data.output || "Sin respuesta.");
    } catch (err) {
      toast.error("Error al conectar con Bruce.");
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  const handleModelChange = async (model: string) => {
    setActiveModel(model);
    await sendPrompt(`cámbiate a ${model}`);
  };

  return (
    <div className="p-4 bg-[#0c0c0c] text-white rounded-2xl shadow-xl w-full max-w-3xl mx-auto mt-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-bold">🧠 Bruce Terminal</h1>
        <span className="text-sm bg-gray-800 px-3 py-1 rounded">Modelo activo: {activeModel}</span>
      </div>

      <select
        value={activeModel}
        onChange={(e) => handleModelChange(e.target.value)}
        className="bg-black border border-gray-700 text-white px-3 py-2 rounded mb-4"
      >
        <option value="deepseek">🧠 DeepSeek</option>
        <option value="phi3">📐 Phi-3</option>
        <option value="tinyllama">⚡ TinyLlama</option>
      </select>

      <div className="bg-gray-900 p-4 rounded h-96 overflow-y-auto mb-4">
        {history.map((item, idx) => (
          <div key={idx} className="mb-2">
            <strong className={item.role === "user" ? "text-blue-400" : "text-green-400"}>
              {item.role === "user" ? "Tú" : "Bruce"}:
            </strong>{" "}
            {item.message}
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Escríbele a Bruce..."
          className="flex-1"
        />
        <Button onClick={() => sendPrompt(input)} disabled={loading}>
          Enviar
        </Button>
      </div>
    </div>
  );
};

export default BruceTerminal;
