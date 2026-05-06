import { request } from '../../services/api/http'

export const profilesApi = {
  candidate: () => request('/v1/candidates/me/profile'),
  updateCandidate: (payload) => request('/v1/candidates/me/profile', { method: 'PATCH', body: JSON.stringify(payload) }),
  recruiter: () => request('/v1/recruiters/me/profile'),
  updateRecruiter: (payload) => request('/v1/recruiters/me/profile', { method: 'PATCH', body: JSON.stringify(payload) }),
}
