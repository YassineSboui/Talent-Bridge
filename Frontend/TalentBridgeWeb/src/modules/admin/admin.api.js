import { request } from '../../services/api/http'

export const adminApi = {
  dashboard: () => request('/v1/admin/dashboard'),
  aiJobs: () => request('/v1/admin/ai-jobs'),
  auditLogs: () => request('/v1/admin/audit-logs'),
  users: () => request('/v1/admin/users'),
  companies: () => request('/v1/admin/companies'),
  jobs: () => request('/v1/admin/jobs'),
  powerbi: () => request('/v1/admin/powerbi'),
  retryAiJob: (id) => request(`/v1/admin/ai-jobs/${id}/retry`, { method: 'POST' }),
  resetDemoData: () => request('/v1/admin/reset-demo-data', { method: 'POST' }),
}
