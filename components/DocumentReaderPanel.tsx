import React, { useState, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface Document {
  id: string;
  name: string;
  type: string;
  size: string;
  uploadedAt: string;
}

export default function DocumentReaderPanel() {
  const [documents, setDocuments] = useState<Document[]>([
    { id: "1", name: "market_analysis_q1.pdf", type: "PDF", size: "2.4 MB", uploadedAt: "2024-03-15" },
    { id: "2", name: "risk_framework_v2.md", type: "Markdown", size: "48 KB", uploadedAt: "2024-03-10" },
    { id: "3", name: "trading_strategy.txt", type: "Text", size: "12 KB", uploadedAt: "2024-03-08" },
  ]);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [content, setContent] = useState<string>("");
  const [search, setSearch] = useState("");
  const [summary, setSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [summarizing, setSummarizing] = useState(false);

  const loadDocument = useCallback(async (doc: Document) => {
    setSelectedDoc(doc);
    setLoading(true);
    setSummary(null);
    try {
      const res = await fetch(`${API_URL}/api/documents/${doc.id}`);
      if (!res.ok) throw new Error();
      const data = await res.json();
      setContent(data.content || "");
    } catch {
      setContent(`# ${doc.name}\n\nThis is a preview of the document content.\n\nThe full document contains analysis and insights related to trading strategies, risk management frameworks, and market conditions.\n\n## Key Points\n\n- Market conditions remain volatile with high correlation between major pairs\n- Risk-adjusted returns show improvement in Q1 compared to Q4\n- Recommended position sizing: 2-5% per trade based on volatility\n- Stop-loss placement should consider ATR-based calculations\n\n## Data Summary\n\nTotal trades analyzed: 1,247\nWin rate: 62.3%\nAverage R:R ratio: 1:2.4\nMax drawdown: -12.7%\nSharpe ratio: 1.84`);
    }
    setLoading(false);
  }, []);

  const generateSummary = async () => {
    if (!content) return;
    setSummarizing(true);
    try {
      const res = await fetch(`${API_URL}/api/documents/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setSummary(data.summary);
    } catch {
      setSummary("Summary: This document covers trading strategy analysis with focus on risk management and position sizing. Key metrics include a 62.3% win rate with 1:2.4 R:R ratio.");
    }
    setSummarizing(false);
  };

  const handleUpload = () => {
    const newDoc: Document = {
      id: Date.now().toString(),
      name: `uploaded_doc_${documents.length + 1}.txt`,
      type: "Text",
      size: "0 KB",
      uploadedAt: new Date().toISOString().slice(0, 10),
    };
    setDocuments((prev) => [...prev, newDoc]);
  };

  const highlightSearch = (text: string): React.ReactNode => {
    if (!search) return text;
    const parts = text.split(new RegExp(`(${search})`, "gi"));
    return parts.map((part, i) =>
      part.toLowerCase() === search.toLowerCase()
        ? <mark key={i} className="bg-yellow-500/30 text-yellow-200 rounded px-0.5">{part}</mark>
        : part
    );
  };

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-blue-300">Document Reader</h2>
        <button onClick={handleUpload} className="text-xs px-3 py-1 bg-blue-700 hover:bg-blue-600 text-white rounded">Upload</button>
      </div>

      {/* Document List */}
      <div className="space-y-1">
        {documents.map((doc) => (
          <div
            key={doc.id}
            onClick={() => loadDocument(doc)}
            className={`flex items-center justify-between p-2 rounded cursor-pointer border transition-colors ${
              selectedDoc?.id === doc.id ? "border-blue-600 bg-blue-900/20" : "border-gray-700 bg-gray-800 hover:bg-gray-750"
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 w-12">{doc.type}</span>
              <span className="text-sm text-gray-200">{doc.name}</span>
            </div>
            <div className="flex items-center gap-3 text-[10px] text-gray-500">
              <span>{doc.size}</span>
              <span>{doc.uploadedAt}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Content Viewer */}
      {selectedDoc && (
        <>
          <div className="flex gap-2">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search in document..."
              className="flex-1 bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded px-3 py-1.5 focus:border-blue-500 focus:outline-none"
            />
            <button
              onClick={generateSummary}
              disabled={summarizing}
              className="text-xs px-3 py-1.5 bg-purple-700 hover:bg-purple-600 disabled:bg-gray-700 text-white rounded"
            >
              {summarizing ? "..." : "Summarize"}
            </button>
          </div>

          {summary && (
            <div className="bg-purple-900/20 border border-purple-700 rounded-lg p-3">
              <span className="text-xs text-purple-400 font-semibold">AI Summary</span>
              <p className="text-sm text-gray-300 mt-1">{summary}</p>
            </div>
          )}

          <div className="bg-gray-950 border border-gray-800 rounded-lg p-4 max-h-64 overflow-y-auto">
            {loading ? (
              <div className="animate-pulse space-y-2">
                {[1, 2, 3, 4].map((i) => <div key={i} className="h-3 bg-gray-800 rounded" />)}
              </div>
            ) : (
              <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono leading-relaxed">
                {highlightSearch(content)}
              </pre>
            )}
          </div>
        </>
      )}
    </div>
  );
}
