import React, { useState, useRef, useEffect } from "react";
import { useApi } from "@/services/useApi";
import { useAuth } from "@/contexts/AuthContext";

export default function ChatLLM() {
  const { chat } = useApi();
  const { token } = useAuth();
  const [messages, setMessages] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const sendMessage = async () => {
    if (!input.trim()) return;
    setLoading(true);
    try {
      const res = await chat.send(input, "me");
      setMessages((prev) => [...prev, `🧠 ${res.response}`]);
      setInput("");
    } catch (e) {
      setMessages((prev) => [...prev, "⚠️ Error en la respuesta"]);
    } finally {
      setLoading(false);
    }
  };

  const handleEnter = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") sendMessage();
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full p-4 bg-white rounded-xl shadow-md space-y-4">
      <div className="flex-grow overflow-auto space-y-2">
        {messages.map((msg, idx) => (
          <div key={idx} className="text-gray-800">{msg}</div>
        ))}
        <div ref={bottomRef}></div>
      </div>
      <div className="flex space-x-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleEnter}
          className="flex-grow p-2 border rounded"
          placeholder="Escribe tu mensaje..."
        />
        <button
          onClick={sendMessage}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "..." : "Enviar"}
        </button>
      </div>
    </div>
  );
}