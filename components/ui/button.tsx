import React from "react";
import clsx from "clsx";

/**
 * 🧠 ButtonProps – Extendido para IA interactiva
 */
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "primary" | "secondary" | "destructive" | "ghost" | "outline";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  children: React.ReactNode;
  icon?: React.ReactNode;
}

/**
 * 🧬 Button – Ultra modular component for Bruce's command interface
 */
const Button: React.FC<ButtonProps> = ({
  variant = "primary",
  size = "md",
  isLoading = false,
  children,
  icon,
  className,
  ...props
}) => {
  const baseStyles =
    "inline-flex items-center justify-center font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl";

  const variantStyles: Record<string, string> = {
    default: "bg-zinc-100 text-zinc-800 hover:bg-zinc-200",
    primary: "bg-indigo-600 text-white hover:bg-indigo-700",
    secondary: "bg-zinc-800 text-white hover:bg-zinc-700",
    destructive: "bg-red-600 text-white hover:bg-red-700",
    ghost: "bg-transparent text-zinc-600 hover:bg-zinc-100",
    outline: "border border-zinc-600 text-zinc-300 bg-transparent hover:bg-zinc-800",
  };

  const sizeStyles: Record<string, string> = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-base",
    lg: "px-6 py-3 text-lg",
  };

  return (
    <button
      className={clsx(
        baseStyles,
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading ? (
        <svg
          className="animate-spin h-5 w-5 text-white"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v4l4-4-4-4v4a8 8 0 100 16 8 8 0 01-8-8z"
          />
        </svg>
      ) : (
        <>
          {icon && <span className="mr-2">{icon}</span>}
          {children}
        </>
      )}
    </button>
  );
};

// Exportación predeterminada del componente Button
export { Button };
export default Button;
