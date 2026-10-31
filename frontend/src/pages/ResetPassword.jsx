
import { useState } from 'react'
import { Link } from 'react-router-dom'

function ResetPassword() {
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  const token = new URLSearchParams(window.location.search).get('token')

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

  const handleReset = async (e) => {
    e.preventDefault()
    setMessage('')

    if (!token) {
      setMessage('Invalid or missing reset link.')
      return
    }

    if (passwordRules.some((rule) => !rule.valid)) {
      setMessage('Please satisfy all password requirements.')
      return
    }

    if (password !== confirmPassword) {
      setMessage('Passwords do not match.')
      return
    }

    setLoading(true)

    try {
      const response = await fetch('http://127.0.0.1:8000/auth/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: token,
          new_password: password,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        const errorMessage =
          typeof data.detail === 'string'
            ? data.detail
            : JSON.stringify(data.detail || 'Password reset failed.')

        throw new Error(errorMessage)
      }

      setMessage('Your password has been reset successfully! You can now log in.')
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
        <h1>Reset password</h1>

        <p className="auth-subtitle">
          Create a strong new password for your account.
        </p>

        <form onSubmit={handleReset}>
          <label htmlFor="new-password">New password</label>

          <div className="password-input">
            <input
              id="new-password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your new password"
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

          <label htmlFor="confirm-password">Confirm new password</label>

          <input
            id="confirm-password"
            type={showPassword ? 'text' : 'password'}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Re-enter your new password"
            minLength={9}
            required
          />

          <button className="auth-submit" type="submit" disabled={loading}>
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
        </form>

        {message && (
          <p className="auth-message" role="status">{message}</p>
        )}

        <p className="auth-footer">
          Remember your password? <Link to="/login">Back to Login</Link>
        </p>
      </div>
    </div>
  )
}

export default ResetPassword
