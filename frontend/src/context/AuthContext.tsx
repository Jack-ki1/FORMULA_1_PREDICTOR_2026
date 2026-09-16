/**
 * Authentication context stub - auth is currently disabled
 * Provides compatibility with existing code while auth is turned off
 */
import { createContext, useContext, ReactNode } from 'react'

// Auth is disabled - this is a stub for compatibility
interface AuthContextType {
  user: null
  isLoading: false
  error: null
  login: () => Promise<void>
  register: () => Promise<void>
  logout: () => Promise<void>
  refreshAuth: () => Promise<void>
  isAuthenticated: false
  isAdmin: false
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoading: false,
  error: null,
  login: async () => {},
  register: async () => {},
  logout: async () => {},
  refreshAuth: async () => {},
  isAuthenticated: false,
  isAdmin: false,
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const value: AuthContextType = {
    user: null,
    isLoading: false,
    error: null,
    login: async () => {},
    register: async () => {},
    logout: async () => {},
    refreshAuth: async () => {},
    isAuthenticated: false,
    isAdmin: false,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
