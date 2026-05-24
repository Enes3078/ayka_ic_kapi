<template>
  <div class="page-content">
    <div class="page-header">
      <h2 class="page-title">Genel Bakış</h2>
    </div>

    <div class="stats-grid dashboard-stats">
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
      <div class="dashboard-table-header">
        <div>
          <h3 style="font-weight: 700;">Görevler</h3>
          <div class="text-sm text-muted">{{ statusLabel(activeStatus) }} durumundaki görevler</div>
        </div>
        <div class="dashboard-status-tabs" role="tablist">
          <button
            v-for="option in statusOptions"
            :key="option.value"
            type="button"
            class="status-tab"
            :class="{ active: activeStatus === option.value }"
            @click="setStatus(option.value)"
          >
            <span class="status-label-full">{{ option.label }}</span>
            <span class="status-label-short">{{ option.shortLabel }}</span>
          </button>
        </div>
        <router-link to="/tasks" class="btn btn-ghost btn-sm">Tümünü Gör →</router-link>
      </div>
      <div v-if="loading" class="loading-container">
        <div class="spinner"></div>
      </div>
      <div v-else-if="filteredTasks.length === 0" class="empty-state">
        <div class="empty-state-icon">📋</div>
        <div class="empty-state-text">{{ statusLabel(activeStatus) }} durumunda görev yok</div>
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>Öncelik</th>
            <th>Görev</th>
            <th>Durum</th>
            <th>Ekip</th>
            <th>Tarih</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in filteredTasks" :key="task.id" class="clickable-row" @click="openTaskDetail(task)">
            <td><span :class="['badge', `badge-${task.priority}`]">{{ priorityLabel(task.priority) }}</span></td>
            <td style="font-weight: 600;">{{ task.title }}</td>
            <td><span :class="['badge', `badge-${task.status.replace('_', '-')}`]">{{ statusLabel(task.status) }}</span></td>
            <td class="text-muted">{{ task.team_name || '—' }}</td>
            <td class="text-muted text-sm">{{ formatDate(task.created_at) }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!loading && filteredTasks.length" class="task-card-list">
        <button
          v-for="task in filteredTasks"
          :key="task.id"
          type="button"
          class="task-card-row"
          @click="openTaskDetail(task)"
        >
          <span :class="['priority-chip', `priority-chip--${task.priority}`]">{{ priorityLabel(task.priority) }}</span>
          <span class="task-card-main">
            <strong>{{ task.title }}</strong>
            <span>{{ statusLabel(task.status) }} · {{ task.team_name || 'Ekip yok' }} · {{ formatDate(task.created_at) }}</span>
          </span>
        </button>
      </div>
    </div>

    <div v-if="showDetailModal" class="modal-backdrop" @click.self="closeTaskDetail">
      <div class="modal-content dashboard-task-modal">
        <div class="modal-header">
          <div>
            <h2>{{ selectedTask?.title || 'Görev Detayı' }}</h2>
            <div class="modal-subtitle">
              {{ selectedTask?.team_detail?.name || 'Ekip atanmadı' }} · {{ formatDateTime(selectedTask?.created_at) }}
            </div>
          </div>
          <button class="btn btn-ghost btn-icon" @click="closeTaskDetail">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="detailLoading" class="loading-container">
            <div class="spinner"></div>
          </div>
          <template v-else-if="selectedTask">
            <div class="detail-summary">
              <div class="detail-pill">
                <span>Durum</span>
                <strong>{{ statusLabel(selectedTask.status) }}</strong>
              </div>
              <div class="detail-pill">
                <span>Öncelik</span>
                <strong>{{ priorityLabel(selectedTask.priority) }}</strong>
              </div>
              <div class="detail-pill">
                <span>Planlanan</span>
                <strong>{{ selectedTask.planned_hours || 0 }} sa</strong>
              </div>
              <div class="detail-pill">
                <span>Kalem</span>
                <strong>{{ selectedTask.product_lines?.length || 0 }}</strong>
              </div>
            </div>

            <div class="detail-grid">
              <div>
                <div class="detail-label">Açıklama</div>
                <p class="detail-text">{{ selectedTask.description || 'Açıklama girilmemiş.' }}</p>
              </div>
              <div>
                <div class="detail-label">Sorumlular</div>
                <div class="detail-text">
                  Sahip: {{ selectedTask.owner_detail?.first_name || selectedTask.owner_detail?.username || '—' }}
                  <br />
                  Atanan: {{ selectedTask.assignee_detail?.first_name || selectedTask.assignee_detail?.username || '—' }}
                </div>
              </div>
              <div>
                <div class="detail-label">Başlangıç</div>
                <div class="detail-text">{{ formatDateTime(selectedTask.start_date) }}</div>
              </div>
              <div>
                <div class="detail-label">Bitiş / Termin</div>
                <div class="detail-text">
                  {{ formatDateTime(selectedTask.end_date) }}
                  <br />
                  <span class="text-muted">Termin: {{ formatDateTime(selectedTask.due_date) }}</span>
                </div>
              </div>
            </div>

            <div class="detail-section">
              <div class="detail-label mb-8">Üretim Kalemleri</div>
              <table v-if="selectedTask.product_lines?.length" class="data-table compact-table">
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Varyant</th>
                    <th>Ölçü</th>
                    <th>Adet</th>
                    <th>Üretilen</th>
                    <th>Süre</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="line in selectedTask.product_lines" :key="line.id">
                    <td style="font-weight: 600;">{{ line.model_code }}</td>
                    <td>{{ line.variant || '—' }}</td>
                    <td>{{ line.dimension || '—' }}</td>
                    <td>{{ line.quantity }}</td>
                    <td>{{ line.qty_produced }}</td>
                    <td>{{ line.total_planned_minutes || 0 }} dk</td>
                  </tr>
                </tbody>
              </table>
              <div v-else class="text-muted">Bu görevde üretim kalemi yok.</div>
            </div>
          </template>
        </div>
        <div class="modal-footer">
          <router-link v-if="selectedTask" :to="`/tasks/${selectedTask.id}`" class="btn btn-secondary" @click="closeTaskDetail">
            Detay Sayfasına Git
          </router-link>
          <button class="btn btn-primary" @click="closeTaskDetail">Kapat</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useTaskStore } from '../stores/tasks'
import api from '../api'

const taskStore = useTaskStore()
const loading = ref(true)
const detailLoading = ref(false)
const activeStatus = ref('todo')
const allTasks = ref([])
const filteredTasks = ref([])
const selectedTask = ref(null)
const showDetailModal = ref(false)

const statusOptions = [
  { value: 'todo', label: 'Yapılacak', shortLabel: 'Yapılacak' },
  { value: 'in_progress', label: 'Devam Eden', shortLabel: 'Devam' },
  { value: 'done', label: 'Tamamlanan', shortLabel: 'Tamam' },
]

onMounted(async () => {
  await fetchDashboardTasks()
})

async function fetchDashboardTasks() {
  loading.value = true
  try {
    const [allRes, filteredRes] = await Promise.all([
      api.get('/tasks/tasks/'),
      api.get('/tasks/tasks/', { params: { status: activeStatus.value } }),
    ])
    allTasks.value = allRes.data.results || allRes.data
    filteredTasks.value = filteredRes.data.results || filteredRes.data
  } finally {
    loading.value = false
  }
}

async function setStatus(status) {
  activeStatus.value = status
  loading.value = true
  try {
    const res = await api.get('/tasks/tasks/', { params: { status } })
    filteredTasks.value = res.data.results || res.data
  } finally {
    loading.value = false
  }
}

async function openTaskDetail(task) {
  showDetailModal.value = true
  detailLoading.value = true
  selectedTask.value = null
  try {
    selectedTask.value = await taskStore.fetchTask(task.id)
  } finally {
    detailLoading.value = false
  }
}

function closeTaskDetail() {
  showDetailModal.value = false
  selectedTask.value = null
}

const stats = computed(() => {
  const all = allTasks.value
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

function formatDateTime(d) {
  if (!d) return '—'
  return new Date(d).toLocaleString('tr-TR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.dashboard-stats {
  width: 100%;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.dashboard-table-header {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) auto auto;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}
.dashboard-status-tabs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
  padding: 4px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-body);
}
.status-tab {
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font-weight: 700;
  padding: 8px 12px;
  cursor: pointer;
  min-width: 112px;
  min-height: 42px;
  text-align: center;
  line-height: 1.15;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.status-tab.active {
  background: var(--accent-blue);
  color: white;
}
.status-label-short {
  display: none;
}
.clickable-row {
  cursor: pointer;
}
.task-card-list {
  display: none;
}
.task-card-row {
  width: 100%;
  display: grid;
  grid-template-columns: 82px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  padding: 14px 0;
  border: 0;
  border-bottom: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-primary);
  font-family: inherit;
  text-align: left;
}
.task-card-row:last-child {
  border-bottom: 0;
}
.task-card-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.task-card-main strong {
  font-size: 1rem;
  line-height: 1.35;
  white-space: normal;
  overflow-wrap: anywhere;
}
.task-card-main span {
  color: var(--text-secondary);
  font-size: 0.88rem;
}
.priority-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 34px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  font-weight: 800;
}
.priority-chip--low {
  background: var(--bg-card-hover);
  color: var(--text-secondary);
}
.priority-chip--medium {
  background: var(--accent-blue);
  color: white;
}
.priority-chip--high {
  background: var(--accent-orange-bg);
  color: var(--accent-orange);
  border: 1px solid #f9731633;
}
.priority-chip--urgent {
  background: var(--accent-red-bg);
  color: var(--accent-red);
  border: 1px solid #ef444433;
}
.dashboard-task-modal {
  max-width: 980px;
  width: 92%;
}
.modal-subtitle {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin-top: 4px;
}
.detail-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}
.detail-pill {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 12px;
  background: var(--bg-body);
}
.detail-pill span,
.detail-label {
  display: block;
  color: var(--text-muted);
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.6px;
  text-transform: uppercase;
}
.detail-pill strong {
  display: block;
  margin-top: 6px;
  font-size: 1rem;
}
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
  margin-bottom: 22px;
}
.detail-text {
  margin-top: 8px;
  color: var(--text-primary);
  line-height: 1.55;
}
.detail-section {
  border-top: 1px solid var(--border-color);
  padding-top: 18px;
}
.compact-table th,
.compact-table td {
  padding: 10px 12px;
}
@media (max-width: 860px) {
  .dashboard-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .dashboard-table-header {
    grid-template-columns: 1fr;
    align-items: stretch;
  }
  .dashboard-status-tabs {
    width: 100%;
  }
  .status-tab {
    min-width: 0;
    padding: 10px 6px;
    font-size: 0.86rem;
  }
  .card .data-table {
    display: none;
  }
  .task-card-list {
    display: block;
  }
  .detail-summary,
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 390px) {
  .dashboard-stats {
    grid-template-columns: 1fr;
  }
  .status-label-full {
    display: none;
  }
  .status-label-short {
    display: inline;
  }
  .status-tab {
    font-size: 0.84rem;
    padding-inline: 4px;
  }
}
</style>
