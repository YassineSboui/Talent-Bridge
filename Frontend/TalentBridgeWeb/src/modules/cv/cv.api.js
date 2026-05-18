import { request } from '../../services/api/http'

export const cvApi = {
  mine: () => request('/v1/cv/my'),
  upload: (file) => {
    const data = new FormData()
    data.append('file', file)
    return request('/v1/cv/upload', { method: 'POST', body: data })
  },
}
