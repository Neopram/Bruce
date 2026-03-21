// frontend/src/pages/bruce-terminal.tsx

import { useState } from "react";

export default function BruceTerminal() {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const handleCommand = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = `> ${input}`;
    setHistory((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/terminal/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();
      setHistory((prev) => [...prev, data.response || "⚠️ No response received"]);
    } catch (err) {
      setHistory((prev) => [...prev, "❌ Error communicating with Bruce"]);
    } finally {
      setLoading(false);
      setInput("");
    }
  };

  return (
    <div className="min-h-screen bg-black text-green-500 font-mono p-4">
      <h1 className="text-xl mb-4">🧠 Bruce Terminal</h1>
      <div className="border border-green-700 rounded p-4 mb-4 h-96 overflow-y-auto bg-black">
        {history.map((line, i) => (
          <div key={i} className="whitespace-pre-wrap">{line}</div>
        ))}
        {loading && <div>Bruce is thinking...</div>}
      </div>

      <form onSubmit={handleCommand}>
        <input
          className="w-full bg-black border border-green-500 px-3 py-2 text-green-500 focus:outline-none"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message for Bruce..."
        />
      </form>
    </div>
  );
}
