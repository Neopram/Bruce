import React, { useState } from "react";
import clsx from "clsx";

export interface TabItem {
  label: string;
  content: React.ReactNode;
  icon?: React.ReactNode;
  disabled?: boolean;
}

interface TabsProps {
  tabs: TabItem[];
  defaultTab?: number;
  onChange?: (index: number) => void;
  variant?: "default" | "pills" | "underline";
  className?: string;
}

const Tabs: React.FC<TabsProps> = ({
  tabs,
  defaultTab = 0,
  onChange,
  variant = "default",
  className,
}) => {
  const [activeTab, setActiveTab] = useState(defaultTab);

  const handleTabClick = (index: number) => {
    if (tabs[index]?.disabled) return;
    setActiveTab(index);
    onChange?.(index);
  };

  const tabBaseStyles = "px-4 py-2 text-sm font-medium transition-all duration-200 flex items-center gap-2 whitespace-nowrap";

  const getTabStyle = (index: number) => {
    const isActive = index === activeTab;
    const isDisabled = tabs[index]?.disabled;

    if (isDisabled) {
      return "text-zinc-400 dark:text-zinc-600 cursor-not-allowed";
    }

    switch (variant) {
      case "pills":
        return isActive
          ? "bg-indigo-600 text-white rounded-lg shadow-sm"
          : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg";
      case "underline":
        return isActive
          ? "text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400"
          : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-300 border-b-2 border-transparent";
      default:
        return isActive
          ? "bg-white dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-t-lg border border-b-0 border-zinc-200 dark:border-zinc-700"
          : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-300";
    }
  };

  return (
    <div className={clsx("w-full", className)}>
      <div
        className={clsx(
          "flex",
          variant === "default" && "border-b border-zinc-200 dark:border-zinc-700",
          variant === "pills" && "bg-zinc-100 dark:bg-zinc-800/50 rounded-lg p-1 gap-1",
          variant === "underline" && "border-b border-zinc-200 dark:border-zinc-700 gap-4"
        )}
        role="tablist"
      >
        {tabs.map((tab, index) => (
          <button
            key={index}
            role="tab"
            aria-selected={index === activeTab}
            onClick={() => handleTabClick(index)}
            className={clsx(tabBaseStyles, getTabStyle(index))}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>
      <div className="mt-4" role="tabpanel">
        {tabs[activeTab]?.content}
      </div>
    </div>
  );
};

export default Tabs;
