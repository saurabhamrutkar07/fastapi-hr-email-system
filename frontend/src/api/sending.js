import { api } from './client'

// The user's saved "about me" details for emails. Each returns the response body.
export const senderProfilesApi = {
  // Default first: [{ id, name, job_position, experience_years, skills: [..], linkedin_url, is_default }]
  list: () => api.get('/sender-profiles/').then((res) => res.data),

  // { name, job_position, experience_years, skills, linkedin_url, is_default } -> the new set.
  // The first set becomes the default.
  create: (body) => api.post('/sender-profiles/', body).then((res) => res.data),

  update: (id, body) => api.put(`/sender-profiles/${id}`, body).then((res) => res.data),

  // 400 for the default set: another one must be made the default first
  remove: (id) => api.delete(`/sender-profiles/${id}`).then((res) => res.data),

  setDefault: (id) => api.post(`/sender-profiles/${id}/set-default`).then((res) => res.data),
}

// Admins only: while on, the admin's sends may only go to their test emails
export const testModeApi = {
  // { enabled, test_emails: [..] }
  get: () => api.get('/test-mode/').then((res) => res.data),
  update: (body) => api.put('/test-mode/', body).then((res) => res.data),
}

export const sendApi = {
  // { contact_id, template_id, sender_profile_id } -> { to_name, to_email, company, subject, body, attachment_name }
  preview: (body) => api.post('/email/preview', body).then((res) => res.data),

  // { contact_ids (up to 50), template_id, sender_profile_id } -> { total, test_mode, items: [{ contact_id, name, email, request_id }] }
  send: (body) => api.post('/email/send', body).then((res) => res.data),

  // [request ids] -> [{ request_id, status: PENDING | SUCCESS | FAILED, error_code, response_details }]
  status: (requestIds) =>
    api.get('/email/status', { params: { request_ids: requestIds.join(',') } }).then((res) => res.data),

  // { 'hr@company.com': '2026-10-25' }: the day each address was last emailed successfully
  lastSent: () => api.get('/email/last-sent').then((res) => res.data),
}
