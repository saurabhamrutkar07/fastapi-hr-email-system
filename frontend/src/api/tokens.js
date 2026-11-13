// The access token lives only in memory, so a script injected into the page can't
// read it from storage. A page reload forgets it, and AuthProvider asks /auth/refresh
// for a new one. The refresh token is an httpOnly cookie that JavaScript never sees.

let accessToken = null 

export const tokenStore = {
    getAccess: () => accessToken,

    // `tokens` is the backend's TokenResponse: { access_token, token_type }
    save(tokens){
        accessToken = tokens.access_token
    },

    clear() {
        accessToken = null 
    },

}

// Older versions kept both tokens in localStorage; remove anything left behind 
try{
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
}catch {
    // storage blocked (private mode): nothing was saved there 
}