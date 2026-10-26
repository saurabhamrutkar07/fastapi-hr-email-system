import { api } from './client'


// Every email the user has sent (admins: everyone's), newest first. Each returns the response body.
export const historyApi = {
    // { status: 'SUCCESS' | 'FAILED', q, days, limit, offset } -> { total, items: [{ request_id, recipient_email,
    //   status, error_code, created_at, contact_name, company, subject, sender_name }] }
    // Leave a filter out (undefined) to not filter by it.
    list: (params) => api.get('/email/history', { params }).then((res) => res.data),
    
    // One email with what it said: the list fields + { body, response_details, template_name, resume_version, sender_email }
    get: (requestId) => api.get(`/email/history/${requestId}`).then((res) => res.data),
}