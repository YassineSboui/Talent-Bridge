import { reactive } from 'vue'

export const authStore = reactive({
  token: localStorage.getItem('talentbridge_token') || '',
  user: JSON.parse(localStorage.getItem('talentbridge_user') || 'null'),
  setSession(payload) {
    this.token = payload.access_token
    this.user = payload.user
    localStorage.setItem('talentbridge_token', this.token)
    localStorage.setItem('talentbridge_user', JSON.stringify(this.user))
  },
  logout() {
    this.token = ''
    this.user = null
    localStorage.removeItem('talentbridge_token')
    localStorage.removeItem('talentbridge_user')
  },
})
