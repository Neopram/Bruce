import DeepSeekMultilingualPanel from "@/components/DeepSeekMultilingualPanel";
import Head from "next/head"
import Dashboard from "../components/Dashboard"
import DataLoaderComponent from "../components/DataLoaderComponent"
import RLTrainerPanel from "../components/RLTrainerPanel"
import EpisodeViewerPanel from "../components/EpisodeViewerPanel"
import DeepSeekSupervisorPanel from "../components/DeepSeekSupervisorPanel"

export default function Home() {
  return (
    <>
      <Head>
        <title>OKK Gorilla Bot Dashboard</title>
        <meta name="description" content="OCFA - Autonomous Trading System Control Panel" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="min-h-screen bg-gray-100 py-10 px-4">
        <div className="max-w-7xl mx-auto space-y-12">

          {/* HEADER */}
          <section className="space-y-4">
            <h1 className="text-4xl font-bold text-gray-900">
              🦍 OKK Gorilla Bot Dashboard
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl">
              Welcome to your Autonomous Cognitive Financial Agent (OCFA) interface. 
              Here you can control training, monitor performance, manage strategies, 
              interact with DeepSeek AI, and operate across multiple exchanges.
            </p>
          </section>

          {/* MARKET DATA LOADER */}
          <section className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-800">📥 Market Data Loader</h2>
            <DataLoaderComponent />
          </section>

          {/* RL TRAINER PANEL */}
          <section className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-800">🤖 Reinforcement Learning Panel</h2>
            <RLTrainerPanel />
          </section>

          {/* EPISODIC VIEWER */}
          <section className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-800">📈 Episode History Viewer</h2>
            <EpisodeViewerPanel />
          </section>

          {/* CORE DASHBOARD */}
          <section className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-800">📊 Core Analytics Dashboard</h2>
            <Dashboard />
          </section>

          {/* DEEPSEEK SUPERVISOR CONTROL */}
          <section className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-800">🧠 DeepSeek Supervisor Control</h2>
            <DeepSeekSupervisorPanel />
          </section>

          {/* FUTURE MODULES */}
          <section className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-800">🧠 Expansion Modules</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

              <div className="p-4 bg-white rounded-xl shadow-sm border">
                <h3 className="text-xl font-bold mb-2">💬 DeepSeek AI Terminal</h3>
                <p className="text-sm text-gray-600">
                  Interactive chat with your AI strategist. Explain trades, request insights, automate actions.
                </p>
              </div>

              <div className="p-4 bg-white rounded-xl shadow-sm border">
                <h3 className="text-xl font-bold mb-2">📈 Execution & Risk Monitor</h3>
                <p className="text-sm text-gray-600">
                  Real-time metrics: PnL, drawdown, slippage, Sharpe ratio, and operational health.
                </p>
              </div>

              <div className="p-4 bg-white rounded-xl shadow-sm border">
                <h3 className="text-xl font-bold mb-2">🎥 Trade Simulation & Playback</h3>
                <p className="text-sm text-gray-600">
                  Replay market scenarios, inspect past strategies and learn from every episode.
                </p>
              </div>

              <div className="p-4 bg-white rounded-xl shadow-sm border">
                <h3 className="text-xl font-bold mb-2">🧬 DAO Governance Interface</h3>
                <p className="text-sm text-gray-600">
                  Submit proposals, vote on strategies, and deploy governance actions on-chain.
                </p>
              </div>

              <div className="p-4 bg-white rounded-xl shadow-sm border">
                <h3 className="text-xl font-bold mb-2">🌐 Web3 Integration Layer</h3>
                <p className="text-sm text-gray-600">
                  Full wallet, funding, and on-chain execution through Ethereum, Solana, and others.
                </p>
              </div>

            </div>
          </section>
        </div>
        <DeepSeekMultilingualPanel />
</main>
    </>
  )
}