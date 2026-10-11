// Login tokens are kept in localStorage so a page reload keeps you signed in.
// Every access is wrapped in try/catch because storage can be blocked (private mode).
const ACCESS_KEY = 'access_token'
const REFRESH_KEY = 'refresh_token'

function read(key){
    try{
        return localStorage.getItem(key)
    }
    catch{
        return null
    }
}

export const tokenStore = {
    getAccess: () => read(ACCESS_KEY),
    getRefresh: () => read(REFRESH_KEY),

    // `tokens` is the backend's TokenResponse : { access_token, refresh_token }
    save(tokens){
        try{
            localStorage.setItem(ACCESS_KEY,tokens.access_token)
            localStorage.setItem(REFRESH_KEY,tokens.refresh_token)
        }
        catch{
            // storage blocked - user stays signed in only until the tab closes
        }
    },

    clear(){
        try{
            localStorage.removeItem(ACCESS_KEY)
            localStorage.removeItem(REFRESH_KEY)
        }catch{
            // nothing stored, nothing to clear
        }
    },
}