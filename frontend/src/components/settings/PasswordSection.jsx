import { useEffect, useState } from 'react'
import { authApi } from '../../api/auth'
import { getErrorMessage } from '../../api/client'
import { useAuth } from '../../auth/context'
import Alert from '../Alert'
import Button from '../Button'
import Field from '../Field'
import OtpInput from '../OtpInput'
import PasswordInput from '../PasswordInput'
import Section from './Section'

const RESEND_SECONDS = 30

/*
    Change the ColdReach sign-in password (not the Gmail App Password) with an emailed code,
    the same backend steps as Forgot password:
      1. POST /auth/forgot-password  -> emails a 6-digit code to the user
      2. POST /auth/reset-password   -> code + new password
    Also lets people who signed up with Google set a password for the first time.
*/
export default function PasswordSection() {
  const { user } = useAuth()
  const [codeSent, setCodeSent] = useState(false)
  const [otp, setOtp] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [fieldErrors, setFieldErrors] = useState({})
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(false)
  const [resendIn, setResendIn] = useState(0)

  // Count down once a second until "Resend code" is allowed again
  useEffect(() => {
    if (resendIn <= 0) return
    const timer = setTimeout(() => setResendIn(resendIn - 1), 1000)
    return () => clearTimeout(timer)
  }, [resendIn])

  // Runs a backend call with the spinner and error box handled in one place
  async function run(action) {
    setError('')
    setNotice('')
    setLoading(true)
    try {
      await action()
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const edit = (setValue, field) => (value) => {
    setValue(value)
    setFieldErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  function sendCode() {
    run(async () => {
      await authApi.forgotPassword({ email: user.email })
      setCodeSent(true)
      setResendIn(RESEND_SECONDS)
      setNotice(`We sent a 6-digit code to ${user.email}.`)
    })
  }

  function cancel() {
    setCodeSent(false)
    setOtp('')
    setPassword('')
    setConfirm('')
    setFieldErrors({})
    setError('')
    setNotice('')
  }

  function validate() {
    const errors = {}
    if (otp.length !== 6) errors.otp = 'Enter the 6-digit code from the email.'
    if (password.length < 8) errors.password = 'Use at least 8 characters.'
    if (confirm !== password) errors.confirm = 'The passwords don’t match.'
    return errors
  }

  function handleSubmit(event) {
    event.preventDefault()
    const errors = validate()
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return
    run(async () => {
      await authApi.resetPassword({ email: user.email, otp_code: otp, new_password: password })
      cancel()
      setNotice('Password changed. Use the new one next time you sign in.')
    })
  }

  return (
    <Section title="Password" description="The password you sign in to ColdReach with.">
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4 px-4 py-4 sm:px-5">
        <Alert>{error}</Alert>
        <Alert tone="success">{notice}</Alert>

        {!codeSent ? (
          <>
            <p className="text-[13.5px] text-muted">
              To change your password we’ll email a 6-digit code to <b className="break-all text-fg">{user.email}</b>.
              Signed up with Google? This also sets your first password.
            </p>
            <div className="flex justify-end">
              <Button type="button" loading={loading} onClick={sendCode}>
                Email me a code
              </Button>
            </div>
          </>
        ) : (
          <>
            <Field id="password-otp" label="Code from the email" error={fieldErrors.otp}>
              <OtpInput id="password-otp" value={otp} onChange={edit(setOtp, 'otp')} invalid={Boolean(fieldErrors.otp)} autoFocus />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field id="password-new" label="New password" error={fieldErrors.password}>
                <PasswordInput
                  id="password-new"
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => edit(setPassword, 'password')(e.target.value)}
                  aria-invalid={Boolean(fieldErrors.password)}
                />
              </Field>
              <Field id="password-confirm" label="Confirm new password" error={fieldErrors.confirm}>
                <PasswordInput
                  id="password-confirm"
                  autoComplete="new-password"
                  value={confirm}
                  onChange={(e) => edit(setConfirm, 'confirm')(e.target.value)}
                  aria-invalid={Boolean(fieldErrors.confirm)}
                />
              </Field>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <button
                type="button"
                onClick={sendCode}
                disabled={resendIn > 0 || loading}
                className="text-[13px] font-semibold text-link hover:underline disabled:cursor-not-allowed disabled:text-muted disabled:no-underline"
              >
                {resendIn > 0 ? `Resend code in ${resendIn}s` : 'Resend code'}
              </button>
              <div className="flex gap-2">
                <Button type="button" variant="secondary" onClick={cancel}>
                  Cancel
                </Button>
                <Button type="submit" loading={loading}>
                  Change password
                </Button>
              </div>
            </div>
          </>
        )}
      </form>
    </Section>
  )
}
