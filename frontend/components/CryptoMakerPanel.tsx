import React, { useState } from "react";
import axios from "axios";

interface TokenForm {
  name: string;
  symbol: string;
  totalSupply: string;
  decimals: string;
  chain: string;
}

const CHAINS = ["Ethereum", "BSC", "Polygon", "Solana", "Avalanche", "Base"];
const STEPS = ["Details", "Configuration", "Preview", "Create"];

const CryptoMakerPanel: React.FC = () => {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<TokenForm>({
    name: "", symbol: "", totalSupply: "1000000", decimals: "18", chain: "Ethereum",
  });
  const [gasEstimate, setGasEstimate] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const updateField = (field: keyof TokenForm, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const estimateGas = async () => {
    try {
      const res = await axios.post("/api/create-token/estimate", {
        chain: form.chain,
        totalSupply: form.totalSupply,
      });
      setGasEstimate(res.data?.estimate || "~0.005 ETH");
    } catch {
      setGasEstimate("Unable to estimate");
    }
  };

  const handleNext = () => {
    if (step === 1) estimateGas();
    if (step < STEPS.length - 1) setStep(step + 1);
  };

  const handleBack = () => {
    if (step > 0) setStep(step - 1);
  };

  const handleCreate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post("/api/create-token", {
        name: form.name,
        symbol: form.symbol,
        totalSupply: parseInt(form.totalSupply),
        decimals: parseInt(form.decimals),
        chain: form.chain,
      });
      setResult(res.data);
    } catch (err: any) {
      setError(err?.response?.data?.error || "Token creation failed");
    } finally {
      setLoading(false);
    }
  };

  const isStep1Valid = form.name.trim() && form.symbol.trim();
  const isStep2Valid = parseInt(form.totalSupply) > 0 && parseInt(form.decimals) >= 0;

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Token Name</label>
              <input value={form.name} onChange={(e) => updateField("name", e.target.value)}
                placeholder="e.g. My Token" className="w-full bg-gray-700 text-white text-sm rounded px-3 py-2 border border-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500" />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Symbol</label>
              <input value={form.symbol} onChange={(e) => updateField("symbol", e.target.value.toUpperCase())}
                placeholder="e.g. MTK" maxLength={10} className="w-full bg-gray-700 text-white text-sm rounded px-3 py-2 border border-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500" />
            </div>
          </div>
        );
      case 1:
        return (
          <div className="space-y-3">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Total Supply</label>
              <input type="number" value={form.totalSupply} onChange={(e) => updateField("totalSupply", e.target.value)}
                className="w-full bg-gray-700 text-white text-sm rounded px-3 py-2 border border-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500" />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Decimals</label>
              <input type="number" min="0" max="18" value={form.decimals} onChange={(e) => updateField("decimals", e.target.value)}
                className="w-full bg-gray-700 text-white text-sm rounded px-3 py-2 border border-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500" />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Chain</label>
              <select value={form.chain} onChange={(e) => updateField("chain", e.target.value)}
                className="w-full bg-gray-700 text-white text-sm rounded px-3 py-2 border border-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500">
                {CHAINS.map((c) => <option key={c}>{c}</option>)}
              </select>
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-3">
            <h4 className="text-sm font-medium text-gray-300">Token Preview</h4>
            <div className="bg-gray-800 rounded-lg p-4 space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-gray-400">Name:</span><span className="font-medium">{form.name || "-"}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Symbol:</span><span className="font-medium">{form.symbol || "-"}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Supply:</span><span className="font-mono">{parseInt(form.totalSupply).toLocaleString()}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Decimals:</span><span className="font-mono">{form.decimals}</span></div>
              <div className="flex justify-between"><span className="text-gray-400">Chain:</span><span>{form.chain}</span></div>
              <div className="flex justify-between border-t border-gray-700 pt-2 mt-2">
                <span className="text-gray-400">Est. Gas:</span>
                <span className="text-yellow-400 font-mono">{gasEstimate || "Calculating..."}</span>
              </div>
            </div>
          </div>
        );
      case 3:
        if (result) {
          return (
            <div className="text-center space-y-3 py-4">
              <div className="w-12 h-12 rounded-full bg-green-600 mx-auto flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
              </div>
              <p className="text-green-400 font-semibold">Token Created Successfully!</p>
              {result.address && <p className="text-xs text-gray-400 font-mono break-all">{result.address}</p>}
            </div>
          );
        }
        return (
          <div className="text-center space-y-3 py-4">
            <p className="text-sm text-gray-300">Ready to deploy <span className="font-bold">{form.symbol}</span> on {form.chain}?</p>
            <button onClick={handleCreate} disabled={loading}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-700 px-6 py-2 rounded-lg text-sm font-medium transition">
              {loading ? "Deploying..." : "Deploy Token"}
            </button>
          </div>
        );
    }
  };

  return (
    <div className="bg-gray-900 text-white rounded-xl border border-gray-700 overflow-hidden">
      <div className="px-4 py-3 bg-gray-800 border-b border-gray-700">
        <h2 className="text-lg font-semibold">Token Creator</h2>
      </div>

      <div className="p-4 space-y-4">
        {error && <div className="bg-red-900/40 border border-red-700 text-red-300 px-3 py-2 rounded text-xs">{error}</div>}

        {/* Step Indicator */}
        <div className="flex items-center gap-1">
          {STEPS.map((s, i) => (
            <React.Fragment key={s}>
              <div className={`flex items-center gap-1 ${i <= step ? "text-blue-400" : "text-gray-600"}`}>
                <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border ${i <= step ? "border-blue-500 bg-blue-600/20" : "border-gray-700"}`}>{i + 1}</span>
                <span className="text-xs hidden sm:inline">{s}</span>
              </div>
              {i < STEPS.length - 1 && <div className={`flex-1 h-px ${i < step ? "bg-blue-500" : "bg-gray-700"}`} />}
            </React.Fragment>
          ))}
        </div>

        {renderStep()}

        {/* Navigation */}
        {step < 3 && (
          <div className="flex justify-between pt-2">
            <button onClick={handleBack} disabled={step === 0}
              className="px-4 py-1.5 rounded text-xs text-gray-400 hover:text-white disabled:opacity-30 transition">Back</button>
            <button onClick={handleNext}
              disabled={(step === 0 && !isStep1Valid) || (step === 1 && !isStep2Valid)}
              className="px-4 py-1.5 rounded text-xs bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 transition">
              {step === 2 ? "Proceed" : "Next"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CryptoMakerPanel;
