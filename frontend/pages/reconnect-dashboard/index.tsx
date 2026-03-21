
import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";

const ReconnectDashboard = () => {
  const [modules, setModules] = useState<Record<string, string[]>>({});

  useEffect(() => {
    fetch("/api/self-audit")
      .then((res) => res.json())
      .then((data) => setModules(data.disconnected_functions || []));
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">🧠 Bruce Reconnect Dashboard</h1>
      <p className="text-muted-foreground">
        Visual overview of all disconnected modules. Toggle to activate or inspect.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(modules).map(([file, funcs]) => (
          <Card key={file} className="shadow-lg border border-muted">
            <CardContent className="space-y-2 py-4">
              <h2 className="text-lg font-semibold">{file}</h2>
              <ul className="space-y-1">
                {funcs.map((func) => (
                  <li key={func} className="flex justify-between items-center">
                    <span className="text-sm">{func}</span>
                    <div className="flex items-center space-x-2">
                      <Label htmlFor={func}>Enable</Label>
                      <Switch id={func} />
                    </div>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default ReconnectDashboard;
