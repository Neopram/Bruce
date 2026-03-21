import React, { useState, useMemo } from "react";
import clsx from "clsx";

export interface Column<T = any> {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (value: any, row: T, index: number) => React.ReactNode;
  width?: string;
  align?: "left" | "center" | "right";
}

interface TableProps<T = any> {
  columns: Column<T>[];
  data: T[];
  sortable?: boolean;
  onSort?: (key: string, direction: "asc" | "desc") => void;
  emptyMessage?: string;
  className?: string;
  compact?: boolean;
  striped?: boolean;
  hoverable?: boolean;
}

type SortDirection = "asc" | "desc";

const Table = <T extends Record<string, any>>({
  columns,
  data,
  sortable = false,
  onSort,
  emptyMessage = "No data available",
  className,
  compact = false,
  striped = true,
  hoverable = true,
}: TableProps<T>) => {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDirection>("asc");

  const handleSort = (key: string) => {
    if (!sortable) return;
    const col = columns.find((c) => c.key === key);
    if (col && col.sortable === false) return;

    const newDir = sortKey === key && sortDir === "asc" ? "desc" : "asc";
    setSortKey(key);
    setSortDir(newDir);
    onSort?.(key, newDir);
  };

  const sortedData = useMemo(() => {
    if (!sortKey || onSort) return data;
    return [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      if (typeof aVal === "number" && typeof bVal === "number") {
        return sortDir === "asc" ? aVal - bVal : bVal - aVal;
      }
      const cmp = String(aVal).localeCompare(String(bVal));
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [data, sortKey, sortDir, onSort]);

  const SortIcon = ({ active, direction }: { active: boolean; direction: SortDirection }) => (
    <span className={clsx("ml-1 inline-block", active ? "text-indigo-400" : "text-zinc-500")}>
      {active ? (direction === "asc" ? "\u25B2" : "\u25BC") : "\u25B4"}
    </span>
  );

  if (data.length === 0) {
    return (
      <div className={clsx("rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900", className)}>
        <div className="flex flex-col items-center justify-center py-12 text-zinc-400 dark:text-zinc-500">
          <svg className="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <p className="text-sm">{emptyMessage}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx("overflow-x-auto rounded-xl border border-zinc-200 dark:border-zinc-700", className)}>
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-zinc-50 dark:bg-zinc-800 border-b border-zinc-200 dark:border-zinc-700">
            {columns.map((col) => (
              <th
                key={col.key}
                className={clsx(
                  "font-semibold text-zinc-600 dark:text-zinc-300 select-none",
                  compact ? "px-3 py-2" : "px-4 py-3",
                  col.align === "center" && "text-center",
                  col.align === "right" && "text-right",
                  sortable && col.sortable !== false && "cursor-pointer hover:text-indigo-500"
                )}
                style={col.width ? { width: col.width } : undefined}
                onClick={() => handleSort(col.key)}
              >
                <span className="inline-flex items-center">
                  {col.label}
                  {sortable && col.sortable !== false && (
                    <SortIcon active={sortKey === col.key} direction={sortDir} />
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row, rowIdx) => (
            <tr
              key={rowIdx}
              className={clsx(
                "border-b border-zinc-100 dark:border-zinc-800 transition-colors",
                striped && rowIdx % 2 === 1 && "bg-zinc-50/50 dark:bg-zinc-800/30",
                hoverable && "hover:bg-indigo-50/50 dark:hover:bg-zinc-800/60"
              )}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={clsx(
                    "text-zinc-800 dark:text-zinc-200",
                    compact ? "px-3 py-1.5" : "px-4 py-3",
                    col.align === "center" && "text-center",
                    col.align === "right" && "text-right"
                  )}
                >
                  {col.render
                    ? col.render(row[col.key], row, rowIdx)
                    : row[col.key] ?? "-"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Table;
