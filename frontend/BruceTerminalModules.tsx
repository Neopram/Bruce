import React, { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { UploadCloud, Trash2, BookOpen, Settings2 } from 'lucide-react'

export function FileUploader({ onFileUpload }: { onFileUpload: (file: File) => void }) {
  const fileRef = useRef<HTMLInputElement | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(e.target.files[0])
    }
  }

  return (
    <div className="flex items-center gap-2">
      <input type="file" className="hidden" ref={fileRef} onChange={handleFileChange} />
      <Button onClick={() => fileRef.current?.click()} variant="outline">
        <UploadCloud size={16} className="mr-2" />
        Upload File
      </Button>
    </div>
  )
}

export function HistoryPanel({ history, onClear }: {
  history: { role: string, message: string }[],
  onClear: () => void
}) {
  return (
    <div className="bg-gray-900 p-4 border border-gray-700 rounded-lg max-h-[300px] overflow-y-scroll">
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-sm text-white">Conversation History</h2>
        <Button size="sm" variant="destructive" onClick={onClear}>
          <Trash2 size={14} />
        </Button>
      </div>
      <ul className="text-sm space-y-1 text-gray-300">
        {history.map((msg, i) => (
          <li key={i}>
            <span className="font-bold">{msg.role === "bruce" ? "🧠" : "🧍"}:</span> {msg.message.slice(0, 80)}...
          </li>
        ))}
      </ul>
    </div>
  )
}

export function PersonalitySelector({
  selected, onChange
}: { selected: string, onChange: (p: string) => void }) {
  const personas = ["Default", "Guardian", "Shadow", "Genius", "Healer"]
  return (
    <div className="flex items-center gap-2 mt-2">
      <span className="text-gray-300 text-sm">Persona:</span>
      <select
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        className="bg-gray-800 text-white border border-gray-600 rounded px-2 py-1 text-sm"
      >
        {personas.map((p) => (
          <option key={p} value={p}>{p}</option>
        ))}
      </select>
    </div>
  )
}
