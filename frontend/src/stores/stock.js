import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useStockStore = defineStore('stock', () => {
  const items = ref([])
  const history = ref([])
  const dashboardStats = ref(null)
  const loading = ref(false)

  async function fetchItems(params = {}) {
    loading.value = true
    try {
      const res = await api.get('/stock/items/', { params })
      items.value = res.data.results || res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchItem(id) {
    const res = await api.get(`/stock/items/${id}/`)
    return res.data
  }

  async function createItem(data) {
    const res = await api.post('/stock/items/', data)
    await fetchItems()
    return res.data
  }

  async function updateItem(id, data) {
    const res = await api.put(`/stock/items/${id}/`, data)
    await fetchItems()
    return res.data
  }

  async function deleteItem(id) {
    await api.delete(`/stock/items/${id}/`)
    await fetchItems()
  }

  async function stockEntry(id, quantity, notes = '') {
    const res = await api.post(`/stock/items/${id}/entry/`, { quantity, notes })
    await fetchItems()
    return res.data
  }

  async function stockExit(id, quantity, notes = '', usage_location = '') {
    const res = await api.post(`/stock/items/${id}/exit/`, { quantity, notes, usage_location })
    await fetchItems()
    return res.data
  }

  async function fetchHistory(params = {}) {
    const res = await api.get('/stock/history/', { params })
    history.value = res.data
  }

  async function fetchDashboard() {
    const res = await api.get('/stock/dashboard/')
    dashboardStats.value = res.data
  }

  return {
    items, history, dashboardStats, loading,
    fetchItems, fetchItem, createItem, updateItem, deleteItem,
    stockEntry, stockExit, fetchHistory, fetchDashboard
  }
})
