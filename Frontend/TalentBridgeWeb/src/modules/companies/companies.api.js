import { request } from '../../services/api/http'

export const companiesApi = {
  create: (payload) => request('/v1/companies', { method: 'POST', body: JSON.stringify(payload) }),
  get: (companyId) => request(`/v1/companies/${companyId}`),
  update: (companyId, payload) => request(`/v1/companies/${companyId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
}
