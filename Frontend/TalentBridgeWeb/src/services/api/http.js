import { authStore } from '../../stores/authStore'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export async function request(path, options = {}) {
  const headers = new Headers(options.headers || {})
  if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (authStore.token) headers.set('Authorization', `Bearer ${authStore.token}`)
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(payload.detail || `Request failed: ${response.status}`)
  return payload
}
