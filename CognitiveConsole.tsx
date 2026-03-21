import React from "react";
import BruceAvatar from "@/components/BruceAvatar";
import EmotionDashboard from "@/components/EmotionDashboard";
import ChatLLM from "@/ChatLLM";

export default function CognitiveConsole() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 to-white p-6 space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-4">
          <BruceAvatar />
          <EmotionDashboard />
        </div>
        <div className="space-y-4">
          <ChatLLM />
        </div>
      </div>
    </div>
  );
}