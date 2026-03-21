import React, { forwardRef } from "react";

/**
 * 🧠 InputProps – Propiedades extendidas para el componente Input.
 */
interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

/**
 * 🧬 Input – Componente de entrada reutilizable con soporte para etiquetas y mensajes de error.
 */
const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = "", ...props }, ref) => {
    return (
      <div className={`flex flex-col space-y-2 ${className}`}>
        {label && (
          <label
            htmlFor={props.id}
            className="text-sm font-medium text-zinc-700 dark:text-zinc-300"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-zinc-800 dark:border-zinc-600 dark:text-zinc-200 ${
            error ? "border-red-500" : "border-zinc-300"
          }`}
          {...props}
        />
        {error && <p className="text-sm text-red-500">{error}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";

export default Input;  // Exportación por defecto
