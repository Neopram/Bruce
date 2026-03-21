import React, { useState, useEffect } from "react";

interface MarketSession {
  name: string;
  region: string;
  timezone: string;
  openHour: number;
  closeHour: number;
  color: string;
  textColor: string;
}

const SESSIONS: MarketSession[] = [
  { name: "US", region: "New York", timezone: "America/New_York", openHour: 9, closeHour: 16, color: "bg-blue-600", textColor: "text-blue-300" },
  { name: "EU", region: "London", timezone: "Europe/London", openHour: 8, closeHour: 16, color: "bg-green-600", textColor: "text-green-300" },
  { name: "Asia", region: "Tokyo", timezone: "Asia/Tokyo", openHour: 9, closeHour: 15, color: "bg-red-600", textColor: "text-red-300" },
  { name: "Crypto", region: "24/7", timezone: "UTC", openHour: 0, closeHour: 24, color: "bg-purple-600", textColor: "text-purple-300" },
];

function getTimeInTimezone(tz: string): { hours: number; minutes: number; formatted: string } {
  try {
    const now = new Date();
    const str = now.toLocaleTimeString("en-US", { timeZone: tz, hour12: false, hour: "2-digit", minute: "2-digit" });
    const [h, m] = str.split(":").map(Number);
    return { hours: h, minutes: m, formatted: str };
  } catch {
    const now = new Date();
    return { hours: now.getUTCHours(), minutes: now.getUTCMinutes(), formatted: `${now.getUTCHours()}:${String(now.getUTCMinutes()).padStart(2, "0")}` };
  }
}

function isSessionOpen(session: MarketSession): boolean {
  if (session.openHour === 0 && session.closeHour === 24) return true;
  const { hours } = getTimeInTimezone(session.timezone);
  return hours >= session.openHour && hours < session.closeHour;
}

export default function TimeAwarenessIndicator() {
  const [, setTick] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 10000);
    return () => clearInterval(interval);
  }, []);

  const now = new Date();
  const utcTime = now.toLocaleTimeString("en-US", { timeZone: "UTC", hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const activeSessions = SESSIONS.filter(isSessionOpen);

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-gray-300">Market Sessions</h3>
        <span className="text-xs font-mono text-gray-500">UTC {utcTime}</span>
      </div>

      {/* Active Session Indicator */}
      <div className="flex gap-1.5">
        {SESSIONS.map((session) => {
          const open = isSessionOpen(session);
          return (
            <div
              key={session.name}
              className={`flex-1 rounded-lg p-2 border transition-all ${
                open ? `${session.color}/20 border-${session.color.replace("bg-", "")} ring-1 ring-${session.color.replace("bg-", "")}/30` : "bg-gray-800 border-gray-700"
              }`}
            >
              <div className="flex items-center gap-1 mb-0.5">
                <span className={`w-1.5 h-1.5 rounded-full ${open ? session.color + " animate-pulse" : "bg-gray-600"}`} />
                <span className={`text-xs font-bold ${open ? session.textColor : "text-gray-500"}`}>{session.name}</span>
              </div>
              <span className="text-[10px] text-gray-500">{session.region}</span>
              <div className="text-[10px] font-mono text-gray-400 mt-0.5">
                {getTimeInTimezone(session.timezone).formatted}
              </div>
            </div>
          );
        })}
      </div>

      {/* Status */}
      <div className="flex items-center justify-between text-[10px]">
        <span className="text-gray-500">
          {activeSessions.length} session(s) active
        </span>
        <div className="flex gap-1">
          {activeSessions.map((s) => (
            <span key={s.name} className={`px-1.5 py-0.5 rounded ${s.color}/30 ${s.textColor}`}>{s.name}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
