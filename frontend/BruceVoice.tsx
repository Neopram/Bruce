import React, { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Mic, StopCircle, PlayCircle } from 'lucide-react'

export function VoiceRecorder({ onTranscript }: { onTranscript: (text: string) => void }) {
  const [recording, setRecording] = useState(false)
  const [recognition, setRecognition] = useState<any>(null)

  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
      const rec = new SpeechRecognition()
      rec.lang = 'en-US'
      rec.continuous = false
      rec.interimResults = false

      rec.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript
        onTranscript(transcript)
      }

      rec.onend = () => setRecording(false)

      setRecognition(rec)
    }
  }, [])

  const toggleRecording = () => {
    if (!recognition) return
    if (recording) {
      recognition.stop()
    } else {
      recognition.start()
    }
    setRecording(!recording)
  }

  return (
    <Button onClick={toggleRecording} variant={recording ? 'destructive' : 'outline'}>
      {recording ? <StopCircle size={16} className="mr-2" /> : <Mic size={16} className="mr-2" />}
      {recording ? "Stop" : "Speak"}
    </Button>
  )
}

export function TTSPlayer({ text }: { text: string }) {
  const handlePlay = () => {
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = "en-US"
    utterance.rate = 1
    speechSynthesis.speak(utterance)
  }

  return (
    <Button onClick={handlePlay} variant="outline">
      <PlayCircle size={16} className="mr-2" />
      Speak
    </Button>
  )
}
