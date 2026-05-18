<template>
  <div class="page-content">
    <div class="page-header">
      <h2 class="page-title">Geçmiş Görevlerim</h2>
      <p class="text-muted text-sm mt-4">Bugüne kadar başarıyla devrettiğiniz/bitirdiğiniz üretim kalemleri aşağıda listelenmektedir.</p>
    </div>

    <div class="card">
      <div v-if="loading" class="loading-container">
        <div class="spinner"></div>
      </div>
      <div v-else-if="pastTasks.length === 0" class="empty-state">
        <div class="empty-state-icon">✅</div>
        <div class="empty-state-text">Henüz tamamladığınız bir üretim kalemi bulunmuyor.</div>
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Görev / Kalem Kodu</th>
            <th>Çalıştığınız Ekip (Aşama)</th>
            <th class="text-right">Üretim Adedi</th>
            <th class="text-right">Fire Adedi</th>
            <th>Tamamlanma Tarihi</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in pastTasks" :key="task.id">
            <td>
              <div style="font-weight: 600; color: var(--accent-blue);">{{ task.model_code }}</div>
              <div class="text-xs text-muted">{{ task.task_title }}</div>
            </td>
            <td>
              <span class="badge badge-done">{{ task.team }}</span>
            </td>
            <td class="text-right" style="font-weight: 700; color: var(--accent-green);">
              {{ task.qty_produced }}
            </td>
            <td class="text-right" style="font-weight: 700; color: var(--accent-red);">
              {{ task.scrap_qty }}
            </td>
            <td class="text-sm text-muted">
              {{ formatDate(task.completed_at) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const pastTasks = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await api.get('/tasks/my-past-tasks/')
    pastTasks.value = res.data
  } catch (err) {
    console.error('Geçmiş görevler yüklenemedi', err)
  } finally {
    loading.value = false
  }
})

function formatDate(d) {
  if (!d) return ''
  const date = new Date(d)
  return date.toLocaleDateString('tr-TR') + ' ' + date.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
}
</script>
