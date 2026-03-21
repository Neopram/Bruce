import React, { createContext, useContext, useState } from "react";

interface SessionContextType {
  model: string;
  setModel: (model: string) => void;
  personality: string;
  setPersonality: (personality: string) => void;
}

const SessionContext = createContext<SessionContextType>({
  model: "deepseek",
  setModel: () => {},
  personality: "default",
  setPersonality: () => {},
});

export const SessionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [model, setModel] = useState("deepseek");
  const [personality, setPersonality] = useState("default");

  return (
    <SessionContext.Provider value={{ model, setModel, personality, setPersonality }}>
      {children}
    </SessionContext.Provider>
  );
};

export const useSession = () => useContext(SessionContext);
