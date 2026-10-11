import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { authApi } from "../../api/auth";
import { getErrorMessage } from "../../api/client";
import { useAuth } from "../../auth/context";
import Alert from "../../components/Alert";
import Button from "../../components/Button";
import Field from "../../components/Field";
import GoogleIcon from "../../components/GoogleIcon";
import Input from "../../components/Input";
import PasswordInput from "../../components/PasswordInput";


export default function LoginPage(){
    const { login } = useAuth()
    const navigate = useNavigate()

    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [fieldErrors, setFieldErrors] = useState({})

    // checks the form before calling the backend. Returns {email?: msg, password?: msg}
    function validate(){
        const errors = {}
        if (!email.trim()) errors.email = 'Enter your email address.'
        else if (!/^\S+@\S+\.\S+$/.test(email)) errors.email = 'Enter a valid email address, like name@example.com.'
        if (!password) errors.password = 'Enter your password.'
        return errors
    }
    
    async function handleSubmit(event) {
        event.preventDefault() // stop the browser from reloading the page 
        const errors = validate()
        setFieldErrors(errors)
        if (Object.keys(errors).length > 0) return
        setError('')
        setLoading(true)
        try{
            await login(email,password)
            navigate('/', {replace:true})
        }catch(err){
            setError(getErrorMessage(err))
            setLoading(false)
        }
    }

    return(
        <>
        <div>
        <h2 className="font-display text-[26px] font-bold text-brand-ink">Welcome back</h2>
        <p className="mt-1 text-muted">Sign in to continue your outreach.</p>
      </div>

      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        <Alert>{error}</Alert>

        <Field id="email" label="Email" error={fieldErrors.email}>
            <Input 
            id= "email"
            type="email"
            autoComplete="email"
            required
            aria-invalid = {Boolean(fieldErrors.email)}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            />
        </Field>
        <Field id='password' label="Password" error={fieldErrors.password}>
            <PasswordInput 
            id="password"
            autoComplete="current-password"
            required
            aria-invalid={Boolean(fieldErrors.password)}
            value={password}
            onChange={(e)=> setPassword(e.target.value)}
            />
        </Field>

        <div className="flex justify-end">
                <Link to="/forgot-password" className="text-[13px] font-semibold text-link hover:underline">
                    Forgot password?
                </Link>
            </div>
            <Button type="submit" loading={loading} className="w-full">
                Sign in
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
        Continue with Google
      </a>

      <p className="text-center text-muted">
        New to ColdReach?{' '}
        <Link to="/signup" className="font-semibold text-link hover:underline">
          Create an account
        </Link>
      </p>

      </>
    )

}