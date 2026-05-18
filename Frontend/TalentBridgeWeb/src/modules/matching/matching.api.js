import { request } from '../../services/api/http'

export const matchingApi = {
  candidateJobs: () => request('/v1/matching/candidates/me/jobs'),
  jobCandidates: (jobId) => request(`/v1/matching/jobs/${jobId}/candidates`, { method: 'POST' }),
}

export const skillGapApi = {
  jobGap: (jobId) => request(`/v1/skill-gap/jobs/${jobId}`),
  topMissing: (limit = 10) => request(`/v1/skill-gap/top-missing?limit=${limit}`),
}
