<template>
  <div class="page-content">
    <div class="page-header" style="flex-direction: column; align-items: flex-start; gap: 16px;">
      <div class="flex justify-between w-full">
        <h2 class="page-title">Gelişmiş Raporlama</h2>
        <button v-if="!loading" class="btn btn-primary" @click="exportToPDF">
          📄 PDF İndir
        </button>
      </div>
      
      <!-- Sekmeler (Tabs) -->
      <div class="tabs">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'task' }" 
          @click="activeTab = 'task'">
          Görev Raporu
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'production' }" 
          @click="activeTab = 'production'">
          Üretim (Faaliyet) Raporu
        </button>
      </div>
    </div>

    <!-- GÖREV RAPORU SEKMESİ -->
    <div v-if="activeTab === 'task'">
      <div class="card mb-16 bg-slate-50">
        <h3 class="mb-12 text-sm font-bold text-muted">Filtreler</h3>
        <div class="form-row" style="display:flex;gap:12px;flex-wrap:wrap;">
          <div class="form-group" style="flex:1;min-width:150px;">
            <label class="form-label">Yıl</label>
            <input v-model="taskFilters.year" type="number" class="form-input" placeholder="2024" @change="fetchTaskReport" />
          </div>
          <div class="form-group" style="flex:1;min-width:150px;">
            <label class="form-label">Ay</label>
            <select v-model="taskFilters.month" class="form-select" @change="fetchTaskReport">
              <option value="">Tümü</option>
              <option v-for="m in 12" :key="m" :value="m">{{ m }}. Ay</option>
            </select>
          </div>
          <div class="form-group" style="flex:1;min-width:150px;">
            <label class="form-label">Durum</label>
            <select v-model="taskFilters.status" class="form-select" @change="fetchTaskReport">
              <option value="">Tümü</option>
              <option value="todo">Yapılacak</option>
              <option value="in_progress">Devam Ediyor</option>
              <option value="done">Tamamlandı</option>
            </select>
          </div>
        </div>
      </div>

      <div v-if="loading" class="loading-container"><div class="spinner"></div></div>
      <div v-else>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-16 mb-24">
          <div class="stat-card">
            <div class="stat-title">Filtrelenen Görev Sayısı</div>
            <div class="stat-value" style="color: var(--accent-blue);">{{ taskReport?.aggregate?.total_created || 0 }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-title">Tamamlanan Görev Sayısı</div>
            <div class="stat-value" style="color: var(--accent-green);">{{ taskReport?.aggregate?.total_completed || 0 }}</div>
          </div>
        </div>

        <div class="card">
          <h3 class="mb-16">Görev Listesi</h3>
          <div v-if="!taskReport?.tasks?.length" class="empty-state">
            <div class="empty-state-text">Bu filtrelere uygun görev bulunamadı.</div>
          </div>
          <div style="overflow-x: auto;" v-else>
            <table class="data-table" id="task-table">
              <thead>
                <tr>
                  <th>Görev Başlığı</th>
                  <th>Durum</th>
                  <th>Öncelik</th>
                  <th>Ekip</th>
                  <th>Atanan</th>
                  <th>Kalem Sy.</th>
                  <th>Planlanan (Sa)</th>
                  <th>Gerçekleşen (Sa)</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="t in taskReport.tasks" :key="t.id">
                  <td style="font-weight: 500;">{{ t.title }}</td>
                  <td><span class="badge">{{ t.status }}</span></td>
                  <td>{{ t.priority }}</td>
                  <td>{{ t.team }}</td>
                  <td>{{ t.assignee }}</td>
                  <td>{{ t.product_line_count }}</td>
                  <td style="font-weight: 600;">{{ t.planned_hours }}</td>
                  <td style="font-weight: 600;" :style="{ color: t.actual_hours > t.planned_hours ? 'var(--accent-red)' : 'var(--accent-green)' }">
                    {{ t.actual_hours }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ÜRETİM RAPORU SEKMESİ -->
    <div v-if="activeTab === 'production'">
      <div class="card mb-16 bg-slate-50">
        <h3 class="mb-12 text-sm font-bold text-muted">Filtreler</h3>
        <div class="form-row" style="display:flex;gap:12px;flex-wrap:wrap;">
          <div class="form-group" style="flex:1;min-width:150px;">
            <label class="form-label">Tarih</label>
            <input v-model="prodFilters.date" type="date" class="form-input" @change="fetchProductionReport" />
          </div>
        </div>
      </div>

      <div v-if="loading" class="loading-container"><div class="spinner"></div></div>
      <div v-else>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-16 mb-24">
          <div class="stat-card">
            <div class="stat-title">Toplam Üretim Kaydı</div>
            <div class="stat-value" style="color: var(--accent-blue);">{{ prodReport?.aggregate?.total_logs || 0 }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-title">Toplam Üretilen (Miktar)</div>
            <div class="stat-value" style="color: var(--accent-green);">{{ prodReport?.aggregate?.total_produced || 0 }}</div>
          </div>
        </div>

        <div class="card">
          <h3 class="mb-16">Üretim Hareketleri</h3>
          <div v-if="!prodReport?.logs?.length" class="empty-state">
            <div class="empty-state-text">Bu tarihte üretim hareketi bulunamadı.</div>
          </div>
          <div style="overflow-x: auto;" v-else>
            <table class="data-table" id="prod-table">
              <thead>
                <tr>
                  <th>Görev</th>
                  <th>Kalem (Model Kodu)</th>
                  <th>Ekip</th>
                  <th>İşçi</th>
                  <th class="text-right">Hedef</th>
                  <th class="text-right">Üretilen</th>
                  <th class="text-right">Fire</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(l, i) in prodReport.logs" :key="i">
                  <td>{{ l.task_title }}</td>
                  <td style="font-weight: 500; color: var(--accent-blue);">{{ l.model_code }}</td>
                  <td><span class="badge badge-medium">{{ l.team }}</span></td>
                  <td>{{ l.worker }}</td>
                  <td class="text-right">{{ l.target_qty }}</td>
                  <td class="text-right" style="font-weight: 700; color: var(--accent-green);">{{ l.produced_qty }}</td>
                  <td class="text-right" style="font-weight: 700; color: var(--accent-red);">{{ l.scrap_qty }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../api'
import jsPDF from 'jspdf'
import 'jspdf-autotable'

const activeTab = ref('task')
const loading = ref(false)

const taskFilters = ref({ year: new Date().getFullYear(), month: '', status: '' })
const prodFilters = ref({ date: new Date().toISOString().slice(0, 10) })

const taskReport = ref(null)
const prodReport = ref(null)

onMounted(() => {
  fetchTaskReport()
  fetchProductionReport()
})

watch(activeTab, () => {
  if (activeTab.value === 'task' && !taskReport.value) fetchTaskReport()
  if (activeTab.value === 'production' && !prodReport.value) fetchProductionReport()
})

async function fetchTaskReport() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (taskFilters.value.year) params.append('year', taskFilters.value.year)
    if (taskFilters.value.month) params.append('month', taskFilters.value.month)
    if (taskFilters.value.status) params.append('status', taskFilters.value.status)
    
    const res = await api.get(`/tasks/reports/task-report/?${params.toString()}`)
    taskReport.value = res.data
  } catch (err) {
    console.error('Görev raporu çekilemedi', err)
  } finally {
    loading.value = false
  }
}

async function fetchProductionReport() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (prodFilters.value.date) params.append('date', prodFilters.value.date)
    
    const res = await api.get(`/tasks/reports/production-report/?${params.toString()}`)
    prodReport.value = res.data
  } catch (err) {
    console.error('Üretim raporu çekilemedi', err)
  } finally {
    loading.value = false
  }
}

// Türkçe karakterleri temizleme (jsPDF standart font uyumluluğu için)
function tr2en(str) {
  if (!str) return ''
  return str.toString()
    .replace(/ğ/g, 'g').replace(/Ğ/g, 'G')
    .replace(/ü/g, 'u').replace(/Ü/g, 'U')
    .replace(/ş/g, 's').replace(/Ş/g, 'S')
    .replace(/ı/g, 'i').replace(/İ/g, 'I')
    .replace(/ö/g, 'o').replace(/Ö/g, 'O')
    .replace(/ç/g, 'c').replace(/Ç/g, 'C')
}

function exportToPDF() {
  const doc = new jsPDF('landscape')
  doc.setFontSize(18)
  
  if (activeTab.value === 'task') {
    doc.text(tr2en('Gorev Raporu'), 14, 20)
    doc.setFontSize(11)
    doc.text(tr2en(`Toplam: ${taskReport.value?.aggregate?.total_created || 0} | Tamamlanan: ${taskReport.value?.aggregate?.total_completed || 0}`), 14, 28)
    
    const rows = taskReport.value?.tasks?.map(t => [
      tr2en(t.title), tr2en(t.status), tr2en(t.priority), tr2en(t.team), tr2en(t.assignee),
      t.product_line_count, t.planned_hours, t.actual_hours
    ]) || []
    
    doc.autoTable({
      startY: 35,
      head: [[tr2en('Baslik'), 'Durum', 'Oncelik', 'Ekip', 'Atanan', 'Kalem', 'Plan.(sa)', 'Gerc.(sa)']],
      body: rows,
      theme: 'grid',
      headStyles: { fillColor: [79, 110, 247] }
    })
    doc.save(`Gorev_Raporu_${new Date().getTime()}.pdf`)
    
  } else {
    doc.text(tr2en('Uretim Raporu - ' + prodFilters.value.date), 14, 20)
    doc.setFontSize(11)
    doc.text(tr2en(`Toplam Uretim (Miktar): ${prodReport.value?.aggregate?.total_produced || 0}`), 14, 28)
    
    const rows = prodReport.value?.logs?.map(l => [
      tr2en(l.task_title), tr2en(l.model_code), tr2en(l.team), tr2en(l.worker),
      l.target_qty, l.produced_qty, l.scrap_qty
    ]) || []
    
    doc.autoTable({
      startY: 35,
      head: [['Gorev', 'Kalem Kodu', 'Ekip', 'Isci', 'Hedef', 'Uretilen', 'Fire']],
      body: rows,
      theme: 'grid',
      headStyles: { fillColor: [40, 167, 69] }
    })
    doc.save(`Uretim_Raporu_${prodFilters.value.date}.pdf`)
  }
}
</script>

<style scoped>
.tabs {
  display: flex; gap: 12px; background: var(--bg-card); padding: 6px;
  border-radius: var(--radius-md); border: 1px solid var(--border-color);
}
.tab-btn {
  background: transparent; border: none; padding: 10px 20px;
  font-size: 0.95rem; font-weight: 600; color: var(--text-muted);
  cursor: pointer; border-radius: var(--radius-sm); transition: all 0.2s ease;
}
.tab-btn:hover { background: rgba(0, 0, 0, 0.05); }
.tab-btn.active { background: var(--accent-blue); color: white; box-shadow: 0 2px 8px rgba(79, 110, 247, 0.3); }

.stat-card {
  background: white; border: 1px solid var(--border-color); border-radius: var(--radius-md);
  padding: 24px; text-align: center;
}
.stat-title { font-size: 0.9rem; color: var(--text-muted); margin-bottom: 8px; font-weight: 600; }
.stat-value { font-size: 2rem; font-weight: 800; }
</style>
