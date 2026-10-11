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

    // { email, password} -> {access_token, refresh_token, token_type }
    login : (body) => api.post('/auth/login', body).then((res)=> res.data),

    // { email } -> { message } (same message whether or not the email exists)
    forgotPassword: (body) => api.post('/auth/forgot-password',body).then((res) => res.data),

    // { email, otp_code, new_password } -> { message }
    resetPassword: (body) => api.post('/auth/reset-password',body).then((res) => res.data),

    // Revokes the refresh token on the server 
    logout : (refreshToken) => api.post('/auth/logout', {refresh_token: refreshToken}).then((res) => res.data),

    // The signed-in user: { id, name, email, mobile, role, is_active, ...}
    me: () => api.get('/users/me').then((res)=> res.data),

    // Google sign-in is a full page redirect, not an API call 
    googleLoginUrl : `${import.meta.env.VITE_API_URL}/auth/google/login`,


}