// 📂 Ruta: C:\Users\feder\Desktop\OKK_Gorilla_Bot\frontend\components\TradeSimulationPanel.tsx

import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Label,
} from "recharts";
import { toast } from "react-toastify";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface SimulationStep {
  timestamp: string;
  price: number;
  action: string;
  reward: number;
  position: number;
  episode?: number;
}

export default function TradeSimulationPanel() {
  const [data, setData] = useState<SimulationStep[]>([]);
  const [index, setIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const [currentStep, setCurrentStep] = useState<SimulationStep | null>(null);

  const fetchSimulationData = async () => {
    try {
      const res = await axios.get(`${API_URL}/simulation/episode`);
      setData(res.data || []);
      setIndex(0);
      setCurrentStep(res.data[0] || null);
    } catch (err) {
      toast.error("Failed to fetch simulation episode data");
      console.error(err);
    }
  };

  const startPlayback = () => {
    if (data.length === 0) return;
    setIsPlaying(true);
    intervalRef.current = setInterval(() => {
      setIndex((prev) => {
        const next = prev + 1;
        if (next >= data.length) {
          clearInterval(intervalRef.current!);
          setIsPlaying(false);
          return prev;
        }
        setCurrentStep(data[next]);
        return next;
      });
    }, 700);
  };

  const pausePlayback = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setIsPlaying(false);
  };

  const resetPlayback = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setIndex(0);
    setCurrentStep(data[0] || null);
    setIsPlaying(false);
  };

  useEffect(() => {
    fetchSimulationData();
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const visibleData = data.slice(0, index + 1);

  return (
    <div className="p-6 border rounded-2xl shadow-md bg-white space-y-6">
      <h2 className="text-2xl font-semibold">🎥 Trade Simulation Playback</h2>
      <p className="text-gray-600 text-sm">
        Step through historical decisions of your RL agent and visualize its performance over time.
      </p>

      <div className="flex gap-4">
        <button
          onClick={startPlayback}
          disabled={isPlaying}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          ▶️ Start
        </button>
        <button
          onClick={pausePlayback}
          disabled={!isPlaying}
          className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
        >
          ⏸ Pause
        </button>
        <button
          onClick={resetPlayback}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          ⏹ Reset
        </button>
      </div>

      {currentStep && (
        <div className="text-sm text-gray-700">
          <strong>Current Step:</strong> Episode {currentStep.episode ?? "-"}, Action: <em>{currentStep.action}</em>,
          Reward: {currentStep.reward}, Price: {currentStep.price}, Position: {currentStep.position}
        </div>
      )}

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={visibleData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp">
              <Label value="Time" offset={-5} position="insideBottom" />
            </XAxis>
            <YAxis yAxisId="left" orientation="left">
              <Label value="Price" angle={-90} position="insideLeft" />
            </YAxis>
            <YAxis yAxisId="right" orientation="right">
              <Label value="Reward" angle={-90} position="insideRight" />
            </YAxis>
            <Tooltip />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="price"
              stroke="#2563eb"
              strokeWidth={2}
              name="Price"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="reward"
              stroke="#10b981"
              strokeWidth={2}
              name="Reward"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}