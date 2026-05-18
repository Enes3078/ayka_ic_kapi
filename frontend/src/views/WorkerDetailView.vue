<template>
  <div class="page-content">
    <div class="page-header">
      <div class="flex items-center gap-12">
        <button class="btn btn-ghost btn-icon" @click="router.push('/worker-tracking')" title="Geri Dön">
          <span style="font-size:1.5rem;">←</span>
        </button>
        <div>
          <h2 class="page-title mb-4">{{ workerName }}</h2>
          <div class="text-sm text-muted">Departman: {{ department }}</div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
    </div>

    <div v-else>
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-24 mb-24">
        <!-- 14 Günlük Grafik -->
        <div class="card">
          <h3 class="mb-16">Son 14 Günlük Performans (Tamamlanan Kalem)</h3>
          <div style="height: 300px;">
            <Bar :data="dailyChartData" :options="chartOptions" />
          </div>
        </div>
        
        <!-- 12 Aylık Grafik -->
        <div class="card">
          <h3 class="mb-16">Son 12 Aylık Performans</h3>
          <div style="height: 300px;">
            <Line :data="monthlyChartData" :options="chartOptions" />
          </div>
        </div>
      </div>

      <!-- Aktif Görevler Tablosu -->
      <div class="card">
        <h3 class="mb-16">Aktif Üzerindeki Görevler ({{ activeTasks.length }})</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>Görev</th>
              <th>Kalem Kodu</th>
              <th>Takım / Aşama</th>
              <th>Miktar</th>
              <th>Başlama Zamanı</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="task in activeTasks" :key="task.id">
              <td style="font-weight: 500;">{{ task.task_title }}</td>
              <td class="text-muted" style="font-family: monospace;">{{ task.model_code }}</td>
              <td><span class="badge badge-done">{{ task.team }}</span></td>
              <td>{{ task.qty }}</td>
              <td class="text-sm text-muted">{{ formatDate(task.started_at) }}</td>
            </tr>
            <tr v-if="activeTasks.length === 0">
              <td colspan="5" class="text-center py-24 text-muted">Şu an üzerinde aktif üretim kalemi bulunmuyor.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Tamamlanmış Görevler Tablosu -->
      <div class="card mt-24">
        <h3 class="mb-16">Tamamlanmış Görev Geçmişi ({{ completedTasks.length }})</h3>
        <table class="data-table">
          <thead>
            <tr>
              <th>Görev</th>
              <th>Kalem Kodu</th>
              <th>Takım / Aşama</th>
              <th>Üretim</th>
              <th>Fire</th>
              <th>Bitiş Zamanı</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="task in completedTasks" :key="task.id">
              <td style="font-weight: 500;">{{ task.task_title }}</td>
              <td class="text-muted" style="font-family: monospace;">{{ task.model_code }}</td>
              <td><span class="badge badge-done">{{ task.team }}</span></td>
              <td style="font-weight: 700; color: var(--accent-green);">{{ task.qty_produced }}</td>
              <td style="font-weight: 700; color: var(--accent-red);">{{ task.scrap_qty }}</td>
              <td class="text-sm text-muted">{{ formatDate(task.completed_at) }}</td>
            </tr>
            <tr v-if="completedTasks.length === 0">
              <td colspan="6" class="text-center py-24 text-muted">Henüz tamamlanmış görev geçmişi bulunmuyor.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import {
  Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale,
  PointElement, LineElement
} from 'chart.js'
import { Bar, Line } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend)

const route = useRoute()
const router = useRouter()
const workerId = route.params.id

const loading = ref(true)
const workerName = ref('')
const department = ref('')
const activeTasks = ref([])
const completedTasks = ref([])

const dailyChartData = ref({ labels: [], datasets: [] })
const monthlyChartData = ref({ labels: [], datasets: [] })

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { precision: 0 }
    }
  }
}

onMounted(() => {
  fetchWorkerData()
})

async function fetchWorkerData() {
  try {
    const res = await api.get(`/tasks/worker-tracking/${workerId}/`)
    const data = res.data
    
    workerName.value = data.worker_name
    department.value = data.department || 'Bilinmiyor'
    activeTasks.value = data.active_tasks || []
    completedTasks.value = data.completed_tasks || []
    
    dailyChartData.value = {
      labels: data.daily_chart.labels,
      datasets: [{
        label: 'Tamamlanan İş',
        backgroundColor: '#4f6ef7',
        data: data.daily_chart.data
      }]
    }
    
    monthlyChartData.value = {
      labels: data.monthly_chart.labels,
      datasets: [{
        label: 'Tamamlanan İş',
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.2)',
        data: data.monthly_chart.data,
        fill: true,
        tension: 0.4
      }]
    }
  } catch(err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

function formatDate(d) {
  if (!d) return ''
  const date = new Date(d)
  return date.toLocaleDateString('tr-TR') + ' ' + date.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
}
</script>
