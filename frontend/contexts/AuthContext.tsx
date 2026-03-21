import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react"

interface AuthContextType {
  token: string | null
  setToken: (token: string | null) => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("jwt_token")
      if (stored && stored.length > 10) {
        setToken(stored)
        setIsAuthenticated(true)
      }
    }
  }, [])

  useEffect(() => {
    if (typeof window !== "undefined") {
      if (token && token.length > 10) {
        localStorage.setItem("jwt_token", token)
        setIsAuthenticated(true)
      } else {
        localStorage.removeItem("jwt_token")
        setIsAuthenticated(false)
      }
    }
  }, [token])

  return (
    <AuthContext.Provider value={{ token, setToken, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}