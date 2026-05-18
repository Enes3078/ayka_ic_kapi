import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useTaskStore = defineStore('tasks', () => {
  const tasks = ref([])
  const currentTask = ref(null)
  const teams = ref([])
  const loading = ref(false)
  const totalCount = ref(0)

  async function fetchTasks(params = {}) {
    loading.value = true
    try {
      const res = await api.get('/tasks/tasks/', { params })
      tasks.value = res.data.results || res.data
      totalCount.value = res.data.count || tasks.value.length
    } finally {
      loading.value = false
    }
  }

  async function fetchTask(id) {
    const res = await api.get(`/tasks/tasks/${id}/`)
    currentTask.value = res.data
    return res.data
  }

  async function createTask(data) {
    const res = await api.post('/tasks/tasks/', data)
    await fetchTasks()
    return res.data
  }

  async function updateTask(id, data) {
    const res = await api.put(`/tasks/tasks/${id}/`, data)
    await fetchTasks()
    return res.data
  }

  async function deleteTask(id) {
    await api.delete(`/tasks/tasks/${id}/`)
    await fetchTasks()
  }

  async function changeStatus(id, status) {
    const res = await api.post(`/tasks/tasks/${id}/change-status/`, { status })
    await fetchTasks()
    return res.data
  }

  async function importExcel(file) {
    const formData = new FormData()
    formData.append('file', file)
    const res = await api.post('/tasks/import-excel/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  }

  async function fetchTeams() {
    const res = await api.get('/tasks/teams/')
    teams.value = res.data.results || res.data
    return teams.value
  }

  return {
    tasks, currentTask, teams, loading, totalCount,
    fetchTasks, fetchTask, createTask, updateTask,
    deleteTask, changeStatus, importExcel, fetchTeams,
  }
})
