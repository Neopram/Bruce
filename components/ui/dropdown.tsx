import React, { useState, useRef, useEffect, useCallback, useMemo } from "react";
import clsx from "clsx";

export interface DropdownOption {
  value: string;
  label: string;
  disabled?: boolean;
  icon?: React.ReactNode;
}

interface DropdownProps {
  options: DropdownOption[];
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  searchable?: boolean;
  disabled?: boolean;
  className?: string;
  label?: string;
  error?: string;
}

const Dropdown: React.FC<DropdownProps> = ({
  options,
  value,
  onChange,
  placeholder = "Select an option...",
  searchable = false,
  disabled = false,
  className,
  label,
  error,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLInputElement>(null);

  const selectedOption = options.find((o) => o.value === value);

  const filtered = useMemo(() => {
    if (!search) return options;
    const lower = search.toLowerCase();
    return options.filter((o) => o.label.toLowerCase().includes(lower));
  }, [options, search]);

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setSearch("");
      }
    };
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, []);

  useEffect(() => {
    if (isOpen && searchable && searchRef.current) {
      searchRef.current.focus();
    }
  }, [isOpen, searchable]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isOpen) {
        if (e.key === "Enter" || e.key === " " || e.key === "ArrowDown") {
          e.preventDefault();
          setIsOpen(true);
        }
        return;
      }

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setHighlightIndex((prev) => Math.min(prev + 1, filtered.length - 1));
          break;
        case "ArrowUp":
          e.preventDefault();
          setHighlightIndex((prev) => Math.max(prev - 1, 0));
          break;
        case "Enter":
          e.preventDefault();
          if (highlightIndex >= 0 && filtered[highlightIndex] && !filtered[highlightIndex].disabled) {
            onChange(filtered[highlightIndex].value);
            setIsOpen(false);
            setSearch("");
          }
          break;
        case "Escape":
          setIsOpen(false);
          setSearch("");
          break;
      }
    },
    [isOpen, highlightIndex, filtered, onChange]
  );

  const handleSelect = (opt: DropdownOption) => {
    if (opt.disabled) return;
    onChange(opt.value);
    setIsOpen(false);
    setSearch("");
  };

  return (
    <div className={clsx("flex flex-col space-y-1", className)} ref={containerRef}>
      {label && (
        <label className="text-sm font-medium text-zinc-700 dark:text-zinc-300">{label}</label>
      )}
      <div className="relative" onKeyDown={handleKeyDown}>
        <button
          type="button"
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled}
          className={clsx(
            "w-full flex items-center justify-between px-4 py-2 rounded-lg border text-sm transition-colors",
            "bg-white dark:bg-zinc-800 text-zinc-800 dark:text-zinc-200",
            error ? "border-red-500" : "border-zinc-300 dark:border-zinc-600",
            disabled ? "opacity-50 cursor-not-allowed" : "hover:border-indigo-400 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          )}
        >
          <span className={clsx(!selectedOption && "text-zinc-400")}>
            {selectedOption ? (
              <span className="flex items-center gap-2">
                {selectedOption.icon}
                {selectedOption.label}
              </span>
            ) : (
              placeholder
            )}
          </span>
          <svg
            className={clsx("w-4 h-4 text-zinc-400 transition-transform", isOpen && "rotate-180")}
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {isOpen && (
          <div className="absolute z-50 w-full mt-1 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg shadow-xl max-h-60 overflow-hidden">
            {searchable && (
              <div className="px-3 py-2 border-b border-zinc-200 dark:border-zinc-700">
                <input
                  ref={searchRef}
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value);
                    setHighlightIndex(0);
                  }}
                  placeholder="Search..."
                  className="w-full px-2 py-1 text-sm bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:text-zinc-200"
                />
              </div>
            )}
            <ul className="overflow-y-auto max-h-48" role="listbox">
              {filtered.length === 0 ? (
                <li className="px-4 py-3 text-sm text-zinc-400 text-center">No options found</li>
              ) : (
                filtered.map((opt, idx) => (
                  <li
                    key={opt.value}
                    role="option"
                    aria-selected={opt.value === value}
                    onClick={() => handleSelect(opt)}
                    className={clsx(
                      "px-4 py-2 text-sm cursor-pointer transition-colors flex items-center gap-2",
                      opt.disabled && "opacity-40 cursor-not-allowed",
                      idx === highlightIndex && "bg-indigo-50 dark:bg-indigo-900/30",
                      opt.value === value && "text-indigo-600 dark:text-indigo-400 font-medium",
                      !opt.disabled && "hover:bg-zinc-50 dark:hover:bg-zinc-700"
                    )}
                  >
                    {opt.icon}
                    {opt.label}
                    {opt.value === value && (
                      <svg className="w-4 h-4 ml-auto text-indigo-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </li>
                ))
              )}
            </ul>
          </div>
        )}
      </div>
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
};

export default Dropdown;
