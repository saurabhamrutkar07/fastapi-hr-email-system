import { Navigate, Outlet, useLocation } from "react-router";
import { useAuth } from "./context";

// "Gatekeepers" for routes. Each one either shows its child pages (<Outlet />)
// or sends the user somewhere else (<Navigate />).

// Shown for the moment it takes to check a saved token after a page reload

function CheckingSession(){
    return (
    <div className="grid min-h-dvh place-items-center bg-bg" role="status" aria-label="Loading">
        <span className="size-8 animate-spin rounded-full border-3 border-primary border-r-transparent" />
    </div> 
    )
}

// App pages: not signed in -> /login, remembering the page they wanted 


export function RequireAuth() {
    const { status } = useAuth()
    const location = useLocation()

    if (status === 'loading') return <CheckingSession/>
    if (status === 'signed-out') return <Navigate to="/login" replace state={{from: location}} />
    return <Outlet/>
}

// Sign in / sign up pages: already signed in -> back to the page they wanted (or the dashboard)
export function RequireGuest(){
    const { status } = useAuth()
    const location = useLocation()

    if (status === 'loading') return <CheckingSession/>
    if (status === 'signed-in') return <Navigate to={location.state?.from?.pathname ?? '/'} replace />
    return <Outlet/>
}

// Admin-only pages: everyone else goes to the dashboard
export function RequireAdmin(){
    const { user } = useAuth()

    if (user?.role !== 'admin') return <Navigate to="/" replace />
    return <Outlet/>

}


