import { request } from '../../services/api/http'

export const jobsApi = {
  list: (query = '') => request(`/v1/jobs${query ? `?${query}` : ''}`),
  create: (payload) => request('/v1/jobs', { method: 'POST', body: JSON.stringify(payload) }),
  update: (jobId, payload) => request(`/v1/jobs/${jobId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  publish: (jobId) => request(`/v1/jobs/${jobId}/publish`, { method: 'POST' }),
  close: (jobId) => request(`/v1/jobs/${jobId}/close`, { method: 'POST' }),
}
