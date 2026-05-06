import { request } from '../../services/api/http'

export const candidatesApi = {
  search: () => request('/v1/candidates'),
}
