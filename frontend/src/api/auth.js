import { api } from "./client";

// One function per backend auth endpoint. Each returns the response body.
// Request/response shapes match app/schemas/auth.py.
export const authApi = {
    // {name, email, mobile} -> {user_id, message}
    // Calling it again for an unfinished signup sends a fresh OTP ("Resend code")
    signup: (body) => api.post('/auth/signup',body).then((res)=> res.data),

    // { email,otp_code } -> { message, signup_token }
    verifyOtp: (body) => api.post('/auth/verify-otp', body).then((res) => res.data),

    // { email, signup_token, password } -> { message }
    setPassword: (body) => api.post('/auth/set-password', body).then((res) => res.data),

    // { email, password} -> {access_token, token_type }; the refresh token arrives as an httpOnly cookie
    login : (body) => api.post('/auth/login', body).then((res)=> res.data),

    // Uses the refresh-token cookie -> { access_token, token_type }. 401 when not signed in
    refresh: () => api.post('/auth/refresh').then((res) => res.data), 

    // The one-time code from /oauth-success#code=... ->{ access_token, token_type } + the cookie 
    googleExchange : (code) => api.post('/auth/google/exchange', { code }).then((res)=> res.data),

    // { email } -> { message } (same message whether or not the email exists)
    forgotPassword: (body) => api.post('/auth/forgot-password',body).then((res) => res.data),

    // { email, otp_code, new_password } -> { message }
    resetPassword: (body) => api.post('/auth/reset-password',body).then((res) => res.data),

    // Revokes the refresh-token cookie on the server and deletes it
    logout : () => api.post('/auth/logout').then((res) => res.data),

    // The signed-in user: { id, name, email, mobile, role, is_active, ...}
    me: () => api.get('/users/me').then((res)=> res.data),

    // Google sign-in is a full page redirect, not an API call 
    googleLoginUrl : `${import.meta.env.VITE_API_URL}/auth/google/login`,


}