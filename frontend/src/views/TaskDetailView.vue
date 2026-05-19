<template>
  <div class="page-content">
    <div class="page-header">
      <div class="flex items-center gap-12">
        <button class="btn btn-ghost btn-icon" @click="router.push('/tasks')" title="Görevlere Dön">
          <span style="font-size:1.5rem;">←</span>
        </button>
        <div>
          <h2 class="page-title mb-4">{{ task?.title || 'Yükleniyor...' }}</h2>
          <div class="flex gap-8" v-if="task">
            <span :class="['badge', `badge-${task.priority}`]">{{ priorityLabel(task.priority) }}</span>
            <span :class="['badge', `badge-${task.status.replace('_', '-')}`]">{{ statusLabel(task.status) }}</span>
          </div>
        </div>
      </div>
      <div class="flex gap-12" v-if="task && auth.isAdminOrManager">
        <button class="btn btn-secondary" @click="showEditModal = true">
          ✏️ Görevi Düzenle
        </button>
        <button class="btn btn-danger" @click="confirmDeleteTask" :disabled="deleting">
          🗑️ Görevi Sil
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
    </div>
    
    <div v-else-if="task">
      <!-- Task Info Card -->
      <div class="card mb-24">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-16">
          <div>
            <div class="text-sm text-muted">Açıklama</div>
            <div class="mt-4">{{ task.description || 'Açıklama yok' }}</div>
          </div>
          <div>
            <div class="text-sm text-muted">Oluşturan</div>
            <div class="mt-4" style="font-weight: 500;">{{ task.owner_name }}</div>
          </div>
          <div>
            <div class="text-sm text-muted">Oluşturulma Tarihi</div>
            <div class="mt-4">{{ formatDate(task.created_at) }}</div>
          </div>
          <div>
            <div class="text-sm text-muted">Son Tarih (Vade)</div>
            <div class="mt-4" style="color: var(--accent-orange); font-weight: 600;">
              {{ formatDate(task.due_date) || 'Belirtilmedi' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Product Lines List -->
      <h3 class="mb-16">Üretim Kalemleri İş Akışı ({{ task.product_lines.length }})</h3>
      
      <div class="grid grid-cols-1 gap-16">
        <div v-for="pl in task.product_lines" :key="pl.id" class="card" style="border-left: 4px solid var(--accent-blue);">
          <div class="flex flex-col md:flex-row justify-between md:items-center gap-16 mb-16">
            <div>
              <h4 style="font-size: 1.1rem; font-weight: 700; margin-bottom: 4px;">{{ pl.model_code }}</h4>
              <div class="text-sm text-muted">
                <span v-if="pl.variant">Varyant: {{ pl.variant }} | </span>
                <span v-if="pl.color">Renk: {{ pl.color }} <span v-if="pl.product_color_code">({{ pl.product_color_code }})</span> | </span>
                <span v-if="pl.dimension">Ölçü: {{ pl.dimension }}</span>
              </div>
            </div>
            
            <div class="flex gap-16 text-right">
              <div>
                <div class="text-sm text-muted">Hedef</div>
                <div style="font-weight: 700;">{{ pl.quantity }} {{ pl.unit_type }}</div>
              </div>
              <div>
                <div class="text-sm text-muted">Üretilen</div>
                <div style="font-weight: 700; color: var(--accent-green);">{{ pl.qty_produced }} {{ pl.unit_type }}</div>
              </div>
              <div>
                <div class="text-sm text-muted">Fire</div>
                <div style="font-weight: 700; color: var(--accent-red);">{{ pl.fire_qty }} {{ pl.unit_type }}</div>
              </div>
            </div>
          </div>
          
          <div v-if="pl.brief_intro" class="mb-16 p-12 bg-slate-50 rounded text-sm" style="border-left: 2px solid var(--border-color);">
            {{ pl.brief_intro }}
          </div>

          <!-- Workflow Visualizer -->
          <div>
            <div class="text-sm font-semibold mb-8">İş Akışı Rotası</div>
            <div v-if="pl.workflow_team_ids && pl.workflow_team_ids.length > 0" class="flex flex-wrap items-center gap-8">
              <template v-for="(teamId, index) in pl.workflow_team_ids" :key="index">
                <div 
                  class="px-12 py-6 rounded text-sm"
                  :class="getStageClass(pl, index)"
                  style="border: 1px solid var(--border-color); font-weight: 500;"
                >
                  {{ getTeamName(teamId) }}
                  <span v-if="pl.active_product_index === index && !pl.stage_done" style="font-size: 0.7rem; margin-left: 4px;">(Aktif)</span>
                  <span v-if="index < pl.active_product_index || pl.stage_done" style="font-size: 0.7rem; margin-left: 4px;">✓</span>
                </div>
                <span v-if="index < pl.workflow_team_ids.length - 1" class="text-muted">➡</span>
              </template>
            </div>
            <div v-else class="text-sm text-muted">
              Bu kalem için iş akışı rotası atanmamış.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Task Modal -->
    <TaskModal
      v-if="showEditModal"
      :task="task"
      @close="showEditModal = false"
      @saved="onTaskSaved"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTaskStore } from '../stores/tasks'
import { useAuthStore } from '../stores/auth'
import TaskModal from '../components/tasks/TaskModal.vue'
import api from '../api'

const route = useRoute()
const router = useRouter()
const taskStore = useTaskStore()
const auth = useAuthStore()
const showToast = inject('showToast')

const taskId = route.params.id
const loading = ref(true)
const task = ref(null)
const showEditModal = ref(false)
const deleting = ref(false)

onMounted(async () => {
  await taskStore.fetchTeams() // Make sure teams are loaded for name mapping
  await fetchTaskDetail()
})

async function fetchTaskDetail() {
  loading.value = true
  try {
    const res = await api.get(`/tasks/tasks/${taskId}/`)
    task.value = res.data
  } catch (err) {
    console.error('Task detayı yüklenemedi', err)
  } finally {
    loading.value = false
  }
}

async function onTaskSaved() {
  showEditModal.value = false
  await fetchTaskDetail()
}

async function confirmDeleteTask() {
  if (!window.confirm('Bu görevi silmek istediğinize emin misiniz? Bu işlem geri alınamaz ve tüm ilişkili üretim kalemleri ile iş akışları silinecektir.')) {
    return
  }
  deleting.value = true
  try {
    await api.delete(`/tasks/tasks/${taskId}/`)
    showToast('Görev başarıyla silindi!', 'success')
    router.push('/tasks')
  } catch (err) {
    console.error('Görev silinemedi', err)
    showToast('Görev silinirken bir hata oluştu.', 'error')
  } finally {
    deleting.value = false
  }
}

function getTeamName(teamId) {
  const team = taskStore.teams.find(t => t.id === teamId)
  return team ? team.name : `Ekip ${teamId}`
}

function getStageClass(pl, index) {
  if (pl.stage_done) {
    return 'bg-green-50 text-green-700 border-green-200'
  }
  if (index < pl.active_product_index) {
    return 'bg-green-50 text-green-700 border-green-200' // Passed stages
  }
  if (index === pl.active_product_index) {
    return 'bg-blue-50 text-blue-700 border-blue-200 shadow-sm' // Current active stage
  }
  return 'bg-slate-50 text-slate-500' // Upcoming stages
}

const statusLabels = { todo: 'Yapılacak', in_progress: 'Devam Ediyor', done: 'Tamamlandı' }
const priorityLabels = { low: 'Düşük', medium: 'Orta', high: 'Yüksek', urgent: 'Acil' }
const statusLabel = (s) => statusLabels[s] || s
const priorityLabel = (p) => priorityLabels[p] || p

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.bg-green-50 { background-color: #f0fdf4; }
.text-green-700 { color: #15803d; }
.border-green-200 { border-color: #bbf7d0 !important; }

.bg-blue-50 { background-color: #eff6ff; }
.text-blue-700 { color: #1d4ed8; }
.border-blue-200 { border-color: #bfdbfe !important; }

.bg-slate-50 { background-color: #f8fafc; }
.text-slate-500 { color: #64748b; }
</style>
