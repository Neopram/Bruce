import React, { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";

interface RequestHistory {
  id: string;
  method: HttpMethod;
  endpoint: string;
  status: number;
  durationMs: number;
  response: any;
  timestamp: string;
}

const COMMON_ENDPOINTS = [
  "/bruce-api/emotion/state/default",
  "/bruce-api/cognition/status",
  "/bruce-api/inference/models",
  "/ai/self-healing/status",
  "/api/v1/agents",
  "/api/logs",
  "/api/security/status",
  "/api/diagnostics",
  "/api/sessions",
  "/health",
];

const METHOD_COLORS: Record<HttpMethod, string> = {
  GET: "text-green-400 bg-green-900/30",
  POST: "text-blue-400 bg-blue-900/30",
  PUT: "text-yellow-400 bg-yellow-900/30",
  DELETE: "text-red-400 bg-red-900/30",
};

export default function DevToolsConsole() {
  const [method, setMethod] = useState<HttpMethod>("GET");
  const [endpoint, setEndpoint] = useState(COMMON_ENDPOINTS[0]);
  const [body, setBody] = useState("{}");
  const [executing, setExecuting] = useState(false);
  const [response, setResponse] = useState<any>(null);
  const [responseStatus, setResponseStatus] = useState<number | null>(null);
  const [history, setHistory] = useState<RequestHistory[]>([]);
  const [error, setError] = useState<string | null>(null);

  const executeRequest = async () => {
    setExecuting(true);
    setError(null);
    const start = Date.now();

    try {
      const options: RequestInit = { method };
      if (method !== "GET" && method !== "DELETE") {
        options.headers = { "Content-Type": "application/json" };
        options.body = body;
      }

      const res = await fetch(`${API_URL}${endpoint}`, options);
      const duration = Date.now() - start;
      let data: any;
      const contentType = res.headers.get("content-type") || "";
      if (contentType.includes("json")) {
        data = await res.json();
      } else {
        data = await res.text();
      }

      setResponse(data);
      setResponseStatus(res.status);

      const entry: RequestHistory = {
        id: Date.now().toString(),
        method,
        endpoint,
        status: res.status,
        durationMs: duration,
        response: data,
        timestamp: new Date().toISOString().slice(11, 19),
      };
      setHistory((prev) => [entry, ...prev].slice(0, 20));
    } catch (err: any) {
      setError(err.message || "Request failed");
      setResponse(null);
      setResponseStatus(null);
    } finally {
      setExecuting(false);
    }
  };

  const loadFromHistory = (entry: RequestHistory) => {
    setMethod(entry.method);
    setEndpoint(entry.endpoint);
    setResponse(entry.response);
    setResponseStatus(entry.status);
  };

  return (
    <div className="bg-gray-950 border border-gray-700 rounded-xl p-6 space-y-4 font-mono">
      <h2 className="text-lg font-bold text-gray-200">Dev Tools Console</h2>

      {/* Request Builder */}
      <div className="flex gap-2">
        <select
          value={method}
          onChange={(e) => setMethod(e.target.value as HttpMethod)}
          className={`bg-gray-800 border border-gray-700 text-sm rounded px-2 py-1.5 focus:outline-none ${METHOD_COLORS[method]}`}
        >
          {(["GET", "POST", "PUT", "DELETE"] as HttpMethod[]).map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
        <select
          value={endpoint}
          onChange={(e) => setEndpoint(e.target.value)}
          className="flex-1 bg-gray-800 border border-gray-700 text-gray-300 text-sm rounded px-2 py-1.5 focus:outline-none"
        >
          {COMMON_ENDPOINTS.map((ep) => <option key={ep} value={ep}>{ep}</option>)}
        </select>
        <button
          onClick={executeRequest}
          disabled={executing}
          className="px-4 py-1.5 bg-blue-700 hover:bg-blue-600 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm rounded transition-colors"
        >
          {executing ? "..." : "Send"}
        </button>
      </div>

      {/* Custom Endpoint */}
      <input
        type="text"
        value={endpoint}
        onChange={(e) => setEndpoint(e.target.value)}
        placeholder="/custom/endpoint"
        className="w-full bg-gray-900 border border-gray-700 text-gray-300 text-sm rounded px-3 py-1.5 focus:border-gray-500 focus:outline-none"
      />

      {/* Body (for POST/PUT) */}
      {(method === "POST" || method === "PUT") && (
        <div>
          <span className="text-xs text-gray-500 block mb-1">Request Body (JSON)</span>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            className="w-full h-20 bg-gray-900 border border-gray-700 text-gray-300 text-sm rounded p-2 focus:outline-none resize-y"
            spellCheck={false}
          />
        </div>
      )}

      {/* Response */}
      <div className="bg-black/60 border border-gray-800 rounded-lg overflow-hidden">
        <div className="flex items-center justify-between px-3 py-1.5 bg-gray-800 border-b border-gray-700">
          <span className="text-xs text-gray-400">Response</span>
          {responseStatus != null && (
            <span className={`text-xs font-bold ${responseStatus < 300 ? "text-green-400" : responseStatus < 500 ? "text-yellow-400" : "text-red-400"}`}>
              {responseStatus}
            </span>
          )}
        </div>
        <div className="p-3 max-h-48 overflow-auto">
          {error ? (
            <p className="text-red-400 text-sm">{error}</p>
          ) : response != null ? (
            <pre className="text-xs text-gray-300 whitespace-pre-wrap">{typeof response === "string" ? response : JSON.stringify(response, null, 2)}</pre>
          ) : (
            <p className="text-gray-600 text-xs">Send a request to see the response</p>
          )}
        </div>
      </div>

      {/* History */}
      {history.length > 0 && (
        <div>
          <h3 className="text-xs text-gray-500 mb-1">History</h3>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {history.map((h) => (
              <div
                key={h.id}
                onClick={() => loadFromHistory(h)}
                className="flex items-center gap-2 px-2 py-1 bg-gray-900 rounded cursor-pointer hover:bg-gray-800 text-[10px]"
              >
                <span className={`px-1 rounded ${METHOD_COLORS[h.method]}`}>{h.method}</span>
                <span className="text-gray-400 flex-1 truncate">{h.endpoint}</span>
                <span className={h.status < 300 ? "text-green-500" : "text-red-500"}>{h.status}</span>
                <span className="text-gray-600">{h.durationMs}ms</span>
                <span className="text-gray-600">{h.timestamp}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
