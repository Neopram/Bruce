import React from "react";
import VantablackDashboard from "./components/vantablack/VantablackDashboard";
import { AuthProvider } from "./contexts/AuthContext";

export default function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-950 text-white font-sans p-4">
        <VantablackDashboard />
      </div>
    </AuthProvider>
  );
}