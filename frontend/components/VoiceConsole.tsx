import { useState } from 'react'
import axios from 'axios'

export default function VoiceConsole() {
  const [text, setText] = useState('')
  const [voice, setVoice] = useState('creator')
  const [audio, setAudio] = useState('')

  const speak = async () => {
    const res = await axios.post('/api/speak', { text, voice })
    setAudio(res.data.audio)
  }

  return (
    <div className="p-4 rounded-xl shadow-xl">
      <h2 className="text-xl font-bold mb-2">🗣️ Bruce Voice Console</h2>
      <textarea value={text} onChange={e => setText(e.target.value)} className="w-full p-2 mb-2" rows={4} />
      <input value={voice} onChange={e => setVoice(e.target.value)} className="w-full p-2 mb-2" placeholder="Voice ID" />
      <button onClick={speak} className="bg-black text-white px-4 py-2 rounded-xl">Speak</button>
      {audio && <p className="mt-4">{audio}</p>}
    </div>
  )
}