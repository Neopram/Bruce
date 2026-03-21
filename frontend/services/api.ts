import { useAuth } from "@/contexts/AuthContext"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"

export const useApi = () => {
  const { token } = useAuth()

  const getHeaders = () => ({
    "Content-Type": "application/json",
    Authorization: token ? `Bearer ${token}` : "",
  })

  const handleResponse = async (res: Response) => {
    if (!res.ok) {
      const text = await res.text()
      throw new Error(`Error ${res.status}: ${text}`)
    }
    return res.json()
  }

  const get = async (endpoint: string) => {
    const res = await fetch(`${BASE_URL}${endpoint}`, {
      method: "GET",
      headers: getHeaders(),
    })
    return handleResponse(res)
  }

  const post = async (endpoint: string, body: any) => {
    const res = await fetch(`${BASE_URL}${endpoint}`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(body),
    })
    return handleResponse(res)
  }

  return {
    prediction: {
      get: () => get("/predict"),
    },
    training: {
      start: (payload: {
        model_name: string
        env_name: string
        learning_rate: number
        episodes: number
      }) => post("/train/start", payload),
      stop: () => post("/train/stop", {}),
      logs: () => get("/train/logs"),
    },
    memory: {
      summary: () => get("/memory/summary"),
      stats: () => get("/memory/stats"),
    },
    meta: {
      info: () => get("/meta/info"),
    },
    health: {
      check: () => get("/health"),
    },
  }
}