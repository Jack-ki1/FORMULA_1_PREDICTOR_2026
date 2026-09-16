/**
 * Authentication API client.
 * Handles user registration, login, token management, and profile operations.
 */
import { api } from './client'

export interface RegisterData {
  email: string
  username: string
  password: string
  full_name?: string
}

export interface LoginData {
  email_or_username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserProfile {
  id: number
  email: string
  username: string
  full_name?: string
  is_admin: boolean
  favorite_driver?: string
  favorite_team?: string
  theme_preference: string
  created_at: string
}

export interface UpdateProfileData {
  full_name?: string
  favorite_driver?: string
  favorite_team?: string
  theme_preference?: string
}

/**
 * Register a new user account
 */
export async function register(data: RegisterData): Promise<TokenResponse & { user: UserProfile; message: string }> {
  const response = await api.post<any>('/api/v1/auth/register', data)
  return response
}

/**
 * Login with credentials
 */
export async function login(data: LoginData): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>('/api/v1/auth/login', data)
  return response
}

/**
 * Refresh access token using refresh token
 */
export async function refreshToken(refreshToken: string): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>('/api/v1/auth/refresh', null, {
    params: { refresh: refreshToken }
  })
  return response
}

/**
 * Get current user profile
 */
export async function getProfile(): Promise<UserProfile> {
  const response = await api.get<UserProfile>('/api/v1/auth/profile')
  return response
}

/**
 * Update user profile
 */
export async function updateProfile(data: UpdateProfileData): Promise<UserProfile> {
  const response = await api.put<UserProfile>('/api/v1/auth/profile', data)
  return response
}

/**
 * Logout (client-side token removal)
 */
export async function logout(): Promise<{ message: string }> {
  const response = await api.post<{ message: string }>('/api/v1/auth/logout', {})
  return response
}

/**
 * Verify if current token is valid
 */
export async function verifyToken(): Promise<{ valid: boolean; user_id: number; username: string; is_admin: boolean }> {
  const response = await api.get<any>('/api/v1/auth/verify')
  return response
}

/**
 * Store tokens in localStorage
 */
export function storeTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem('f1_access_token', accessToken)
  localStorage.setItem('f1_refresh_token', refreshToken)
}

/**
 * Get stored access token
 */
export function getAccessToken(): string | null {
  return localStorage.getItem('f1_access_token')
}

/**
 * Get stored refresh token
 */
export function getRefreshToken(): string | null {
  return localStorage.getItem('f1_refresh_token')
}

/**
 * Clear stored tokens
 */
export function clearTokens(): void {
  localStorage.removeItem('f1_access_token')
  localStorage.removeItem('f1_refresh_token')
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return !!getAccessToken()
}
