import React, { useState, useCallback } from "react";

interface MindNode {
  id: string;
  label: string;
  domain: "trading" | "shipping" | "crypto" | "ai" | "risk" | "core";
  x: number;
  y: number;
  children?: MindNode[];
}

const DOMAIN_COLORS: Record<string, string> = {
  trading:  "#3b82f6",
  shipping: "#22c55e",
  crypto:   "#8b5cf6",
  ai:       "#06b6d4",
  risk:     "#ef4444",
  core:     "#f59e0b",
};

const INITIAL_NODES: MindNode[] = [
  {
    id: "trading", label: "Trading", domain: "trading", x: 200, y: 50,
    children: [
      { id: "t-algo", label: "Algo Strategies", domain: "trading", x: 320, y: 20 },
      { id: "t-risk", label: "Risk Mgmt", domain: "trading", x: 320, y: 80 },
    ],
  },
  {
    id: "shipping", label: "Shipping", domain: "shipping", x: 50, y: 150,
    children: [
      { id: "s-routes", label: "Route Optimization", domain: "shipping", x: -30, y: 120 },
      { id: "s-fleet", label: "Fleet Analytics", domain: "shipping", x: -30, y: 190 },
    ],
  },
  {
    id: "crypto", label: "Crypto", domain: "crypto", x: 200, y: 250,
    children: [
      { id: "c-defi", label: "DeFi", domain: "crypto", x: 320, y: 220 },
      { id: "c-tokens", label: "Token Creator", domain: "crypto", x: 320, y: 280 },
    ],
  },
  {
    id: "ai", label: "AI Engine", domain: "ai", x: 350, y: 150,
    children: [
      { id: "a-nlp", label: "NLP", domain: "ai", x: 450, y: 120 },
      { id: "a-rl", label: "RL Agent", domain: "ai", x: 450, y: 180 },
    ],
  },
  {
    id: "risk", label: "Risk", domain: "risk", x: 50, y: 50,
    children: [
      { id: "r-geo", label: "Geopolitical", domain: "risk", x: -30, y: 20 },
      { id: "r-stress", label: "Stress Testing", domain: "risk", x: -30, y: 80 },
    ],
  },
];

const CENTER = { x: 200, y: 150 };

const MindMap: React.FC = () => {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [hovered, setHovered] = useState<string | null>(null);

  const toggleExpand = useCallback((id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }, []);

  const renderNode = (node: MindNode, isChild = false) => {
    const color = DOMAIN_COLORS[node.domain] ?? "#9ca3af";
    const isHovered = hovered === node.id;
    const isExpanded = expanded.has(node.id);
    const r = isChild ? 6 : 10;

    return (
      <g key={node.id}>
        {/* Line to center for top-level */}
        {!isChild && (
          <line x1={CENTER.x} y1={CENTER.y} x2={node.x} y2={node.y}
            stroke={color} strokeWidth="1" opacity="0.4" strokeDasharray="4 2" />
        )}

        {/* Children lines + nodes */}
        {isExpanded && node.children?.map((child) => (
          <g key={child.id}>
            <line x1={node.x} y1={node.y} x2={child.x} y2={child.y}
              stroke={color} strokeWidth="0.8" opacity="0.5" />
            {renderNode(child, true)}
          </g>
        ))}

        {/* Node circle */}
        <circle cx={node.x} cy={node.y} r={isHovered ? r + 2 : r}
          fill={color} opacity={isHovered ? 1 : 0.8}
          stroke="white" strokeWidth={isHovered ? 1.5 : 0}
          className="cursor-pointer transition-all duration-200"
          onClick={() => !isChild && toggleExpand(node.id)}
          onMouseEnter={() => setHovered(node.id)}
          onMouseLeave={() => setHovered(null)} />

        {/* Label */}
        <text x={node.x} y={node.y + (isChild ? 14 : 20)}
          textAnchor="middle" fill="white" fontSize={isChild ? 8 : 10} fontWeight={isChild ? "normal" : "bold"}>
          {node.label}
        </text>

        {/* Expand indicator */}
        {!isChild && node.children && (
          <text x={node.x + r + 4} y={node.y + 3} fill={color} fontSize="10" className="cursor-pointer"
            onClick={() => toggleExpand(node.id)}>
            {isExpanded ? "\u2212" : "+"}
          </text>
        )}
      </g>
    );
  };

  return (
    <div className="bg-gray-900 text-white rounded-2xl shadow-lg p-6 space-y-4">
      <h2 className="text-xl font-bold">Cognitive Mind Map</h2>
      <p className="text-sm text-gray-400">Click nodes to expand domains</p>

      <div className="bg-gray-800 rounded-xl p-2 overflow-hidden">
        <svg viewBox="-60 -20 540 320" className="w-full h-auto" style={{ minHeight: 280 }}>
          {/* Central node */}
          <circle cx={CENTER.x} cy={CENTER.y} r="16" fill="#f59e0b" opacity="0.9" />
          <circle cx={CENTER.x} cy={CENTER.y} r="20" fill="none" stroke="#f59e0b" strokeWidth="1" opacity="0.3" className="animate-pulse" />
          <text x={CENTER.x} y={CENTER.y + 4} textAnchor="middle" fill="white" fontSize="9" fontWeight="bold">Bruce</text>

          {INITIAL_NODES.map((n) => renderNode(n))}
        </svg>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 justify-center">
        {Object.entries(DOMAIN_COLORS).map(([domain, color]) => (
          <div key={domain} className="flex items-center gap-1.5 text-xs">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            <span className="text-gray-400 capitalize">{domain}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MindMap;
