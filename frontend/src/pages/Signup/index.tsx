/**
 * Signup page component.
 * Allows new users to register for an account.
 */
import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export function SignupPage() {
  const navigate = useNavigate()
  const { register, isLoading, error } = useAuth()
  
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    full_name: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
    setValidationError(null)
  }

  const validateForm = (): boolean => {
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) {
      setValidationError('Please enter a valid email address')
      return false
    }

    // Username validation
    if (formData.username.length < 3) {
      setValidationError('Username must be at least 3 characters')
      return false
    }
    if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      setValidationError('Username can only contain letters, numbers, and underscores')
      return false
    }

    // Password validation
    if (formData.password.length < 8) {
      setValidationError('Password must be at least 8 characters')
      return false
    }
    if (formData.password !== formData.confirmPassword) {
      setValidationError('Passwords do not match')
      return false
    }

    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    try {
      await register({
        email: formData.email,
        username: formData.username,
        password: formData.password,
        full_name: formData.full_name || undefined,
      })
      navigate('/dashboard')
    } catch (err: any) {
      console.error('Registration error:', err)
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
          <h1 className="f1-display text-3xl font-black" style={{ color: 'var(--text)' }}>Create Account</h1>
          <p className="fs-11 mt-2" style={{ color: 'var(--sub)' }}>Join F1 Predictor 2026</p>
        </div>

        {/* Signup Form */}
        <div className="card p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Error Messages */}
            {(error || validationError) && (
              <div className="p-3 rounded-lg text-sm" style={{ background: '#fee2e2', color: '#dc2626', border: '1px solid #fecaca' }}>
                {validationError || error}
              </div>
            )}

            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block fs-11 font-bold mb-1" style={{ color: 'var(--text)' }}>
                Email Address
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="you@example.com"
                className="f1-input w-full"
                autoComplete="email"
                required
              />
            </div>

            {/* Username Field */}
            <div>
              <label htmlFor="username" className="block fs-11 font-bold mb-1" style={{ color: 'var(--text)' }}>
                Username
              </label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="johndoe"
                className="f1-input w-full"
                autoComplete="username"
                required
              />
              <p className="fs-11 mt-1" style={{ color: 'var(--sub)' }}>Letters, numbers, and underscores only</p>
            </div>

            {/* Full Name Field (Optional) */}
            <div>
              <label htmlFor="full_name" className="block fs-11 font-bold mb-1" style={{ color: 'var(--text)' }}>
                Full Name <span style={{ color: 'var(--sub)' }}>(Optional)</span>
              </label>
              <input
                type="text"
                id="full_name"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                placeholder="John Doe"
                className="f1-input w-full"
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
                  placeholder="Minimum 8 characters"
                  className="f1-input w-full pr-10"
                  autoComplete="new-password"
                  required
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

            {/* Confirm Password Field */}
            <div>
              <label htmlFor="confirmPassword" className="block fs-11 font-bold mb-1" style={{ color: 'var(--text)' }}>
                Confirm Password
              </label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="Re-enter your password"
                className="f1-input w-full"
                autoComplete="new-password"
                required
              />
            </div>

            {/* Terms and Conditions */}
            <div className="fs-11" style={{ color: 'var(--sub)' }}>
              By creating an account, you agree to our{' '}
              <a href="#" className="hover:underline" style={{ color: 'var(--red)' }}>Terms of Service</a>
              {' '}and{' '}
              <a href="#" className="hover:underline" style={{ color: 'var(--red)' }}>Privacy Policy</a>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full"
              style={{ background: 'var(--red)' }}
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-3">
            <div className="flex-1 h-px" style={{ background: 'var(--border)' }}></div>
            <span className="fs-11" style={{ color: 'var(--sub)' }}>or</span>
            <div className="flex-1 h-px" style={{ background: 'var(--border)' }}></div>
          </div>

          {/* Login Link */}
          <div className="text-center">
            <p className="fs-11" style={{ color: 'var(--sub)' }}>
              Already have an account?{' '}
              <Link to="/login" className="font-bold hover:underline" style={{ color: 'var(--red)' }}>
                Sign in
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
