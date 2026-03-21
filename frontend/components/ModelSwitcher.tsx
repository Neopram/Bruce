
import React, { useState } from "react";
import { Select, SelectItem } from "@/components/ui/select";
import { useSession } from "@/contexts/SessionContext";

export const ModelSwitcher = () => {
  const { model, setModel } = useSession();
  const models = ["deepseek", "phi3", "tinyllama"];

  return (
    <div className="flex flex-col space-y-1 text-sm">
      <label htmlFor="model">🧠 Model</label>
      <Select value={model} onValueChange={setModel} id="model">
        {models.map((m) => (
          <SelectItem key={m} value={m}>
            {m}
          </SelectItem>
        ))}
      </Select>
    </div>
  );
};
