<template>
  <div class="page-content">
    <div class="page-header">
      <h2 class="page-title">Saha Çalışan Takibi</h2>
      <div class="header-actions flex items-center gap-16">
        <span class="text-sm text-muted">
          Son güncellenme: <strong>{{ lastUpdated }}</strong>
        </span>
        <button class="btn btn-secondary btn-icon" @click="fetchData" :disabled="loading" title="Yenile">
          <span :class="{'animate-spin': loading}">🔄</span>
        </button>
      </div>
    </div>

    <!-- Özet İstatistikler -->
    <div class="stats-grid mb-24">
      <div class="stat-card">
        <div class="stat-label">Toplam Aktif Çalışan</div>
        <div class="stat-value">{{ totalWorkers }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Toplam Aktif Görev</div>
        <div class="stat-value text-accent">{{ totalTasks }}</div>
      </div>
    </div>

    <!-- Çalışan Tablosu -->
    <div class="card">
      <div v-if="loading && workers.length === 0" class="loading-container">
        <div class="spinner"></div>
      </div>
      <div v-else-if="workers.length === 0" class="empty-state">
        <div class="empty-state-icon">👷</div>
        <div class="empty-state-text">Şu an sahada aktif çalışan bulunmuyor.</div>
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Çalışan</th>
            <th>Departman</th>
            <th>Aktif Görevler</th>
            <th>Son Aktivite</th>
            <th>Son Devir (Handover)</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="worker in workers" :key="worker.id" :class="{'row-highlight': worker.is_recent_handover}">
            <td>
              <div class="flex items-center gap-12">
                <div class="avatar">{{ worker.name.charAt(0) }}</div>
                <div>
                  <router-link :to="`/worker-tracking/${worker.id}`" class="text-primary hover-underline" style="font-weight: 600; text-decoration: none;">
                    {{ worker.name }}
                  </router-link>
                  <div class="text-sm text-muted">{{ worker.username }}</div>
                </div>
              </div>
            </td>
            <td>
              <span class="badge badge-medium">{{ worker.department }}</span>
            </td>
            <td>
              <span class="badge" :class="worker.active_task_count > 0 ? 'badge-in-progress' : 'badge-todo'">
                {{ worker.active_task_count }} Görev
              </span>
            </td>
            <td class="text-muted">
              {{ formatRelativeTime(worker.last_activity) }}
            </td>
            <td>
              <div v-if="worker.last_handover">
                <div style="font-weight: 500;">{{ worker.last_handover.task_title }}</div>
                <div class="text-sm text-muted">
                  ➡ {{ worker.last_handover.team_name }}
                  <span v-if="worker.is_recent_handover" style="color: var(--accent-orange);">
                    ({{ formatRelativeTime(worker.last_handover.date) }})
                  </span>
                </div>
              </div>
              <span v-else class="text-muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '../api'

const workers = ref([])
const totalWorkers = ref(0)
const totalTasks = ref(0)
const loading = ref(true)
const lastUpdated = ref('')
let timer = null

onMounted(() => {
  fetchData()
  // 30 saniyede bir otomatik yenile
  timer = setInterval(fetchData, 30000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

async function fetchData() {
  loading.value = true
  try {
    const res = await api.get('/tasks/worker-tracking/')
    workers.value = res.data.workers
    totalWorkers.value = res.data.total_workers
    totalTasks.value = res.data.total_active_tasks
    lastUpdated.value = new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch (error) {
    console.error('Çalışan verisi alınamadı:', error)
  } finally {
    loading.value = false
  }
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return 'Yok'
  const date = new Date(dateStr)
  const now = new Date()
  const diffInMinutes = Math.floor((now - date) / 60000)
  
  if (diffInMinutes < 1) return 'Az önce'
  if (diffInMinutes < 60) return `${diffInMinutes} dk önce`
  if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)} saat önce`
  return date.toLocaleDateString('tr-TR')
}
</script>

<style scoped>
.text-accent {
  color: var(--accent-blue);
}
.avatar {
  width: 32px;
  height: 32px;
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: var(--text-secondary);
}
.row-highlight td {
  background-color: rgba(249, 115, 22, 0.05);
  border-left: 2px solid var(--accent-orange);
}
.animate-spin {
  display: inline-block;
  animation: spin 1s linear infinite;
}
@keyframes spin { 100% { transform: rotate(360deg); } }
.hover-underline:hover { text-decoration: underline !important; }
.text-primary { color: var(--accent-blue); }
</style>
