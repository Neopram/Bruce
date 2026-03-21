import React, { useState } from 'react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export default function DataLoaderComponent() {
  const [symbol, setSymbol] = useState("BTC/USDT")
  const [exchange, setExchange] = useState("binance")
  const [timeframe, setTimeframe] = useState("1m")
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<any[]>([])
  const [columns, setColumns] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get(`${API_URL}/market/fetch`, {
        params: { symbol, exchange, timeframe }
      })
      setColumns(response.data.columns)
      setPreview(response.data.preview)
    } catch (err: any) {
      console.error(err)
      setError("Error fetching data from exchange.")
    }
    setLoading(false)
  }

  const uploadFile = async () => {
    if (!file) return alert("Please select a file before uploading.")
    setLoading(true)
    setError(null)

    const formData = new FormData()
    formData.append("file", file)
    formData.append("market", symbol)
    formData.append("timeframe", timeframe)
    formData.append("source", "file")

    try {
      const res = await axios.post(`${API_URL}/market/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      })
      setColumns(res.data.columns)
      setPreview(res.data.preview)
    } catch (err: any) {
      console.error(err)
      setError("Failed to upload file.")
    }
    setLoading(false)
  }

  return (
    <div className="p-6 border rounded-2xl shadow-md bg-white space-y-6">
      <h2 className="text-2xl font-semibold">📊 Market Data Loader</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block font-medium">Market Symbol</label>
          <input
            type="text"
            value={symbol}
            onChange={e => setSymbol(e.target.value)}
            className="border p-2 w-full rounded"
          />
        </div>

        <div>
          <label className="block font-medium">Exchange</label>
          <select
            value={exchange}
            onChange={e => setExchange(e.target.value)}
            className="border p-2 w-full rounded"
          >
            <option value="binance">Binance</option>
            <option value="kucoin">KuCoin</option>
          </select>
        </div>

        <div>
          <label className="block font-medium">Timeframe</label>
          <select
            value={timeframe}
            onChange={e => setTimeframe(e.target.value)}
            className="border p-2 w-full rounded"
          >
            <option value="1m">1m</option>
            <option value="5m">5m</option>
            <option value="15m">15m</option>
            <option value="1h">1h</option>
            <option value="1d">1d</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block font-medium mb-1">Upload Custom Dataset</label>
        <input
          type="file"
          accept=".csv,.json,.parquet"
          onChange={e => setFile(e.target.files?.[0] || null)}
          className="block"
        />
        <button
          onClick={uploadFile}
          className="mt-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded"
        >
          Upload File
        </button>
      </div>

      <div className="flex space-x-4">
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
        >
          Fetch from Exchange
        </button>
      </div>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {preview.length > 0 && (
        <div className="overflow-x-auto mt-4">
          <table className="min-w-full text-sm border border-gray-300">
            <thead className="bg-gray-100">
              <tr>{columns.map(col => <th key={col} className="border px-2 py-1">{col}</th>)}</tr>
            </thead>
            <tbody>
              {preview.map((row, idx) => (
                <tr key={idx}>
                  {columns.map(col => (
                    <td key={col} className="border px-2 py-1">{row[col]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
