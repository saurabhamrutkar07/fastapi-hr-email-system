import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { authApi } from '../../api/auth'
import { getErrorMessage } from '../../api/client'
import { useAuth } from '../../auth/context'
import Alert from '../../components/Alert'
import Button from '../../components/Button'
import Field from '../../components/Field'
import Input from '../../components/Input'
import OtpInput from '../../components/OtpInput'
import PasswordInput from '../../components/PasswordInput'

const RESEND_SECONDS = 30

/*
  Reset a forgotten password in two steps:
    1. email                          -> POST /auth/forgot-password (emails a code if the account exists)
    2. code + new password            -> POST /auth/reset-password, then sign in
  The backend gives the same answer whether or not the email is registered,
  so this page never says "no account with this email".
*/


export default function ForgotPasswordPage(){
    const { login } = useAuth()
    const [step, setStep] = useState(1)

    const [email, setEmail] = useState('')
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

    // Runs a backend call with the loading spinner and error box handled in one place
    async function  run(action) {
        setError('')
        setNotice('')
        setLoading(true)
        try{
            await action()
        }catch(err){
            setError(getErrorMessage(err))
        }finally{
            setLoading(false)
        }
    }

    // onChange for a text box: store the new value and hide that box's error while the user fixes it
    function edit(setValue,field) {
        return (event) => {
            setValue(event.target.value)
            setFieldErrors((prev) => ({ ...prev, [field]: undefined}))
        }
    }

    async function sendCode() {
        await authApi.forgotPassword({ email: email.trim()})
        setResendIn(RESEND_SECONDS)
    }


    // Step 1 
    function handleEmail(event) {
        event.preventDefault()
        const errors = {}
        if (!email.trim()) errors.email = 'Enter your email address.'
        else if (!/^\S+@\S+\.\S+$/.test(email)) errors.email = 'Enter a valid email address, like name@example.com.'
        setFieldErrors(errors)
        if (Object.keys(errors).length > 0) return 
        
        run(async () => {
            await sendCode()
            setOtp('')
            setStep(2)
        })
    }

    function handleResend() {
        run(async () => {
            await sendCode()
            setOtp('')
            setNotice(`If ${email.trim()} has an account, a new code is on its way.`)
        })
        
    }
    // Step 2 
    function handleReset(event) {
        event.preventDefault()
        const errors = {}
        if (otp.length !== 6) errors.otp = 'Enter the 6-digit code from the email.'
        if (password.length < 8) errors.password = 'Use at least 8 characters.'
        if (confirm !== password) errors.confirm = 'The passwords do not match.'
        setFieldErrors(errors)
        if (Object.keys(errors).length > 0) return

        run(async () => {
            await authApi.resetPassword({ email: email.trim(), otp_code: otp, new_password: password})
            // Signed in -> the RequireGuest gatekeeper sends the user into the app
            await login(email.trim(),password)
        })
        
    }

    function changeEmail() {
        setStep(1)
        setFieldErrors({})
        setError('')
        setNotice('')
        
    }

    if (step === 1){
      return (
        <>
            <div>
            <h2 className="font-display text-[26px] font-bold text-brand-ink">Reset your password</h2>
            <p className="mt-1 text-muted">Enter your account email and we'll send you a 6-digit code.</p>
            </div>

            <form onSubmit={handleEmail} noValidate className="flex flex-col gap-4">
            <Alert>{error}</Alert>
            <Field id="email" label="Email" error={fieldErrors.email}>
                <Input
                id="email"
                type="email"
                autoComplete="email"
                aria-invalid={Boolean(fieldErrors.email)}
                value={email}
                onChange={edit(setEmail, 'email')}
                />
            </Field>
            <Button type="submit" loading={loading} className="w-full">
                Send code
            </Button>
            </form>

            <Link to="/login" className="text-center font-semibold text-link hover:underline">
            ← Back to sign in
            </Link>
        </>
        )  
    }

    return (
        <>
            <div>
                <h2 className="font-display text-[26px] font-bold text-brand-ink">Choose a new password</h2>
                <p className="mt-1 text-muted">
                If <b className="text-fg">{email.trim()}</b> has an account, we sent it a 6-digit code. It expires in 10
                minutes.
                </p>
            </div>

            <form onSubmit={handleReset} noValidate className="flex flex-col gap-4">
                <Alert>{error}</Alert>
                <Alert tone="success">{notice}</Alert>
                <Field id="otp" label="Code" error={fieldErrors.otp}>
                <OtpInput
                    id="otp"
                    value={otp}
                    onChange={(value) => {
                    setOtp(value)
                    setFieldErrors((prev) => ({ ...prev, otp: undefined }))
                    }}
                    invalid={Boolean(fieldErrors.otp)}
                    autoFocus
                />
                </Field>
                <div className="flex flex-wrap items-center justify-between gap-2 text-[13px]">
                <button type="button" onClick={changeEmail} className="font-semibold text-link hover:underline">
                    Use a different email
                </button>
                {resendIn > 0 ? (
                    <span className="text-muted">Resend code in {resendIn}s</span>
                ) : (
                    <button
                    type="button"
                    onClick={handleResend}
                    disabled={loading}
                    className="font-semibold text-link hover:underline disabled:opacity-60"
                    >
                    Resend code
                    </button>
                )}
                </div>
                <Field id="password" label="New password" error={fieldErrors.password}>
                <PasswordInput
                    id="password"
                    autoComplete="new-password"
                    aria-invalid={Boolean(fieldErrors.password)}
                    value={password}
                    onChange={edit(setPassword, 'password')}
                />
                </Field>
                <Field id="confirm" label="Confirm new password" error={fieldErrors.confirm}>
                <PasswordInput
                    id="confirm"
                    autoComplete="new-password"
                    aria-invalid={Boolean(fieldErrors.confirm)}
                    value={confirm}
                    onChange={edit(setConfirm, 'confirm')}
                />
                </Field>
                <Button type="submit" loading={loading} className="w-full">
                Reset password
                </Button>
            </form>
        </>

    )

}