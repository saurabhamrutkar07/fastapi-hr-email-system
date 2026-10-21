import { api } from "./client";
import { dashboardApi } from './dashboard'

// Everything the Settings page reads and saves 
export const settingsApi = {
    // { name , mobile } -> the updated user (same shape as GET /users/me)
    updateProfile: (body) => api.patch('/users/me', body).then((res) => res.data),

    // { smtp_server, smtp_port, email_address, is_active }, or null when Gmail isn't connected yet
    smtp : dashboardApi.smtp, 

    // { email_address, password } -> saved settings. The backend logs in to Gmail first (400 if rejected)
    saveSmtp: (body) => api.post('/smtp-credentials/', body).then((res) => res.data),

    // Sends a test email from the saved Gmail to itself -> { message }
    testSmtp: () => api.post('/smtp-credentials/test').then((res) => res.data),
}