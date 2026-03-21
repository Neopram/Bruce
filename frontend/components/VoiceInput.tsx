import React, { useState, useRef, useCallback, useEffect } from "react";

interface VoiceInputProps {
  onTranscript?: (text: string) => void;
  language?: string;
}

const VoiceInput: React.FC<VoiceInputProps> = ({ onTranscript, language = "en-US" }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimText, setInterimText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pulseScale, setPulseScale] = useState(1);
  const recognitionRef = useRef<any>(null);
  const animFrameRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      recognitionRef.current?.stop();
    };
  }, []);

  const animatePulse = useCallback(() => {
    if (!isRecording) return;
    const scale = 1 + 0.15 * Math.sin(Date.now() / 200);
    setPulseScale(scale);
    animFrameRef.current = requestAnimationFrame(animatePulse);
  }, [isRecording]);

  useEffect(() => {
    if (isRecording) {
      animatePulse();
    } else {
      setPulseScale(1);
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
    }
  }, [isRecording, animatePulse]);

  const startRecording = () => {
    setError(null);
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setError("Speech recognition not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = language;

    recognition.onresult = (event: any) => {
      let interim = "";
      let final = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += t + " ";
        } else {
          interim += t;
        }
      }
      if (final) {
        setTranscript((prev) => prev + final);
        onTranscript?.(final.trim());
      }
      setInterimText(interim);
    };

    recognition.onerror = (event: any) => {
      setError(`Recognition error: ${event.error}`);
      setIsRecording(false);
    };

    recognition.onend = () => {
      setIsRecording(false);
      setInterimText("");
    };

    recognition.start();
    recognitionRef.current = recognition;
    setIsRecording(true);
    setTranscript("");
  };

  const stopRecording = () => {
    recognitionRef.current?.stop();
    setIsRecording(false);
  };

  const toggleRecording = () => {
    if (isRecording) stopRecording();
    else startRecording();
  };

  return (
    <div className="bg-gray-900 text-white rounded-xl border border-gray-700 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-300">Voice Input</h3>
        {isRecording && (
          <span className="text-xs text-red-400 flex items-center gap-1">
            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            Recording
          </span>
        )}
      </div>

      <div className="flex justify-center">
        <button
          onMouseDown={toggleRecording}
          className={`w-16 h-16 rounded-full flex items-center justify-center transition-all duration-150 ${
            isRecording
              ? "bg-red-600 hover:bg-red-700 shadow-lg shadow-red-900/50"
              : "bg-blue-600 hover:bg-blue-700"
          }`}
          style={{ transform: `scale(${pulseScale})` }}
          title={isRecording ? "Stop recording" : "Start recording"}
        >
          {isRecording ? (
            <svg className="w-6 h-6" fill="white" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2" /></svg>
          ) : (
            <svg className="w-6 h-6" fill="white" viewBox="0 0 24 24"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5z"/><path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>
          )}
        </button>
      </div>

      {/* Transcript Area */}
      <div className="bg-gray-800 rounded-lg p-3 min-h-[60px] text-sm">
        {transcript && <span className="text-gray-200">{transcript}</span>}
        {interimText && <span className="text-gray-500 italic">{interimText}</span>}
        {!transcript && !interimText && (
          <span className="text-gray-600">
            {isRecording ? "Listening..." : "Press the button and speak"}
          </span>
        )}
      </div>

      {error && (
        <div className="bg-red-900/40 border border-red-700 text-red-300 px-3 py-2 rounded text-xs">
          {error}
        </div>
      )}
    </div>
  );
};

export default VoiceInput;
