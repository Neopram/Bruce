import { useState } from 'react'
import axios from 'axios'

export default function VideoReportBuilder() {
  const [script, setScript] = useState('')
  const [persona, setPersona] = useState('reporter')
  const [video, setVideo] = useState('')

  const generate = async () => {
    const res = await axios.post('/api/report', { script, persona })
    setVideo(res.data.video)
  }

  return (
    <div className="p-4 rounded-xl shadow-xl">
      <h2 className="text-xl font-bold mb-2">🎥 Generate Video Report</h2>
      <textarea value={script} onChange={e => setScript(e.target.value)} className="w-full p-2 mb-2" rows={4} />
      <input value={persona} onChange={e => setPersona(e.target.value)} placeholder="Persona (e.g., reporter)" className="w-full p-2 mb-2" />
      <button onClick={generate} className="bg-indigo-600 text-white px-4 py-2 rounded-xl">Generate Video</button>
      {video && <p className="mt-4">{video}</p>}
    </div>
  )
}