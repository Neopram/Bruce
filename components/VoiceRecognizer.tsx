import React, { useState, useRef, useEffect } from "react";

interface VoiceRecognizerProps {
  onResult?: (text: string, isFinal: boolean) => void;
  defaultLanguage?: string;
}

const LANGUAGES = [
  { code: "en-US", label: "English" },
  { code: "es-ES", label: "Spanish" },
  { code: "pt-BR", label: "Portuguese" },
];

const VoiceRecognizer: React.FC<VoiceRecognizerProps> = ({ onResult, defaultLanguage = "en-US" }) => {
  const [isListening, setIsListening] = useState(false);
  const [language, setLanguage] = useState(defaultLanguage);
  const [finalText, setFinalText] = useState("");
  const [interimText, setInterimText] = useState("");
  const [confidence, setConfidence] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) setSupported(false);
    return () => recognitionRef.current?.stop();
  }, []);

  const startListening = () => {
    setError(null);
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { setError("Not supported"); return; }

    const recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = language;

    recognition.onresult = (event: any) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const text = result[0].transcript;
        if (result.isFinal) {
          setFinalText((prev) => prev + text + " ");
          setConfidence(Math.round(result[0].confidence * 100));
          onResult?.(text, true);
        } else {
          interim += text;
          onResult?.(text, false);
        }
      }
      setInterimText(interim);
    };

    recognition.onerror = (event: any) => {
      setError(`Error: ${event.error}`);
      setIsListening(false);
    };

    recognition.onend = () => setIsListening(false);

    recognition.start();
    recognitionRef.current = recognition;
    setIsListening(true);
    setFinalText("");
    setInterimText("");
    setConfidence(null);
  };

  const stopListening = () => {
    recognitionRef.current?.stop();
    setIsListening(false);
  };

  if (!supported) {
    return (
      <div className="bg-gray-900 text-gray-400 rounded-xl border border-gray-700 p-4 text-sm">
        Speech recognition is not supported in this browser.
      </div>
    );
  }

  return (
    <div className="bg-gray-900 text-white rounded-xl border border-gray-700 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-300">Voice Recognizer</h3>
        {confidence !== null && (
          <span className="text-xs text-gray-400">
            Confidence: <span className={confidence > 80 ? "text-green-400" : confidence > 50 ? "text-yellow-400" : "text-red-400"}>{confidence}%</span>
          </span>
        )}
      </div>

      {/* Language Selector */}
      <div className="flex items-center gap-2">
        <label className="text-xs text-gray-400">Language:</label>
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          disabled={isListening}
          className="bg-gray-800 text-white text-xs rounded px-2 py-1 border border-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {LANGUAGES.map((l) => (
            <option key={l.code} value={l.code}>{l.label}</option>
          ))}
        </select>
      </div>

      {/* Controls */}
      <div className="flex gap-2">
        <button
          onClick={isListening ? stopListening : startListening}
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${
            isListening
              ? "bg-red-600 hover:bg-red-700"
              : "bg-green-600 hover:bg-green-700"
          }`}
        >
          {isListening ? "Stop Listening" : "Start Listening"}
        </button>
      </div>

      {/* Status */}
      {isListening && (
        <div className="flex items-center gap-2 text-xs text-green-400">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          Listening...
        </div>
      )}

      {/* Results */}
      <div className="bg-gray-800 rounded-lg p-3 min-h-[80px] text-sm space-y-1">
        {finalText && <p className="text-gray-200">{finalText}</p>}
        {interimText && <p className="text-gray-500 italic">{interimText}</p>}
        {!finalText && !interimText && (
          <p className="text-gray-600">{isListening ? "Speak now..." : "Press Start to begin"}</p>
        )}
      </div>

      {error && (
        <div className="bg-red-900/40 border border-red-700 text-red-300 px-3 py-2 rounded text-xs">{error}</div>
      )}
    </div>
  );
};

export default VoiceRecognizer;
