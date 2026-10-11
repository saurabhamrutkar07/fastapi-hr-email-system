import { createContext, useContext } from "react";

// Holds { user, status, login, loginWithTokens. logout } - filled in by <AuthProvider>
export const AuthContext = createContext(null)

// Use inside any component: const {user, logout } = useAuth()
export function useAuth() {
    const value = useContext(AuthContext)
    if (!value) throw new Error('useAuth must be used inside <AuthProvider>')
    return value
}

