import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { getErrorMessage } from '../../api/client'
import { useAuth } from '../../auth/context'
import Alert from '../../components/Alert'

// The backend's Google callback sends the browser to /oauth-success#token=...&refresh=...

function readTokensFromHash() {
    const params = new URLSearchParams(window.location.hash.slice(1))
    const access = params.get('token')
    const refresh = params.get('refresh')
    return access && refresh ? {access_token: access, refresh_token: refresh }: null    
}

export default function OAuthSuccessPage() {
    const { loginWithTokens } = useAuth()
    // Read once, before the effect below wipes the address bar
    const [tokens] = useState(readTokensFromHash)
    const [error, setError] = useState(tokens ? '' : "Google sign-in didn't finish. Please try again.")

    useEffect(()=> {
      // Remove the tokens from the address bar and browser history straight away
      window.history.replaceState(null, '', window.location.pathname)
      if(!tokens) return  

      let cancelled = false 
      // On success the RequireGuest gatekeeper sends the user into the app
      loginWithTokens(tokens).catch((err)=> {
        if (!cancelled) setError(getErrorMessage(err))
      })
    return ()=> {
        cancelled = true 
    }
    // Run once: loginWithTokens changes on every render of AuthProvider
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [tokens])
    
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