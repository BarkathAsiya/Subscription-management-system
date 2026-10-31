
import { useState } from 'react'
import { Link } from 'react-router-dom'

function Signup() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const passwordRules = [
  {
    label: 'At least 9 characters',
    valid: password.length >= 9,
  },
  {
    label: 'One uppercase letter (A-Z)',
    valid: /[A-Z]/.test(password),
  },
  {
    label: 'One lowercase letter (a-z)',
    valid: /[a-z]/.test(password),
  },
  {
    label: 'One special character',
    valid: /[^A-Za-z0-9]/.test(password),
  },
]

  const handleSignup = async (e) => {
    e.preventDefault()
    setMessage('')

    if (password !== confirmPassword) {
      setMessage('Passwords do not match.')
      return
    }

    if (password.length < 9 || !/[A-Z]/.test(password) ||
        !/[a-z]/.test(password) || !/[^A-Za-z0-9]/.test(password)) {
      setMessage(
        'Password must be at least 9 characters and contain uppercase, lowercase and a special character.'
      )
      return
    }

    setLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:8000/auth/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, password }),
      })

      const data = await response.json()

      if (!response.ok) {
        const errorMessage =
          typeof data.detail === 'string'
            ? data.detail
            : JSON.stringify(data.detail || 'Signup failed.')

        throw new Error(errorMessage)
      }

      setMessage('Account created successfully! You can now sign in.')
      setName('')
      setEmail('')
      setPassword('')
      setConfirmPassword('')
    } catch (error) {
      setMessage(error.message || 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-glow auth-glow-one"></div>
      <div className="auth-glow auth-glow-two"></div>

      <div className="auth-card">
        <div className="auth-logo">S</div>

        <p className="auth-brand">SUBSENTRY AI</p>
        <h1>Create account</h1>
        <p className="auth-subtitle">
          Start managing your subscriptions smarter.
        </p>

        <form onSubmit={handleSignup}>
          <label htmlFor="name">Full name</label>
          <input
            id="name"
            type="text"
            placeholder="Enter your full name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            minLength={2}
            maxLength={100}
            required
          />

          <label htmlFor="email">Email address</label>
          <input
            id="email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label htmlFor="signup-password">Password</label>
          <div className="password-input">
            <input
              id="signup-password"
              type={showPassword ? 'text' : 'password'}
              placeholder="Create a strong password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={9}
              required
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? 'Hide' : 'Show'}
            </button>
         
          </div>

          <div className="password-rules">
            {passwordRules.map((rule, index) => (
              <p
                key={index}
                className={rule.valid ? 'rule-valid' : 'rule-invalid'}
              >
                <span>{rule.valid ? '✓' : '○'}</span>
                {rule.label}
              </p>
            ))}
          </div>

          <label htmlFor="confirm-password">Confirm password</label>

          <input
            id="confirm-password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Re-enter your password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            minLength={9}
            required
          />

          <button className="auth-submit" type="submit" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        {message && (
          <p className="auth-message" role="status">{message}</p>
        )}

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}

export default Signup
