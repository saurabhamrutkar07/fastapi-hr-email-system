import axios from 'axios'
import { tokenStore } from './tokens' 

const API_URL = import.meta.env.VITE_API_URL

// every backend call goes through this instance
export const api = axios.create({baseURL:API_URL,timeout:20000})

//1. Before each request: attach the access token if we have one
api.interceptors.request.use((config) => {
    const token = tokenStore.getAccess()
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

// Shared between requests: if three calls get 401 at the same moment,
// they all wait for ONE refresh insted of sending three.
let refreshPromise = null 


async function refreshAccessToken() {
    const refreshToken = tokenStore.getRefresh()
    if (!refreshToken) throw new Error('No refresh token')
    
    //Plain axios (not `api`) so this call can't loop back into the interceotir below
    const {data} = await axios.post(`${API_URL}/auth/refresh`, { refresh_token: refreshToken })
    tokenStore.save(data)
    return data.access_token
}

// 2. After each response: on 401, refresh the access token once and retry 
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const original = error.config
        const status = error.response?.status
        // A 401 from /auth/* means wrong password or bad token - refreshing won't help 
        const isAuthCall = original?.url?.startsWith('/auth/') 

        if (status !== 401 || isAuthCall || original._retried){
            throw error
        }
        
        original._retried = true 
        try {
            refreshPromise ??= refreshAccessToken().finally(() => {
                refreshPromise = null 
            })
            const newToken = await refreshPromise
            original.headers.Authorization = `Bearer ${newToken}`
            return api(original)
        } catch{
            // Refresh token expired or revoked: sign the user out everywhere in the app
            tokenStore.clear()
            window.dispatchEvent(new Event('auth:logout'))
            throw error
        }
    },
)

// Turns any backend or network error into one sentence we can show in the UI
export function getErrorMessage(error){
    if (!error.response){
        return 'Cannot reach the server. Check that the backend is running.'
    }

    const detail = error.response.data?.detail

    // HTTPException(detail="...") from Fastapi 
    if (typeof detail === 'string') return detail

    // HTTPException(detail={"message": "...", ...})
    if (typeof detail?.message === 'string') return detail.message

    // 422 validation error: [{ loc: ['body','email'], msg: 'value is not a valid email address'}]
    if (Array.isArray(detail) && detail.length > 0){
        const {loc, msg} = detail[0]
        const field =loc?.[loc.length - 1 ]
        return field ? `${field}: ${msg}` : msg
    }

    return 'Something went wrong. Please try again.'
}