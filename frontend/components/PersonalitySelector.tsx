
import React from "react";
import { Select, SelectItem } from "@/components/ui/select";
import { useSession } from "@/contexts/SessionContext";

export const PersonalitySelector = () => {
  const { personality, setPersonality } = useSession();
  const profiles = ["default", "curious", "genius", "healer", "tactical", "brutal", "zen"];

  return (
    <div className="flex flex-col space-y-1 text-sm">
      <label htmlFor="personality">🧬 Personality</label>
      <Select value={personality} onValueChange={setPersonality} id="personality">
        {profiles.map((p) => (
          <SelectItem key={p} value={p}>
            {p}
          </SelectItem>
        ))}
      </Select>
    </div>
  );
};
