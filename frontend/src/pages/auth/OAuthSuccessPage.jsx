import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import { authApi } from '../../api/auth'
import { getErrorMessage } from '../../api/client'
import { useAuth } from '../../auth/context'
import Alert from '../../components/Alert'

// The backend's Google callback sends the browser to /oauth-success#code=<one-time code>
// (or #error=blocked when an admin has blocked the account). The code is traded for
// tokens once, within 60 seconds of signing in; after that it is useless.

function readHash() {
    const params = new URLSearchParams(window.location.hash.slice(1))
    return { code: params.get('code'), problem: params.get('error') }
}

export default function OAuthSuccessPage() {
    const { loginWithTokens } = useAuth()
    // Read once, before the effect below wipes the address bar
    const [{ code, problem }] = useState(readHash)
    const [error, setError] = useState(() => {
        if (code) return ''
        if (problem === 'blocked') {
            return 'This account has been blocked. Contact the admin if you think this is a mistake.'
        }
        return "Google sign-in didn't finish. Please try again."
    })
    // React runs effects twice in development, but the code works only once: trade it once
    const exchange = useRef(null)

    useEffect(()=> {
      // Remove the code from the address bar and browser history straight away
      window.history.replaceState(null, '', window.location.pathname)
      if(!code) return

      let cancelled = false
      // On success the RequireGuest gatekeeper sends the user into the app
      exchange.current ??= authApi.googleExchange(code).then(loginWithTokens)
      exchange.current.catch((err)=> {
        if (!cancelled) setError(getErrorMessage(err))
      })
    return ()=> {
        cancelled = true
    }
    // Run once: loginWithTokens changes on every render of AuthProvider
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [code])

    if(error){
        return (
            <>
                <h2 className="font-display text-[26px] font-bold text-brand-ink">Couldn't sign you in</h2>
                <Alert>{error}</Alert>
                <Link to="/login" className="text-center font-semibold text-link hover:underline">
                ← Back to sign in
                </Link>
            </>
        )
    }

    return (
        <div className="flex items-center gap-3 text-muted" role="status">
        <span className="size-5 animate-spin rounded-full border-2 border-primary border-r-transparent" />
        Signing you in with Google…
        </div>
    )
}
