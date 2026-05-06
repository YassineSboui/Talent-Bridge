import { request } from '../../services/api/http'

export const applicationsApi = {
  mine: () => request('/v1/applications/me'),
  recruiter: () => request('/v1/recruiter/applications'),
  detail: (applicationId) => request(`/v1/recruiter/applications/${applicationId}`),
  apply: (jobId, cvId) => request('/v1/applications', { method: 'POST', body: JSON.stringify({ job_id: jobId, cv_id: cvId }) }),
  updateStatus: (applicationId, status, note = '') => request(`/v1/recruiter/applications/${applicationId}/status`, { method: 'PUT', body: JSON.stringify({ status, note }) }),
  saveNote: (applicationId, note) => request(`/v1/recruiter/applications/${applicationId}/notes`, { method: 'PUT', body: JSON.stringify({ note }) }),
}
