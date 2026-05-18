import { request } from '../../services/api/http'

export const authApi = {
  login: (payload) => request('/v1/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  register: (payload) => request('/v1/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  me: () => request('/v1/auth/me'),
}
