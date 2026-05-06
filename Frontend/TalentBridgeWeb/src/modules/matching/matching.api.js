import { request } from '../../services/api/http'

export const matchingApi = {
  candidateJobs: () => request('/v1/matching/candidates/me/jobs'),
  jobCandidates: (jobId) => request(`/v1/matching/jobs/${jobId}/candidates`, { method: 'POST' }),
}
