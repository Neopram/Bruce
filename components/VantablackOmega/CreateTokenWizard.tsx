
import React, { useState, useCallback } from "react"
import { Card, CardContent } from "@/components/ui/card"
import Badge from "@/components/ui/badge"
import Progress from "@/components/ui/progress"

interface TokenConfig {
  name: string
  symbol: string
  totalSupply: string
  decimals: number
  network: string
  features: {
    mintable: boolean
    burnable: boolean
    pausable: boolean
    taxOnTransfer: boolean
    antiWhale: boolean
  }
  taxPercent: number
  maxWalletPercent: number
}

type WizardStep = "basic" | "features" | "economics" | "review" | "deploy"

const NETWORKS = [
  { value: "solana", label: "Solana" },
  { value: "ethereum", label: "Ethereum" },
  { value: "bsc", label: "BNB Chain" },
  { value: "polygon", label: "Polygon" },
  { value: "base", label: "Base" },
  { value: "arbitrum", label: "Arbitrum" },
]

const STEPS: WizardStep[] = ["basic", "features", "economics", "review", "deploy"]

const CreateTokenWizard = () => {
  const [step, setStep] = useState<WizardStep>("basic")
  const [config, setConfig] = useState<TokenConfig>({
    name: "",
    symbol: "",
    totalSupply: "1000000000",
    decimals: 18,
    network: "solana",
    features: {
      mintable: false,
      burnable: true,
      pausable: false,
      taxOnTransfer: false,
      antiWhale: true,
    },
    taxPercent: 0,
    maxWalletPercent: 2,
  })
  const [deploying, setDeploying] = useState(false)
  const [result, setResult] = useState("")
  const [deployProgress, setDeployProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const currentStepIndex = STEPS.indexOf(step)
  const progressPercent = ((currentStepIndex + 1) / STEPS.length) * 100

  const nextStep = () => {
    const idx = STEPS.indexOf(step)
    if (idx < STEPS.length - 1) setStep(STEPS[idx + 1])
  }

  const prevStep = () => {
    const idx = STEPS.indexOf(step)
    if (idx > 0) setStep(STEPS[idx - 1])
  }

  const handleDeploy = useCallback(async () => {
    setDeploying(true)
    setError(null)
    setDeployProgress(0)

    const progressInterval = setInterval(() => {
      setDeployProgress(prev => Math.min(prev + 8, 90))
    }, 500)

    try {
      const res = await fetch("/api/create-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      })
      const data = await res.json()
      clearInterval(progressInterval)
      setDeployProgress(100)
      setResult(data.message || `Token ${config.symbol} deployed successfully!`)
      setStep("deploy")
    } catch (err: any) {
      clearInterval(progressInterval)
      setError(err.message || "Deployment failed")
      setDeployProgress(0)
    } finally {
      setDeploying(false)
    }
  }, [config])

  const Toggle = ({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) => (
    <label className="flex items-center justify-between py-1.5">
      <span className="text-sm text-zinc-300">{label}</span>
      <button
        type="button"
        onClick={() => onChange(!checked)}
        className={`relative w-10 h-5 rounded-full transition-colors ${checked ? "bg-indigo-600" : "bg-zinc-700"}`}
      >
        <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform ${checked ? "translate-x-5" : ""}`} />
      </button>
    </label>
  )

  return (
    <Card className="bg-gradient-to-br from-zinc-900 to-amber-950/20 border-amber-800/30">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-white">Create Token Wizard</h2>
            <p className="text-sm text-zinc-400 mt-1">Multi-chain token deployment</p>
          </div>
          <Badge variant="warning" size="sm">Step {currentStepIndex + 1}/{STEPS.length}</Badge>
        </div>

        <Progress value={progressPercent} variant="default" size="sm" className="mb-6" />

        {/* Step Indicators */}
        <div className="flex gap-1 mb-6">
          {STEPS.map((s, i) => (
            <button
              key={s}
              onClick={() => i <= currentStepIndex && setStep(s)}
              className={`flex-1 py-1 text-xs rounded transition-colors ${
                i === currentStepIndex
                  ? "bg-amber-700/50 text-white"
                  : i < currentStepIndex
                  ? "bg-zinc-700/50 text-zinc-400 hover:text-white"
                  : "bg-zinc-800/30 text-zinc-600"
              }`}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>

        {error && (
          <div className="mb-4 p-2 rounded-lg bg-red-900/30 border border-red-800/50 text-red-400 text-sm">{error}</div>
        )}

        {/* Step Content */}
        {step === "basic" && (
          <div className="space-y-3">
            <div>
              <label className="text-sm text-zinc-400 block mb-1">Token Name</label>
              <input
                className="w-full p-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:ring-1 focus:ring-amber-600 focus:outline-none"
                value={config.name} onChange={(e) => setConfig(p => ({ ...p, name: e.target.value }))}
                placeholder="e.g., Bruce Coin"
              />
            </div>
            <div>
              <label className="text-sm text-zinc-400 block mb-1">Symbol</label>
              <input
                className="w-full p-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm uppercase focus:ring-1 focus:ring-amber-600 focus:outline-none"
                value={config.symbol} onChange={(e) => setConfig(p => ({ ...p, symbol: e.target.value.toUpperCase() }))}
                placeholder="e.g., BVC"
                maxLength={10}
              />
            </div>
            <div>
              <label className="text-sm text-zinc-400 block mb-1">Network</label>
              <div className="grid grid-cols-3 gap-2">
                {NETWORKS.map(n => (
                  <button
                    key={n.value}
                    onClick={() => setConfig(p => ({ ...p, network: n.value }))}
                    className={`p-2 text-xs rounded-lg border transition-colors ${
                      config.network === n.value
                        ? "bg-amber-800/30 border-amber-600/50 text-white"
                        : "bg-zinc-800/50 border-zinc-700/50 text-zinc-400 hover:border-zinc-600"
                    }`}
                  >
                    {n.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-sm text-zinc-400 block mb-1">Total Supply</label>
              <input
                type="number"
                className="w-full p-2.5 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:ring-1 focus:ring-amber-600 focus:outline-none"
                value={config.totalSupply} onChange={(e) => setConfig(p => ({ ...p, totalSupply: e.target.value }))}
              />
            </div>
          </div>
        )}

        {step === "features" && (
          <div className="space-y-1">
            <Toggle checked={config.features.mintable} onChange={v => setConfig(p => ({ ...p, features: { ...p.features, mintable: v } }))} label="Mintable" />
            <Toggle checked={config.features.burnable} onChange={v => setConfig(p => ({ ...p, features: { ...p.features, burnable: v } }))} label="Burnable" />
            <Toggle checked={config.features.pausable} onChange={v => setConfig(p => ({ ...p, features: { ...p.features, pausable: v } }))} label="Pausable" />
            <Toggle checked={config.features.taxOnTransfer} onChange={v => setConfig(p => ({ ...p, features: { ...p.features, taxOnTransfer: v } }))} label="Tax on Transfer" />
            <Toggle checked={config.features.antiWhale} onChange={v => setConfig(p => ({ ...p, features: { ...p.features, antiWhale: v } }))} label="Anti-Whale Protection" />
          </div>
        )}

        {step === "economics" && (
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-zinc-400">Transfer Tax</span>
                <span className="text-zinc-300">{config.taxPercent}%</span>
              </div>
              <input type="range" min={0} max={10} step={0.5} value={config.taxPercent}
                onChange={(e) => setConfig(p => ({ ...p, taxPercent: parseFloat(e.target.value) }))}
                className="w-full accent-amber-500" />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-zinc-400">Max Wallet %</span>
                <span className="text-zinc-300">{config.maxWalletPercent}%</span>
              </div>
              <input type="range" min={0.5} max={10} step={0.5} value={config.maxWalletPercent}
                onChange={(e) => setConfig(p => ({ ...p, maxWalletPercent: parseFloat(e.target.value) }))}
                className="w-full accent-amber-500" />
            </div>
            <div>
              <label className="text-sm text-zinc-400 block mb-1">Decimals</label>
              <input type="number" min={0} max={18} value={config.decimals}
                onChange={(e) => setConfig(p => ({ ...p, decimals: parseInt(e.target.value) || 18 }))}
                className="w-full p-2 bg-zinc-800 border border-zinc-700 rounded-lg text-white text-sm focus:ring-1 focus:ring-amber-600 focus:outline-none" />
            </div>
          </div>
        )}

        {step === "review" && (
          <div className="space-y-3">
            <div className="bg-zinc-800/50 rounded-lg p-4 space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-zinc-400">Name:</span><span className="text-white">{config.name || "-"}</span></div>
              <div className="flex justify-between"><span className="text-zinc-400">Symbol:</span><span className="text-white">{config.symbol || "-"}</span></div>
              <div className="flex justify-between"><span className="text-zinc-400">Network:</span><span className="text-white capitalize">{config.network}</span></div>
              <div className="flex justify-between"><span className="text-zinc-400">Supply:</span><span className="text-white">{Number(config.totalSupply).toLocaleString()}</span></div>
              <div className="flex justify-between"><span className="text-zinc-400">Tax:</span><span className="text-white">{config.taxPercent}%</span></div>
              <div className="flex justify-between"><span className="text-zinc-400">Max Wallet:</span><span className="text-white">{config.maxWalletPercent}%</span></div>
              <div className="flex gap-2 flex-wrap mt-2">
                {Object.entries(config.features).filter(([,v]) => v).map(([k]) => (
                  <Badge key={k} variant="info" size="sm">{k}</Badge>
                ))}
              </div>
            </div>
            {deploying && <Progress value={deployProgress} variant="default" size="md" showValue label="Deploying..." />}
          </div>
        )}

        {step === "deploy" && result && (
          <div className="text-center py-6">
            <div className="text-4xl mb-3">&#10003;</div>
            <p className="text-lg font-semibold text-emerald-400 mb-2">Deployment Successful</p>
            <p className="text-sm text-zinc-400">{result}</p>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-6">
          <button
            onClick={prevStep}
            disabled={currentStepIndex === 0 || step === "deploy"}
            className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-sm text-white transition-colors disabled:opacity-30"
          >
            Back
          </button>
          {step === "review" ? (
            <button
              onClick={handleDeploy}
              disabled={deploying || !config.name || !config.symbol}
              className="px-6 py-2 bg-amber-600 hover:bg-amber-500 rounded-lg text-sm text-white font-medium transition-colors disabled:opacity-50"
            >
              {deploying ? "Deploying..." : "Deploy Token"}
            </button>
          ) : step !== "deploy" ? (
            <button
              onClick={nextStep}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm text-white transition-colors"
            >
              Next
            </button>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}

export default CreateTokenWizard
