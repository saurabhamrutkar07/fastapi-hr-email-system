import { useEffect, useState } from "react";
import { authApi } from "../api/auth";
import { tokenStore } from "../api/tokens";
import { AuthContext } from "./context";

/*
 Remember who is signed in, for the whole app.
 status: 'loading'    - a token saved earlier, asking the backend who it belongs to
         'signed-in'  - `user` is the response of GET /users/me
         'signed-out' - no answer
*/

export default function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [status, setStatus] = useState(() => (tokenStore.getAccess() ? 'loading' : 'signed-out'))

    // First loads: if a token was saved earlier, load the user it belongs to
    useEffect(() => {
        if (!tokenStore.getAccess()) return
        let cancelled = false

        authApi
            .me()
            .then((me) => {
                if (cancelled) return
                setUser(me)
                setStatus('signed-in')
            })
            .catch(() => {
                if (cancelled) return
                tokenStore.clear()
                setStatus('signed-out')
            })

        // React runs effects twice in development; ignore the first run's answer
        return () => {
            cancelled = true
        }
    }, [])

    // client.js fired 'auth:logout' when the refresh token is rejected
    useEffect(() => {
        function onForcedLogout() {
            setUser(null)
            setStatus('signed-out')
        }

        window.addEventListener('auth:logout', onForcedLogout)
        return () => window.removeEventListener('auth:logout', onForcedLogout)
    }, [])

    // Save tokens, then load the user they belong to (also used by Google sign-in)
    async function loginWithTokens(tokens) {
        tokenStore.save(tokens)
        try {
            const me = await authApi.me()
            setUser(me)
            setStatus('signed-in')
            return me
        } catch (error) {
            tokenStore.clear()
            throw error
        }
    }

    async function login(email, password) {
        const tokens = await authApi.login({ email, password })
        return loginWithTokens(tokens)
    }

    function logout() {
        const refreshToken = tokenStore.getRefresh()
        tokenStore.clear()
        setUser(null)
        setStatus('signed-out')
        // Ask the backend to revoke the refresh token; we are signed out locally either way
        if (refreshToken) authApi.logout(refreshToken).catch(() => {})
    }

    // After the user edits their profile, show the new name everywhere without reloading
    function updateUser(me) {
        setUser(me)
    }

    const value = { user, status, login, loginWithTokens, logout, updateUser };

    // Development only; lets you call auth.login(...) / auth.logout() from the browser console
    useEffect(() => {
        if (import.meta.env.DEV) window.auth = value
    })

    return <AuthContext value={value}>{children}</AuthContext>
}
