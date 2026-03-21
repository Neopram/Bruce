import React from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";

type ChartType = "line" | "bar" | "pie" | "area";

interface ChartConfig {
  dataKeys: string[];
  xAxisKey?: string;
  colors?: string[];
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  height?: number;
  strokeWidth?: number;
  fillOpacity?: number;
  innerRadius?: number;
  outerRadius?: number;
}

interface ChartWrapperProps {
  data: any[];
  type: ChartType;
  config?: ChartConfig;
  title?: string;
  className?: string;
}

const DEFAULT_COLORS = [
  "#6366f1",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#ec4899",
  "#84cc16",
];

const commonAxisProps = {
  tick: { fill: "#9ca3af", fontSize: 12 },
  axisLine: { stroke: "#374151" },
  tickLine: { stroke: "#374151" },
};

const ChartWrapper: React.FC<ChartWrapperProps> = ({
  data,
  type,
  config = {},
  title,
  className,
}) => {
  const {
    dataKeys = [],
    xAxisKey = "name",
    colors = DEFAULT_COLORS,
    showGrid = true,
    showLegend = true,
    showTooltip = true,
    height = 300,
    strokeWidth = 2,
    fillOpacity = 0.3,
    innerRadius = 0,
    outerRadius = 80,
  } = config;

  const tooltipStyle = {
    contentStyle: {
      backgroundColor: "#18181b",
      border: "1px solid #3f3f46",
      borderRadius: "8px",
      color: "#e4e4e7",
      fontSize: "12px",
    },
  };

  const renderChart = () => {
    switch (type) {
      case "line":
        return (
          <LineChart data={data}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />}
            <XAxis dataKey={xAxisKey} {...commonAxisProps} />
            <YAxis {...commonAxisProps} />
            {showTooltip && <Tooltip {...tooltipStyle} />}
            {showLegend && <Legend />}
            {dataKeys.map((key, i) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[i % colors.length]}
                strokeWidth={strokeWidth}
                dot={{ r: 3, fill: colors[i % colors.length] }}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        );

      case "area":
        return (
          <AreaChart data={data}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />}
            <XAxis dataKey={xAxisKey} {...commonAxisProps} />
            <YAxis {...commonAxisProps} />
            {showTooltip && <Tooltip {...tooltipStyle} />}
            {showLegend && <Legend />}
            {dataKeys.map((key, i) => (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colors[i % colors.length]}
                fill={colors[i % colors.length]}
                fillOpacity={fillOpacity}
                strokeWidth={strokeWidth}
              />
            ))}
          </AreaChart>
        );

      case "bar":
        return (
          <BarChart data={data}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />}
            <XAxis dataKey={xAxisKey} {...commonAxisProps} />
            <YAxis {...commonAxisProps} />
            {showTooltip && <Tooltip {...tooltipStyle} />}
            {showLegend && <Legend />}
            {dataKeys.map((key, i) => (
              <Bar
                key={key}
                dataKey={key}
                fill={colors[i % colors.length]}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        );

      case "pie":
        return (
          <PieChart>
            {showTooltip && <Tooltip {...tooltipStyle} />}
            {showLegend && <Legend />}
            <Pie
              data={data}
              dataKey={dataKeys[0] || "value"}
              nameKey={xAxisKey}
              cx="50%"
              cy="50%"
              innerRadius={innerRadius}
              outerRadius={outerRadius}
              paddingAngle={2}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={colors[i % colors.length]} />
              ))}
            </Pie>
          </PieChart>
        );

      default:
        return <p className="text-zinc-400">Unsupported chart type</p>;
    }
  };

  return (
    <div className={className}>
      {title && (
        <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300 mb-3">
          {title}
        </h3>
      )}
      <ResponsiveContainer width="100%" height={height}>
        {renderChart()}
      </ResponsiveContainer>
    </div>
  );
};

export default ChartWrapper;
