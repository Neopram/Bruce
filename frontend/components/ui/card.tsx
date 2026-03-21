import React from "react";

/**
 * 🧠 Card - High-performance container component.
 * Designed for encapsulating content in a clean, modular, and responsive layout.
 * Ideal for dashboards, cognitive modules, and dynamic panels.
 */
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

/**
 * 🧠 CardContent - Internal wrapper for structured layout inside Card.
 * Provides spacing, visual balance, and text normalization.
 */
interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = "",
  ...props
}) => {
  return (
    <div
      className={`rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm hover:shadow-md transition-shadow duration-300 ease-in-out p-6 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardContent: React.FC<CardContentProps> = ({
  children,
  className = "",
  ...props
}) => {
  return (
    <div
      className={`text-zinc-800 dark:text-zinc-200 text-sm leading-relaxed tracking-wide ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
