import { api } from './client'

// The user's resume versions (PDFs kept in S3). Each returns the response body.
export const resumesApi = {
  // Newest first: [{ id, version_number, is_active, uploaded_at }]
  list: () => api.get('/resumes/').then((res) => res.data),

  // A PDF up to 5 MB -> the new version, which becomes the active one
  upload: (file) => {
    const body = new FormData()
    body.append('file', file)
    return api.post('/resumes/upload', body).then((res) => res.data)
  },

  setActive: (id) => api.post(`/resumes/${id}/set-active`).then((res) => res.data),

  // 400 for the active version: another one must be made active first
  remove: (id) => api.delete(`/resumes/${id}`).then((res) => res.data),

  // { url, expires_in } -> a private link that opens the PDF for 15 minutes
  viewUrl: (id) => api.get(`/resumes/${id}/view-url`).then((res) => res.data),
}
