<template>
  <div class="page-content">
    <!-- Page Header -->
    <div class="page-header">
      <h2 class="page-title">Görevler</h2>
      <div class="flex gap-12">
        <button v-if="auth.isAdminOrManager" class="btn btn-secondary" @click="showExcelModal = true">
          📥 Excel İçe Aktar
        </button>
        <button v-if="auth.isAdminOrManager" class="btn btn-primary" @click="openCreateModal">
          ＋ Yeni Görev
        </button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-bar">
      <input
        v-model="searchQuery"
        type="text"
        class="form-input filter-search"
        placeholder="🔍 Görev ara..."
        @input="debouncedFetch"
      />
      <select v-model="filterStatus" class="form-select filter-select" @change="fetchFiltered">
        <option value="">Tüm Durumlar</option>
        <option value="todo">Yapılacak</option>
        <option value="in_progress">Devam Ediyor</option>
        <option value="done">Tamamlandı</option>
      </select>
      <select v-model="filterPriority" class="form-select filter-select" @change="fetchFiltered">
        <option value="">Tüm Öncelikler</option>
        <option value="low">Düşük</option>
        <option value="medium">Orta</option>
        <option value="high">Yüksek</option>
        <option value="urgent">Acil</option>
      </select>
    </div>

    <!-- Task List -->
    <div v-if="taskStore.loading" class="loading-container">
      <div class="spinner"></div>
      <span class="text-muted">Görevler yükleniyor...</span>
    </div>
    <div v-else-if="taskStore.tasks.length === 0" class="empty-state">
      <div class="empty-state-icon">📋</div>
      <div class="empty-state-text">Henüz görev yok. Yeni görev oluşturun veya Excel'den içe aktarın.</div>
    </div>
    <div v-else class="task-grid">
      <div
        v-for="task in taskStore.tasks"
        :key="task.id"
        class="task-card card"
        @click="goToDetail(task.id)"
      >
        <div class="task-card-header">
          <span :class="['badge', `badge-${task.priority}`]">{{ priorityLabel(task.priority) }}</span>
          <span :class="['badge', `badge-${task.status.replace('_', '-')}`]">{{ statusLabel(task.status) }}</span>
        </div>
        <h3 class="task-card-title">{{ task.title }}</h3>
        <div class="task-card-meta">
          <span>👤 {{ task.owner_name }}</span>
          <span v-if="task.team_name">🏭 {{ task.team_name }}</span>
          <span>📦 {{ task.product_line_count }} kalem</span>
        </div>
        <div v-if="task.due_date" class="task-card-due">
          📅 {{ formatDate(task.due_date) }}
        </div>
      </div>
    </div>

    <!-- Task Create/Edit Modal -->
    <TaskModal
      v-if="showTaskModal"
      :task="editingTask"
      :draft-data="draftData"
      @close="closeTaskModal"
      @saved="onTaskSaved"
    />

    <!-- Excel Import Modal -->
    <ExcelImportModal
      v-if="showExcelModal"
      @close="showExcelModal = false"
      @imported="onExcelImported"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '../stores/tasks'
import { useAuthStore } from '../stores/auth'
import TaskModal from '../components/tasks/TaskModal.vue'
import ExcelImportModal from '../components/tasks/ExcelImportModal.vue'

const router = useRouter()
const taskStore = useTaskStore()
const auth = useAuthStore()
const showToast = inject('showToast')

const showTaskModal = ref(false)
const showExcelModal = ref(false)
const editingTask = ref(null)
const draftData = ref(null)

const searchQuery = ref('')
const filterStatus = ref('')
const filterPriority = ref('')

let debounceTimer = null

onMounted(() => {
  fetchFiltered()
  taskStore.fetchTeams()
})

function fetchFiltered() {
  const params = {}
  if (searchQuery.value) params.search = searchQuery.value
  if (filterStatus.value) params.status = filterStatus.value
  if (filterPriority.value) params.priority = filterPriority.value
  taskStore.fetchTasks(params)
}

function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchFiltered, 300)
}

function openCreateModal() {
  editingTask.value = null
  draftData.value = null
  showTaskModal.value = true
}

function goToDetail(id) {
  router.push(`/tasks/${id}`)
}

function closeTaskModal() {
  showTaskModal.value = false
  editingTask.value = null
  draftData.value = null
}

function onTaskSaved() {
  closeTaskModal()
  fetchFiltered()
  showToast('Görev başarıyla kaydedildi!', 'success')
}

function onExcelImported(draft) {
  showExcelModal.value = false
  draftData.value = draft
  editingTask.value = null
  showTaskModal.value = true
  showToast(`Excel'den ${draft.row_count} kalem yüklendi. Kaydetmek için formu doldurun.`, 'success')
}

const statusLabels = { todo: 'Yapılacak', in_progress: 'Devam Ediyor', done: 'Tamamlandı' }
const priorityLabels = { low: 'Düşük', medium: 'Orta', high: 'Yüksek', urgent: 'Acil' }
const statusLabel = (s) => statusLabels[s] || s
const priorityLabel = (p) => priorityLabels[p] || p

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<style scoped>
.filters-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.filter-search {
  flex: 1;
  min-width: 200px;
}
.filter-select {
  width: 180px;
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.task-card {
  cursor: pointer;
  padding: 20px;
}
.task-card-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
}
.task-card-title {
  font-size: 1rem;
  font-weight: 700;
  margin-bottom: 12px;
  line-height: 1.3;
}
.task-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 0.8rem;
  color: var(--text-muted);
}
.task-card-due {
  margin-top: 12px;
  font-size: 0.8rem;
  color: var(--accent-orange);
}
</style>
