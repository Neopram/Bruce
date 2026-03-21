import React, { useState } from "react";

interface SwitchProps {
  id?: string;
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
}

export function Switch({ id, checked, onCheckedChange }: SwitchProps) {
  const [internalChecked, setInternalChecked] = useState(false);
  const isChecked = checked !== undefined ? checked : internalChecked;

  const toggle = () => {
    const next = !isChecked;
    setInternalChecked(next);
    onCheckedChange?.(next);
  };

  return (
    <button
      id={id}
      role="switch"
      aria-checked={isChecked}
      onClick={toggle}
      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
        isChecked ? "bg-indigo-600" : "bg-zinc-300 dark:bg-zinc-600"
      }`}
    >
      <span
        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
          isChecked ? "translate-x-4" : "translate-x-0.5"
        }`}
      />
    </button>
  );
}
