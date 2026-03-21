// Ruta: frontend/services/useApi.ts

import { useAuth } from "@/contexts/AuthContext"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export const useApi = () => {
  const { token } = useAuth()

  const getHeaders = (): HeadersInit => ({
    "Content-Type": "application/json",
    Authorization: token ? `Bearer ${token}` : "",
  })

  const handleResponse = async (res: Response) => {
    if (!res.ok) {
      const error = await res.text()
      throw new Error(`Error ${res.status}: ${error}`)
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
    chat: {
      send: (message: string, user: string) =>
        post("/chat", { message, user }),
    },
    memory: {
      get: (user: string) => get(`/memory/${user}`),
      summarize: (user: string) => get(`/memory/summary/${user}`),
      summary: () => get("/memory/summary"),
      stats: () => get("/memory/stats"),
    },
    training: {
      start: (params: {
        model_name: string
        env_name: string
        learning_rate: number
        episodes: number
      }) => post("/train/start", params),
      stop: () => post("/train/stop", {}),
      logs: () => get("/train/logs"),
    },
    prediction: {
      get: () => get("/predict"),
    },
    arbitraje: {
      opportunities: () => get("/arbitraje/opportunities"),
    },
    health: {
      general: () => get("/health"),
      status: () => get("/ai/self-healing/status"),
      heal: () => post("/ai/self-healing/heal", {}),
    },
    meta: {
      info: () => get("/meta/info"),
      reset: () => post("/meta/reset", {}),
    },
  }
}
