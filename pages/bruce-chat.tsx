"use client";

import React, { useState, useEffect } from "react";
import Head from "next/head";
import Input from "@/components/ui/input";
import Textarea from "@/components/ui/textarea";
import Button from "@/components/ui/button";
import { toast } from "react-hot-toast";

const models = ["deepseek", "phi3", "tinyllama"];
const languages = ["en", "es", "fr", "de", "zh", "ar"];

interface Message {
  role: "user" | "bruce";
  content: string;
}

export default function BruceChatTerminal() {
  const [prompt, setPrompt] = useState("");
  const [conversation, setConversation] = useState<Message[]>([]);
  const [language, setLanguage] = useState("en");
  const [model, setModel] = useState("deepseek");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch("/api/models/status");
        const json = await res.json();
        setStatus(json);
      } catch {
        toast.error("Error loading model status.");
      }
    };
    fetchStatus();
  }, []);

  const handleSend = async () => {
    if (!prompt.trim()) return toast.error("Prompt is empty.");
    if (!status[model]) return toast.error(`Model ${model} not available.`);

    const userMessage: Message = { role: "user", content: prompt };
    setConversation((prev) => [...prev, userMessage]);
    setLoading(true);
    toast.loading("Bruce is thinking...");

    try {
      const res = await fetch("/api/infer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, model, language }),
      });

      const data = await res.json();
      const bruceMessage: Message = {
        role: "bruce",
        content: data.output || "No response from Bruce.",
      };

      setConversation((prev) => [...prev, bruceMessage]);
      toast.dismiss();
      toast.success("Bruce has answered.");
      setPrompt("");
    } catch {
      toast.dismiss();
      toast.error("Inference error.");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setConversation([]);
    toast("Memory wiped 🧼");
  };

  return (
    <>
      <Head>
        <title>Bruce AI – Conversational Terminal</title>
      </Head>
      <main className="min-h-screen bg-black text-white px-6 py-10 flex flex-col items-center">
        <h1 className="text-3xl font-bold mb-6">🧠 Bruce – Memory Terminal</h1>

        <div className="w-full max-w-2xl space-y-4">
          <div className="bg-zinc-900 border border-zinc-700 rounded-xl p-4 h-[400px] overflow-y-auto space-y-3">
            {conversation.map((msg, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg ${
                  msg.role === "user"
                    ? "bg-indigo-800 text-white self-end"
                    : "bg-zinc-800 text-green-400"
                }`}
              >
                <strong>{msg.role === "user" ? "You" : "Bruce"}:</strong>{" "}
                {msg.content}
              </div>
            ))}
          </div>

          <Textarea
            placeholder="Your next question for Bruce..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={3}
          />

          <div className="flex gap-4">
            <select
              className="bg-zinc-800 border border-zinc-600 px-4 py-2 rounded w-full"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {languages.map((lang) => (
                <option key={lang} value={lang}>
                  {lang.toUpperCase()}
                </option>
              ))}
            </select>

            <select
              className="bg-zinc-800 border border-zinc-600 px-4 py-2 rounded w-full"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              {models.map((m) => (
                <option key={m} value={m} disabled={!status[m]}>
                  {m} {status[m] ? "🟢" : "🔴"}
                </option>
              ))}
            </select>
          </div>

          <div className="flex gap-4">
            <Button onClick={handleSend} disabled={loading} className="w-full">
              {loading ? "Thinking..." : "Talk to Bruce"}
            </Button>
            <Button onClick={handleClear} variant="ghost">
              Clear Memory
            </Button>
          </div>
        </div>
      </main>
    </>
  );
}
