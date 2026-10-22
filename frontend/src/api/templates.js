import { api } from './client'

// The user's own email templates. Each returns the response body.
export const templatesApi = {
  // [{ id, name, subject, content, is_default }]
  list: () => api.get('/email-template/').then((res) => res.data),

  // { name, subject, content, is_default } -> the new template. The first template becomes the default.
  // 400 with "Template error on line N: ..." when the template can't be filled in
  create: (body) => api.post('/email-template/', body).then((res) => res.data),

  // { name, subject, content } -> the updated template
  update: (id, body) => api.put(`/email-template/${id}`, body).then((res) => res.data),

  // 400 for the default template: another one must be made the default first
  remove: (id) => api.delete(`/email-template/${id}`).then((res) => res.data),

  setDefault: (id) => api.post(`/email-template/${id}/set-default`).then((res) => res.data),

  // { subject, content } -> { subject, body } filled in for a sample recruiter (Priya Sharma, Zoho)
  preview: (body) => api.post('/email-template/preview', body).then((res) => res.data),
}
