import { api } from './client'

// Minutes this browser is ahead of UTC (India: 330). The backend uses it to decide which day an email belongs to.
const tzOffsetMinutes = () => -new Date().getTimezoneOffset()

// Everything the dashboard reads. Each returns the response body.
export const dashboardApi = {
  // { days, total, sent, failed, success_rate, contacts_total, daily: [{ date, sent, failed }] }
  stats: (days = 14) =>
    api.get('/email/stats', { params: { days, tz_offset_minutes: tzOffsetMinutes() } }).then((res) => res.data),

  // Newest first: [{ id, request_id, recipient_email, status, error_code, response_details, created_at }]
  recentSends: (limit = 5) => api.get('/email/transactions', { params: { limit } }).then((res) => res.data),

  // { smtp_server, smtp_port, email_address, is_active }, or null when the user hasn't set it up yet (backend 404)
  smtp: () =>
    api
      .get('/smtp-credentials/')
      .then((res) => res.data)
      .catch((err) => {
        if (err.response?.status === 404) return null
        throw err
      }),

  // [{ id, name, subject, content, is_default }]
  templates: () => api.get('/email-template/').then((res) => res.data),

  // [{ id, version_number, is_active, uploaded_at }], newest version first
  resumes: () => api.get('/resumes/').then((res) => res.data),
}
