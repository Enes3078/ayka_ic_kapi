<template>
  <div class="page-content">
    <div class="page-header">
      <h2 class="page-title">Genel Bakış</h2>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Toplam Görev</div>
        <div class="stat-value">{{ stats.total }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Yapılacak</div>
        <div class="stat-value" style="background: linear-gradient(135deg, #6b7280, #9ca3af); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">{{ stats.todo }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Devam Ediyor</div>
        <div class="stat-value" style="background: linear-gradient(135deg, #f59e0b, #fbbf24); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">{{ stats.inProgress }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Tamamlandı</div>
        <div class="stat-value" style="background: linear-gradient(135deg, #22c55e, #4ade80); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">{{ stats.done }}</div>
      </div>
    </div>

    <!-- Recent Tasks -->
    <div class="card">
      <div class="flex items-center justify-between mb-16">
        <h3 style="font-weight: 700;">Son Görevler</h3>
        <router-link to="/tasks" class="btn btn-ghost btn-sm">Tümünü Gör →</router-link>
      </div>
      <div v-if="loading" class="loading-container">
        <div class="spinner"></div>
      </div>
      <div v-else-if="recentTasks.length === 0" class="empty-state">
        <div class="empty-state-icon">📋</div>
        <div class="empty-state-text">Henüz görev oluşturulmamış</div>
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Görev</th>
            <th>Durum</th>
            <th>Öncelik</th>
            <th>Ekip</th>
            <th>Tarih</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in recentTasks" :key="task.id">
            <td style="font-weight: 600;">{{ task.title }}</td>
            <td><span :class="['badge', `badge-${task.status.replace('_', '-')}`]">{{ statusLabel(task.status) }}</span></td>
            <td><span :class="['badge', `badge-${task.priority}`]">{{ priorityLabel(task.priority) }}</span></td>
            <td class="text-muted">{{ task.team_name || '—' }}</td>
            <td class="text-muted text-sm">{{ formatDate(task.created_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTaskStore } from '../stores/tasks'

const taskStore = useTaskStore()
const loading = ref(true)

onMounted(async () => {
  try {
    await taskStore.fetchTasks()
  } finally {
    loading.value = false
  }
})

const recentTasks = computed(() => taskStore.tasks.slice(0, 8))

const stats = computed(() => {
  const all = taskStore.tasks
  return {
    total: all.length,
    todo: all.filter(t => t.status === 'todo').length,
    inProgress: all.filter(t => t.status === 'in_progress').length,
    done: all.filter(t => t.status === 'done').length,
  }
})

const statusLabels = { todo: 'Yapılacak', in_progress: 'Devam Ediyor', done: 'Tamamlandı' }
const priorityLabels = { low: 'Düşük', medium: 'Orta', high: 'Yüksek', urgent: 'Acil' }
const statusLabel = (s) => statusLabels[s] || s
const priorityLabel = (p) => priorityLabels[p] || p

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' })
}
</script>
