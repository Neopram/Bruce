import React, { useState } from "react";

const LANGUAGES = [
  { id: "python", label: "Python" },
  { id: "typescript", label: "TypeScript" },
  { id: "javascript", label: "JavaScript" },
  { id: "rust", label: "Rust" },
  { id: "go", label: "Go" },
  { id: "solidity", label: "Solidity" },
];

const FRAMEWORKS: Record<string, string[]> = {
  python: ["FastAPI", "Django", "Flask"],
  typescript: ["Next.js", "Express", "NestJS"],
  javascript: ["React", "Express", "Vue"],
  rust: ["Actix", "Axum", "Rocket"],
  go: ["Gin", "Echo", "Fiber"],
  solidity: ["Hardhat", "Foundry", "Truffle"],
};

export default function FullStackBuilder() {
  const [description, setDescription] = useState("");
  const [language, setLanguage] = useState("python");
  const [framework, setFramework] = useState("FastAPI");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleLangChange = (lang: string) => {
    setLanguage(lang);
    setFramework(FRAMEWORKS[lang]?.[0] ?? "");
  };

  const generate = async () => {
    if (!description.trim()) return;
    setLoading(true);
    setError(null);
    setCode("");
    try {
      const res = await fetch("/api/v1/codegen", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description, language, framework }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setCode(data.code ?? "");
    } catch (e: any) {
      setError(e.message ?? "Code generation failed");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* ignore */ }
  };

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-5">
      <h2 className="text-xl font-bold">FullStack Builder</h2>
      <p className="text-sm text-gray-400">AI-powered code generation engine</p>

      <div className="space-y-3">
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Description</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe the app, feature, or API you want to build..."
            rows={3}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm resize-none focus:outline-none focus:border-cyan-500" />
        </div>

        <div>
          <label className="text-xs text-gray-500 mb-1 block">Language</label>
          <div className="flex flex-wrap gap-2">
            {LANGUAGES.map((l) => (
              <button key={l.id} onClick={() => handleLangChange(l.id)}
                className={`px-3 py-1.5 rounded-lg text-sm border transition ${
                  language === l.id ? "border-cyan-500 bg-gray-800 text-white" : "border-gray-700 bg-gray-800/50 text-gray-500 hover:border-gray-600"
                }`}>
                {l.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-xs text-gray-500 mb-1 block">Framework</label>
          <div className="flex flex-wrap gap-2">
            {(FRAMEWORKS[language] ?? []).map((f) => (
              <button key={f} onClick={() => setFramework(f)}
                className={`px-3 py-1.5 rounded-lg text-sm border transition ${
                  framework === f ? "border-purple-500 bg-gray-800 text-white" : "border-gray-700 bg-gray-800/50 text-gray-500 hover:border-gray-600"
                }`}>
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      <button onClick={generate} disabled={loading || !description.trim()}
        className="w-full py-2.5 rounded-lg bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-600 font-semibold transition">
        {loading ? "Generating..." : "Generate Code"}
      </button>

      {error && (
        <div className="bg-red-900/40 border border-red-500 text-red-300 rounded-lg p-3 text-sm">{error}</div>
      )}

      {code && (
        <div className="relative">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-500">Generated Code ({language} / {framework})</span>
            <button onClick={copyToClipboard}
              className="text-xs px-3 py-1 rounded bg-gray-700 hover:bg-gray-600 transition">
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
          <pre className="bg-gray-950 border border-gray-800 rounded-xl p-4 text-sm font-mono text-green-400 overflow-x-auto max-h-80 overflow-y-auto whitespace-pre-wrap">
            {code}
          </pre>
        </div>
      )}
    </div>
  );
}
