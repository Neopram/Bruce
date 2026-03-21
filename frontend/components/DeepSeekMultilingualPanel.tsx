
import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Input from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "react-hot-toast";

const models = ["deepseek", "phi3", "tinyllama"];
const languages = ["en", "es", "fr", "de", "zh", "ar"];

export default function DeepSeekMultilingualPanel() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");
  const [model, setModel] = useState("deepseek");
  const [lang, setLang] = useState("en");

  const handleSend = async () => {
    try {
      const res = await fetch("http://localhost:8001/ai/multilingual-deepseek", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message, model, lang })
      });
      const data = await res.json();
      setResponse(data.response || "No response");
    } catch (err) {
      toast.error("Error communicating with Bruce.");
    }
  };

  return (
    <Card className="p-4 rounded-2xl shadow-lg bg-white dark:bg-black border border-gray-700">
      <CardContent>
        <h2 className="text-2xl font-bold mb-4">🌐 DeepSeek Multilingual Panel</h2>
        <div className="flex flex-col md:flex-row gap-4">
          <div className="w-full md:w-1/2">
            <Textarea
              className="h-32"
              placeholder="Ask something..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
            <div className="flex gap-2 mt-2">
              <select
                className="p-2 border rounded"
                value={model}
                onChange={(e) => setModel(e.target.value)}
              >
                {models.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
              <select
                className="p-2 border rounded"
                value={lang}
                onChange={(e) => setLang(e.target.value)}
              >
                {languages.map((l) => (
                  <option key={l} value={l}>{l.toUpperCase()}</option>
                ))}
              </select>
              <Button onClick={handleSend}>Send</Button>
            </div>
          </div>
          <div className="w-full md:w-1/2">
            <h3 className="font-semibold mb-2">Bruce says:</h3>
            <div className="p-2 border rounded h-32 overflow-y-auto whitespace-pre-wrap">
              {response}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
