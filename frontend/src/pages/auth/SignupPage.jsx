import { useEffect, useState } from "react";
import { Link } from "react-router";
import { authApi } from "../../api/auth";
import { getErrorMessage } from "../../api/client";
import { useAuth } from "../../auth/context";
import Alert from "../../components/Alert";
import Button from "../../components/Button";
import Field from "../../components/Field";
import GoogleIcon from "../../components/GoogleIcon";
import Input from "../../components/Input";
import OtpInput from "../../components/OtpInput";
import PasswordInput from "../../components/PasswordInput";

const RESEND_SECONDS = 30
const STRENGTH = [
    {label: 'Use 8+ characters with a number and a symbol.', color: 'bg-line'},
    {label: 'Weak', color: 'bg-err'},
    {label: 'Okay', color: 'bg-warn'},
    {label: 'Strong', color: 'bg-ok'},
    {label: 'Very strong', color: 'bg-ok'},

    ]
    // 0-4: one point each for length 8+, a digit, a symbol, and 12+ characters with a capital
    function passwordScore(password){
        let score = 0
        if (password.length >= 8) score++
        if (/\d/.test(password)) score++
        if (/[^A-Za-z0-9]/.test(password)) score++
        if (password.length >= 12 && /[A-Z]/.test(password)) score++
        return score
    }


/*
    Sign up in three steps, all on one page:
    1. name, email, mobile  -> POST /auth/signup       (emails a 6-digit code)
    2. the code             -> POST /auth/verify-otp   (returns signup_token)
    3. password             -> POST /auth/set-password (needs signup_token), then sign in
*/
export default function SignupPage(){
    const { login } = useAuth()
    const [step, setStep] = useState(1)

    const [name, setName] = useState('')
    const [email, setEmail] = useState('')
    const [mobile, setMobile] = useState('')
    const [otp, setOtp] = useState('')
    const [signupToken , setSignUpToken] = useState('')
    const [password, setPassword] = useState('')
    const [confirm, setConfirm] = useState('')

    const [fieldErrors, setFieldErrors] = useState({})
    const [error, setError] = useState('')
    const [notice, setNotice] = useState('') 
    const [loading, setLoading] = useState(false) 
    const [resendIn, setResendIn] = useState(0) 
    
    // Count down once a second until "Resend code" is allowed again

    useEffect(()=> {
        if (resendIn <= 0) return
        const timer = setTimeout(()=> setResendIn(resendIn - 1),1000)
        return ()=> clearTimeout(timer)
    }, [resendIn])

    // Runs a backend call with the loading spinner and error box handled in one place
    async function run(action) {
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
    function edit(setValue,field){
        return(event)=>{
            setValue(event.target.value)
            setFieldErrors((prev)=> ({...prev, [field]: undefined}))
        }
    }

    // The backend accepts 10-15 characters; we send digits only
    const mobileDigits = mobile.replace(/[\s-]/g,'')

    async function sendCode() {
        await authApi.signup({name: name.trim(), email: email.trim(), mobile: mobileDigits})
        setResendIn(RESEND_SECONDS)
    }

    // Step 1
    function handleDetails(event){
        event.preventDefault()
        const errors = {}
        if (!name.trim()) errors.name = 'Enter your name.'
        if (!email.trim()) errors.email = 'Enter your email address.'
        else if (!/^\S+@\S+\.\S+$/.test(email)) errors.email = 'Enter a valid email address, like name@example.com.'
        if (!/^\+?\d+$/.test(mobileDigits) || mobileDigits.length < 10 || mobileDigits.length > 15) errors.mobile = 'Enter a mobile number with 10 to 15 digits.'
        setFieldErrors(errors)
        if (Object.keys(errors).length > 0) return

        run(async () => {
            await sendCode()
            setOtp('')
            setStep(2)
        })
    }

    // Step 2 
    function handleCode(event){
        event.preventDefault()
        if (otp.length !== 6){
            setFieldErrors({otp: 'Enter the 6-digit code from the email.'})
            return
        }
        setFieldErrors({})

        run(async ()=> {
            const result = await authApi.verifyOtp({ email: email.trim(), otp_code: otp})
            setSignUpToken(result.signup_token)
            setStep(3)
        })
    }

    function handleResend(){
        run(async ()=> {
            await sendCode()
            setOtp('')
            setNotice(`We sent a new code to ${email.trim()}.`)
        })
    }

    // Step 3
    function handlePassword(event){
        event.preventDefault()
        const errors = {}
        if(password.length < 8) errors.password = 'Use at least 8 characters.'
        if(confirm !== password) errors.confirm = 'The passwords do not match.'
        setFieldErrors(errors)
        if (Object.keys(errors).length > 0) return

        run(async ()=> {
            await authApi.setPassword({email: email.trim(),signup_token: signupToken , password})
            // Signed in -> the RequireGuest gatekeeper  sends the user into the app
            await login(email.trim(), password)
        })
    }

    function startOver(){
        setStep(1)
        setFieldErrors({})
        setError('')
        setNotice('')
    }

    const score = passwordScore(password)

    return(
        <>
         <div className="flex items-center gap-1.5 text-[12.5] font-semibold text-muted">
            {[1,2,3].map((n)=> (
                <span key ={n} className={`h-1 flex-1 rounded-full ${n <= step ? 'bg-primary' : 'bg-line'}`}/>
            ))}

            <span className="ml-1.5" >Step {step}</span>
         </div>

         {step === 1 && (
            <>
                <div>
                    <h2 className="font-display text-[26px] font-bold text-brand-ink">Create your account</h2>
                    <p className="mt-1 text-muted">We'll send a code to verify your email.</p>
                </div>

                <form onSubmit={handleDetails} noValidate className="flex flex-col gap-4">
                    <Alert>{error}</Alert>
                    <Field id = "name" label="Full name" error={fieldErrors.name}>
                        <Input
                            id="name"
                            autoComplete="name"
                            aria-invalid={Boolean(fieldErrors.name)}
                            value={name}
                            onChange={edit(setName, 'name')}
                        /> 
                    </Field>
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
                    <Field
                    id="mobile"
                    label="Mobile"
                    hint="10 to 15 digits. Shown on the emails you send, never verified."
                    error={fieldErrors.mobile}
                    >
                    <Input
                        id="mobile"
                        type="tel"
                        autoComplete="tel"
                        aria-invalid={Boolean(fieldErrors.mobile)}
                        value={mobile}
                        onChange={edit(setMobile, 'mobile')}
                    />
                    </Field>
                    <Button type="submit" loading={loading} className="w-full">
                    Send verification code
                    </Button>
                </form>

                <div className="flex items-center gap-3 text-[12.5px] text-muted before:flex-1 before:border-t before:border-line after:flex-1 after:border-t after:border-line">
                    or
                </div>
                <a
                    href={authApi.googleLoginUrl}
                    className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-line bg-surface px-4 py-2.5 font-semibold hover:bg-surface-2"
                >
                    <GoogleIcon />
                    Sign up with Google
                </a>
                <p className="text-center text-muted">
                    Already have an account?{' '}
                    <Link to="/login" className="font-semibold text-link hover:underline">
                    Sign in
                    </Link>
                </p>
            </>
         )}

         {step == 2 && (
            <>
                <div>
                    <h2 className="font-display text-[26px] font-bold text-brand-ink">Check your email</h2>
                    <p className="mt-1 text-muted">
                    Enter the 6-digit code we sent to <b className="text-fg">{email.trim()}</b>. It expires in 10 minutes.
                    </p>
                </div>

                <form onSubmit={handleCode} noValidate className="flex flex-col gap-4">
                    <Alert>{error}</Alert>
                    <Alert tone="success">{notice}</Alert>
                    <Field id="otp" label="Verification code" error={fieldErrors.otp}>
                    <OtpInput
                        id="otp"
                        value={otp}
                        onChange={(value) => {
                        setOtp(value)
                        setFieldErrors({})
                        }}
                        invalid={Boolean(fieldErrors.otp)}
                        autoFocus
                    />
                    </Field>
                    <div className="flex flex-wrap items-center justify-between gap-2 text-[13px]">
                    <button type="button" onClick={startOver} className="font-semibold text-link hover:underline">
                        Wrong email? Change it
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
                    <Button type="submit" loading={loading} className="w-full">
                    Verify email
                    </Button>
                </form>
            </>
         )}

         {step === 3 && (
                <>
                <div>
                    <h2 className="font-display text-[26px] font-bold text-brand-ink">Set a password</h2>
                    <p className="mt-1 text-muted">Your email is verified. One last step.</p>
                </div>

                <form onSubmit={handlePassword} noValidate className="flex flex-col gap-4">
                    <Alert>{error}</Alert>
                    <Field id="password" label="Password" error={fieldErrors.password}>
                    <PasswordInput
                        id="password"
                        autoComplete="new-password"
                        aria-invalid={Boolean(fieldErrors.password)}
                        value={password}
                        onChange={edit(setPassword, 'password')}
                    />
                    </Field>
                    <div className="-mt-2 flex flex-col gap-1.5">
                    <div className="flex gap-1">
                        {[1, 2, 3, 4].map((n) => (
                        <span key={n} className={`h-1 flex-1 rounded-full ${n <= score ? STRENGTH[score].color : 'bg-line'}`} />
                        ))}
                    </div>
                    <p className="text-xs text-muted">{STRENGTH[score].label}</p>
                    </div>
                    <Field id="confirm" label="Confirm password" error={fieldErrors.confirm}>
                    <PasswordInput
                        id="confirm"
                        autoComplete="new-password"
                        aria-invalid={Boolean(fieldErrors.confirm)}
                        value={confirm}
                        onChange={edit(setConfirm, 'confirm')}
                    />
                    </Field>
                    <Button type="submit" loading={loading} className="w-full">
                    Create account
                    </Button>
                    {error && (
                    <button type="button" onClick={startOver} className="text-[13px] font-semibold text-link hover:underline">
                        Start over with a new code
                    </button>
                    )}
                </form>
                </>
            )}
        </>
    
    )
}