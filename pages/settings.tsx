import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import Input from "@/components/ui/input";
import Tabs from "@/components/ui/tabs";
import Badge from "@/components/ui/badge";
import Button from "@/components/ui/button";
import Dropdown from "@/components/ui/dropdown";
import { useAuth } from "@/contexts/AuthContext";

const SettingsPage = () => {
  const { isAuthenticated } = useAuth();

  // Profile settings
  const [displayName, setDisplayName] = useState("Bruce Admin");
  const [email, setEmail] = useState("admin@bruceai.io");
  const [timezone, setTimezone] = useState("America/New_York");

  // Personality config
  const [personality, setPersonality] = useState("Guardian");
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [narrativeStyle, setNarrativeStyle] = useState("strategic");
  const [riskTolerance, setRiskTolerance] = useState("moderate");

  // API Keys
  const [apiKeys, setApiKeys] = useState([
    { id: "1", name: "Binance", provider: "binance", maskedKey: "sk-****...7f3a", isActive: true, createdAt: "2025-12-01" },
    { id: "2", name: "OpenAI", provider: "openai", maskedKey: "sk-****...9b2c", isActive: true, createdAt: "2025-11-15" },
    { id: "3", name: "CoinGecko", provider: "coingecko", maskedKey: "cg-****...4d1e", isActive: false, createdAt: "2025-10-20" },
  ]);

  // Notifications
  const [notifyEmail, setNotifyEmail] = useState(true);
  const [notifyPush, setNotifyPush] = useState(true);
  const [notifyTrading, setNotifyTrading] = useState(true);
  const [notifySystem, setNotifySystem] = useState(false);

  const [saving, setSaving] = useState(false);

  const handleSave = () => {
    setSaving(true);
    setTimeout(() => setSaving(false), 1500);
  };

  const Toggle: React.FC<{ checked: boolean; onChange: (v: boolean) => void; label: string }> = ({
    checked, onChange, label,
  }) => (
    <label className="flex items-center justify-between py-2">
      <span className="text-sm text-zinc-300">{label}</span>
      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={`relative w-11 h-6 rounded-full transition-colors ${
          checked ? "bg-indigo-600" : "bg-zinc-700"
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
            checked ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </button>
    </label>
  );

  return (
    <div className="p-6 space-y-6 bg-zinc-950 min-h-screen text-white">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Settings</h1>
        <Button variant="primary" onClick={handleSave} isLoading={saving}>
          Save Changes
        </Button>
      </div>

      <Tabs
        variant="pills"
        tabs={[
          {
            label: "Profile",
            content: (
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-6 space-y-4 max-w-lg">
                  <h2 className="text-lg font-semibold mb-2">Profile Settings</h2>
                  <Input
                    label="Display Name"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                  />
                  <Input
                    label="Email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                  <Dropdown
                    label="Timezone"
                    options={[
                      { value: "America/New_York", label: "Eastern (ET)" },
                      { value: "America/Chicago", label: "Central (CT)" },
                      { value: "America/Denver", label: "Mountain (MT)" },
                      { value: "America/Los_Angeles", label: "Pacific (PT)" },
                      { value: "Europe/London", label: "London (GMT)" },
                      { value: "Europe/Berlin", label: "Berlin (CET)" },
                      { value: "Asia/Tokyo", label: "Tokyo (JST)" },
                      { value: "Asia/Shanghai", label: "Shanghai (CST)" },
                    ]}
                    value={timezone}
                    onChange={setTimezone}
                    searchable
                  />
                  <Dropdown
                    label="Theme"
                    options={[
                      { value: "dark", label: "Dark Mode" },
                      { value: "light", label: "Light Mode" },
                      { value: "system", label: "System Default" },
                    ]}
                    value="dark"
                    onChange={() => {}}
                  />
                </CardContent>
              </Card>
            ),
          },
          {
            label: "Personality",
            content: (
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-6 space-y-4 max-w-lg">
                  <h2 className="text-lg font-semibold mb-2">AI Personality Config</h2>
                  <Dropdown
                    label="Personality Mode"
                    options={[
                      { value: "Default", label: "Default" },
                      { value: "Guardian", label: "Guardian" },
                      { value: "Shadow", label: "Shadow" },
                      { value: "Genius", label: "Genius" },
                      { value: "Healer", label: "Healer" },
                      { value: "Strategist", label: "Strategist" },
                      { value: "Silent", label: "Silent" },
                      { value: "DoomAI", label: "DoomAI" },
                    ]}
                    value={personality}
                    onChange={setPersonality}
                  />
                  <Toggle checked={voiceEnabled} onChange={setVoiceEnabled} label="Voice Narration" />
                  <Dropdown
                    label="Narrative Style"
                    options={[
                      { value: "strategic", label: "Strategic" },
                      { value: "poetic", label: "Poetic" },
                      { value: "analytical", label: "Analytical" },
                      { value: "casual", label: "Casual" },
                      { value: "dramatic", label: "Dramatic" },
                    ]}
                    value={narrativeStyle}
                    onChange={setNarrativeStyle}
                  />
                  <Dropdown
                    label="Risk Tolerance"
                    options={[
                      { value: "conservative", label: "Conservative" },
                      { value: "moderate", label: "Moderate" },
                      { value: "aggressive", label: "Aggressive" },
                    ]}
                    value={riskTolerance}
                    onChange={setRiskTolerance}
                  />
                </CardContent>
              </Card>
            ),
          },
          {
            label: "API Keys",
            content: (
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold">API Keys Management</h2>
                    <Button variant="secondary" size="sm">
                      + Add Key
                    </Button>
                  </div>
                  <div className="space-y-3">
                    {apiKeys.map((key) => (
                      <div
                        key={key.id}
                        className="flex items-center justify-between p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50"
                      >
                        <div className="flex items-center gap-4">
                          <div>
                            <p className="font-medium">{key.name}</p>
                            <p className="text-sm text-zinc-400">{key.provider}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <code className="text-sm font-mono text-zinc-400 bg-zinc-800 px-2 py-1 rounded">
                            {key.maskedKey}
                          </code>
                          <Badge variant={key.isActive ? "success" : "neutral"} size="sm">
                            {key.isActive ? "Active" : "Inactive"}
                          </Badge>
                          <button className="text-zinc-400 hover:text-red-400 transition-colors text-sm">
                            Revoke
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-zinc-500 mt-4">
                    API keys are encrypted and stored securely. Only masked values are displayed.
                  </p>
                </CardContent>
              </Card>
            ),
          },
          {
            label: "Notifications",
            content: (
              <Card className="bg-zinc-900 border-zinc-800">
                <CardContent className="p-6 max-w-lg">
                  <h2 className="text-lg font-semibold mb-4">Notification Preferences</h2>
                  <div className="space-y-1 divide-y divide-zinc-800">
                    <Toggle checked={notifyEmail} onChange={setNotifyEmail} label="Email Notifications" />
                    <Toggle checked={notifyPush} onChange={setNotifyPush} label="Push Notifications" />
                    <Toggle checked={notifyTrading} onChange={setNotifyTrading} label="Trading Alerts" />
                    <Toggle checked={notifySystem} onChange={setNotifySystem} label="System Updates" />
                  </div>
                  <div className="mt-6 p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50">
                    <h3 className="text-sm font-medium mb-2">Alert Thresholds</h3>
                    <div className="space-y-3">
                      <Input label="Price Change Alert (%)" type="number" defaultValue="5" />
                      <Input label="PnL Alert ($)" type="number" defaultValue="1000" />
                      <Input label="Drawdown Alert (%)" type="number" defaultValue="10" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ),
          },
        ]}
      />
    </div>
  );
};

export default SettingsPage;
