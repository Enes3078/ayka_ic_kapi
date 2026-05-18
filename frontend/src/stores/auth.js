import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user_data') || 'null'))
  const isAuthenticated = computed(() => !!localStorage.getItem('access_token'))

  async function login(username, password) {
    const res = await api.post('/auth/login/', { username, password })
    localStorage.setItem('access_token', res.data.access)
    localStorage.setItem('refresh_token', res.data.refresh)
    localStorage.setItem('user_data', JSON.stringify(res.data.user))
    user.value = res.data.user
    return res.data
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_data')
    user.value = null
    window.location.href = '/login'
  }

  async function fetchMe() {
    try {
      const res = await api.get('/auth/me/')
      user.value = res.data
      localStorage.setItem('user_data', JSON.stringify(res.data))
    } catch {
      logout()
    }
  }

  const isAdmin = computed(() => user.value?.role === 'admin')
  const isManager = computed(() => user.value?.role === 'manager')
  const isAdminOrManager = computed(() => ['admin', 'manager'].includes(user.value?.role))

  return { user, isAuthenticated, login, logout, fetchMe, isAdmin, isManager, isAdminOrManager }
})
