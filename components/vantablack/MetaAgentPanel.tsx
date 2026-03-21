import React, { useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import Badge from "@/components/ui/badge";
import Progress from "@/components/ui/progress";

interface Agent {
  id: string;
  objective: string;
  status: "idle" | "running" | "completed" | "failed";
  progress: number;
  result?: string;
  createdAt: string;
}

export default function MetaAgentPanel() {
  const [objective, setObjective] = useState("");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createAgent = useCallback(async () => {
    if (!objective.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/vantablack/meta-agent?objective=${encodeURIComponent(objective)}`);
      if (!res.ok) throw new Error(`Failed (${res.status})`);
      const data = await res.json();
      const newAgent: Agent = {
        id: `agent-${Date.now()}`,
        objective,
        status: "running",
        progress: 0,
        result: data.msg,
        createdAt: new Date().toISOString(),
      };
      setAgents((prev) => [newAgent, ...prev]);
      setObjective("");

      // Simulate progress
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 25;
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
          setAgents((prev) =>
            prev.map((a) =>
              a.id === newAgent.id ? { ...a, status: "completed", progress: 100 } : a
            )
          );
        } else {
          setAgents((prev) =>
            prev.map((a) =>
              a.id === newAgent.id ? { ...a, progress: Math.min(progress, 99) } : a
            )
          );
        }
      }, 800);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [objective]);

  const removeAgent = (id: string) => {
    setAgents((prev) => prev.filter((a) => a.id !== id));
  };

  const statusVariant = (s: Agent["status"]) => {
    const map: Record<Agent["status"], "info" | "success" | "error" | "neutral"> = {
      idle: "neutral", running: "info", completed: "success", failed: "error",
    };
    return map[s];
  };

  return (
    <Card className="bg-gradient-to-br from-zinc-900 to-green-950/20 border-green-800/30">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">Meta-Agent Panel</h2>
          <Badge variant="info" size="sm">{agents.filter((a) => a.status === "running").length} active</Badge>
        </div>

        <div className="flex gap-2 mb-4">
          <input
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            placeholder="Define agent objective..."
            className="flex-1 px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-green-600"
            onKeyDown={(e) => e.key === "Enter" && createAgent()}
          />
          <button
            onClick={createAgent}
            disabled={loading || !objective.trim()}
            className="px-4 py-2 bg-green-700 hover:bg-green-600 rounded-lg text-sm text-white transition-colors disabled:opacity-50"
          >
            {loading ? "Creating..." : "Create Agent"}
          </button>
        </div>

        {error && (
          <div className="mb-4 p-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="space-y-3 max-h-[400px] overflow-y-auto">
          {agents.length === 0 ? (
            <p className="text-center text-zinc-500 py-6 text-sm">
              No agents created yet. Define an objective to spawn a meta-agent.
            </p>
          ) : (
            agents.map((agent) => (
              <div key={agent.id} className="bg-zinc-800/50 rounded-lg border border-zinc-700/50 p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-zinc-200 truncate">{agent.objective}</p>
                    <p className="text-xs text-zinc-500 mt-0.5">
                      {new Date(agent.createdAt).toLocaleTimeString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 ml-2">
                    <Badge variant={statusVariant(agent.status)} size="sm">{agent.status}</Badge>
                    <button
                      onClick={() => removeAgent(agent.id)}
                      className="text-zinc-500 hover:text-red-400 transition-colors text-xs"
                    >
                      Remove
                    </button>
                  </div>
                </div>
                <Progress
                  value={agent.progress}
                  variant={agent.status === "completed" ? "success" : agent.status === "failed" ? "error" : "info"}
                  size="sm"
                />
                {agent.result && (
                  <p className="mt-2 text-xs text-green-400 bg-green-900/20 rounded p-2">{agent.result}</p>
                )}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
