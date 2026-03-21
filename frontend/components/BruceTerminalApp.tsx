
import React, { useState, useEffect, useRef } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import Input from "@/components/ui/input";
import { Sun, Moon, Mic, Send, Volume2 } from "lucide-react";
import { useTheme } from "next-themes";
import { ModelSwitcher } from "./ModelSwitcher";
import { PersonalitySelector } from "./PersonalitySelector";

const BruceTerminalApp = () => {
  const { theme, setTheme } = useTheme();
  const [input, setInput] = useState("");
  const [conversation, setConversation] = useState<{ role: string; text: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    setLoading(true);
    const userMessage = { role: "user", text: input };
    setConversation((prev) => [...prev, userMessage]);

    const res = await fetch("/api/terminal/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: input }),
    });

    const data = await res.json();
    const bruceReply = { role: "bruce", text: data.output || "No response." };
    setConversation((prev) => [...prev, bruceReply]);
    setInput("");
    setLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const speak = (text) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    window.speechSynthesis.speak(utterance);
  };

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  return (
    <div className="flex flex-col h-screen dark:bg-black bg-white transition-all duration-300">
      <header className="p-4 flex items-center justify-between shadow-md dark:bg-gray-900 bg-gray-100">
        <h1 className="text-xl font-bold text-primary">🤖 Bruce Terminal</h1>
        <Button variant="ghost" onClick={toggleTheme}>
          {theme === "dark" ? <Sun /> : <Moon />}
        </Button>
      </header>

      <div className="flex gap-4 px-6 pt-4">
        <ModelSwitcher />
        <PersonalitySelector />
      </div>


      <main className="flex-grow overflow-y-auto p-6 space-y-4">
        {conversation.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-xl px-4 py-2 rounded-xl text-sm shadow-md
              ${msg.role === "user" ? "bg-blue-500 text-white" : "bg-gray-200 dark:bg-gray-800 dark:text-white"}`}>
              {msg.text}
              {msg.role === "bruce" && (
                <button onClick={() => speak(msg.text)} className="ml-2 text-muted-foreground hover:text-primary">
                  <Volume2 size={16} />
                </button>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </main>

      <footer className="p-4 border-t flex gap-2 items-center dark:bg-gray-900 bg-gray-100">
        <Textarea
          placeholder="Ask Bruce something..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          className="flex-grow min-h-[40px] max-h-[120px]"
        />
        <Button onClick={sendMessage} disabled={loading} className="p-2">
          <Send size={18} />
        </Button>
        <Button variant="ghost" disabled className="p-2 opacity-50" title="Voice input coming soon">
          <Mic size={18} />
        </Button>
      </footer>
    </div>
  );
};

export default BruceTerminalApp;
