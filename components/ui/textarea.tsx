import React from "react";

/**
 * 🧠 TextareaProps – Propiedades extendidas para el componente Textarea.
 */
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;  // Etiqueta opcional
  error?: string;  // Mensaje de error opcional
  placeholder?: string;  // Texto de placeholder opcional
  rows?: number;  // Número de filas para el área de texto
  className?: string;  // Clase adicional para personalización
}

/**
 * 🧬 Textarea – Componente de área de texto reutilizable con soporte para etiquetas, mensajes de error y personalización.
 */
const Textarea: React.FC<TextareaProps> = ({
  label,
  error,
  className = "",
  rows = 4,
  ...props
}) => {
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
      <textarea
        className={`px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-zinc-800 dark:border-zinc-600 dark:text-zinc-200 ${
          error ? "border-red-500" : "border-zinc-300"
        }`}
        rows={rows}
        {...props}
      />
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
};

export { Textarea };
export default Textarea;
