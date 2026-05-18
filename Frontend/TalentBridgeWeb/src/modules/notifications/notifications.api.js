import { request } from '../../services/api/http'

export const notificationsApi = {
  list: () => request('/v1/notifications/my'),
  markRead: (notificationId) => request(`/v1/notifications/${notificationId}/read`, { method: 'PUT' }),
  readAll: () => request('/v1/notifications/read-all', { method: 'POST' }),
}
