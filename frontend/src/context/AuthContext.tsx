/**
 * Authentication context and provider for React.
 * Manages user authentication state across the application.
 */
import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { 
  login as apiLogin, 
  register as apiRegister, 
  logout as apiLogout,
  getProfile,
  refreshToken as apiRefreshToken,
  storeTokens,
  // getAccessToken - unused but kept for future use
  getRefreshToken,
  clearTokens,
  isAuthenticated as checkAuth,
  type LoginData,
  type RegisterData,
  type UserProfile,
  type TokenResponse
} from '../api/auth'

interface AuthContextType {
  user: UserProfile | null
  isLoading: boolean
  error: string | null
  login: (data: LoginData) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => Promise<void>
  refreshAuth: () => Promise<void>
  isAuthenticated: boolean
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Initialize auth state on mount
  useEffect(() => {
    initializeAuth()
  }, [])

  const initializeAuth = async () => {
    try {
      if (checkAuth()) {
        const profile = await getProfile()
        setUser(profile)
      }
    } catch (err) {
      console.error('Failed to initialize auth:', err)
      clearTokens()
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (data: LoginData) => {
    try {
      setIsLoading(true)
      setError(null)
      
      const response: TokenResponse = await apiLogin(data)
      
      // Store tokens
      storeTokens(response.access_token, response.refresh_token)
      
      // Fetch user profile
      const profile = await getProfile()
      setUser(profile)
    } catch (err: any) {
      const errorMessage = err.response?.data?.error?.message || 'Login failed'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (data: RegisterData) => {
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await apiRegister(data)
      
      // Store tokens
      storeTokens(response.access_token, response.refresh_token)
      
      // Set user from response
      setUser(response.user)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Registration failed'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await apiLogout()
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      clearTokens()
      setUser(null)
    }
  }

  const refreshAuth = async () => {
    try {
      const refreshTok = getRefreshToken()
      if (!refreshTok) {
        throw new Error('No refresh token')
      }
      
      const response: TokenResponse = await apiRefreshToken(refreshTok)
      storeTokens(response.access_token, response.refresh_token)
      
      // Refresh profile
      const profile = await getProfile()
      setUser(profile)
    } catch (err) {
      console.error('Token refresh failed:', err)
      clearTokens()
      setUser(null)
    }
  }

  const value: AuthContextType = {
    user,
    isLoading,
    error,
    login,
    register,
    logout,
    refreshAuth,
    isAuthenticated: !!user,
    isAdmin: user?.is_admin || false,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
