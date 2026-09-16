/**
 * Login page component.
 * Allows users to authenticate with email/username and password.
 */
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export function LoginPage() {
  const navigate = useNavigate()
  const { login, isLoading, error } = useAuth()
  
  const [formData, setFormData] = useState({
    email_or_username: '',
    password: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
    setValidationError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setValidationError(null)

    // Validation
    if (!formData.email_or_username.trim()) {
      setValidationError('Email or username is required')
      return
    }
    if (!formData.password) {
      setValidationError('Password is required')
      return
    }

    try {
      await login(formData)
      navigate('/dashboard')
    } catch (err: any) {
      console.error('Login error:', err)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12" style={{ background: 'var(--bg)' }}>
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4" style={{ background: 'var(--red)' }}>
            <span className="text-white text-2xl font-black">F1</span>
          </div>
          <h1 className="f1-display text-3xl font-black" style={{ color: 'var(--text)' }}>Welcome Back</h1>
          <p className="fs-11 mt-2" style={{ color: 'var(--sub)' }}>Sign in to access F1 Predictor 2026</p>
        </div>

        {/* Login Form */}
        <div className="card p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Error Messages */}
            {(error || validationError) && (
              <div className="p-3 rounded-lg text-sm" style={{ background: '#fee2e2', color: '#dc2626', border: '1px solid #fecaca' }}>
                {validationError || error}
              </div>
            )}

            {/* Email/Username Field */}
            <div>
              <label htmlFor="email_or_username" className="block fs-11 font-bold mb-1" style={{ color: 'var(--text)' }}>
                Email or Username
              </label>
              <input
                type="text"
                id="email_or_username"
                name="email_or_username"
                value={formData.email_or_username}
                onChange={handleChange}
                placeholder="Enter your email or username"
                className="f1-input w-full"
                autoComplete="username"
                autoFocus
              />
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block fs-11 font-bold mb-1" style={{ color: 'var(--text)' }}>
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Enter your password"
                  className="f1-input w-full pr-10"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 fs-11"
                  style={{ color: 'var(--sub)' }}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full"
              style={{ background: 'var(--red)' }}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-3">
            <div className="flex-1 h-px" style={{ background: 'var(--border)' }}></div>
            <span className="fs-11" style={{ color: 'var(--sub)' }}>or</span>
            <div className="flex-1 h-px" style={{ background: 'var(--border)' }}></div>
          </div>

          {/* Sign Up Link */}
          <div className="text-center">
            <p className="fs-11" style={{ color: 'var(--sub)' }}>
              Don't have an account?{' '}
              <Link to="/signup" className="font-bold hover:underline" style={{ color: 'var(--red)' }}>
                Sign up
              </Link>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center fs-11" style={{ color: 'var(--sub)' }}>
          <p>F1 Predictor 2026 — AI-Powered Race Predictions</p>
        </div>
      </div>
    </div>
  )
}
