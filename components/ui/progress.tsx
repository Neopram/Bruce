import React from "react";
import clsx from "clsx";

type ProgressVariant = "default" | "success" | "warning" | "error" | "info";
type ProgressSize = "sm" | "md" | "lg";

interface ProgressProps {
  value: number;
  variant?: ProgressVariant;
  size?: ProgressSize;
  label?: string;
  showValue?: boolean;
  animated?: boolean;
  striped?: boolean;
  className?: string;
}

const variantColors: Record<ProgressVariant, string> = {
  default: "bg-indigo-600",
  success: "bg-emerald-500",
  warning: "bg-amber-500",
  error: "bg-red-500",
  info: "bg-blue-500",
};

const trackColors: Record<ProgressVariant, string> = {
  default: "bg-indigo-100 dark:bg-indigo-900/30",
  success: "bg-emerald-100 dark:bg-emerald-900/30",
  warning: "bg-amber-100 dark:bg-amber-900/30",
  error: "bg-red-100 dark:bg-red-900/30",
  info: "bg-blue-100 dark:bg-blue-900/30",
};

const sizeHeights: Record<ProgressSize, string> = {
  sm: "h-1.5",
  md: "h-2.5",
  lg: "h-4",
};

const Progress: React.FC<ProgressProps> = ({
  value,
  variant = "default",
  size = "md",
  label,
  showValue = false,
  animated = true,
  striped = false,
  className,
}) => {
  const clampedValue = Math.min(100, Math.max(0, value));

  return (
    <div className={clsx("w-full", className)}>
      {(label || showValue) && (
        <div className="flex items-center justify-between mb-1.5">
          {label && (
            <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              {label}
            </span>
          )}
          {showValue && (
            <span className="text-sm font-mono text-zinc-500 dark:text-zinc-400">
              {Math.round(clampedValue)}%
            </span>
          )}
        </div>
      )}
      <div
        className={clsx(
          "w-full rounded-full overflow-hidden",
          trackColors[variant],
          sizeHeights[size]
        )}
        role="progressbar"
        aria-valuenow={clampedValue}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={clsx(
            "h-full rounded-full transition-all duration-500 ease-out",
            variantColors[variant],
            animated && "transition-[width]",
            striped &&
              "bg-gradient-to-r from-transparent via-white/20 to-transparent bg-[length:20px_100%] animate-[progress-stripe_1s_linear_infinite]"
          )}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
    </div>
  );
};

export default Progress;
