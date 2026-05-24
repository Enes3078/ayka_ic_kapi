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
      <div class="tabs" style="display: flex; flex-wrap: wrap; gap: 8px; width: 100%;">
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
          Üretim Raporu
        </button>
        <!-- Dinamik Ekip Sekmeleri -->
        <button 
          v-for="team in teams" 
          :key="team.id"
          class="tab-btn" 
          :class="{ active: activeTab === 'team_' + team.id }" 
          @click="activeTab = 'team_' + team.id">
          {{ team.name }} Raporu
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
              <option v-for="(monthName, index) in monthNames" :key="monthName" :value="index + 1">{{ monthName }}</option>
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
            <div class="stat-title">Sağlam Çıkan Miktar</div>
            <div class="stat-value" style="color: var(--accent-green);">{{ prodReport?.aggregate?.total_produced || 0 }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-title">İşlenen Miktar</div>
            <div class="stat-value" style="color: var(--accent-blue);">{{ prodReport?.aggregate?.total_processed || 0 }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-title">Toplam Fire</div>
            <div class="stat-value" style="color: var(--accent-red);">{{ prodReport?.aggregate?.total_scrap || 0 }}</div>
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
                  <th class="text-right">İşlenen</th>
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

    <!-- DİNAMİK EKİP FAALİYET RAPORLARI -->
    <div v-if="activeTab.startsWith('team_')">
      <div class="card mb-16 bg-slate-50">
        <h3 class="mb-12 text-sm font-bold text-muted">Filtreler</h3>
        <div class="form-row" style="display:flex;gap:12px;flex-wrap:wrap;">
          <div class="form-group" style="flex:1;min-width:150px;">
            <label class="form-label">Tarih</label>
            <input v-model="teamDate" type="date" class="form-input" @change="fetchTeamReport" />
          </div>
        </div>
      </div>

      <div v-if="loading" class="loading-container"><div class="spinner"></div></div>
      <div v-else>
        <div class="card">
          <h3 class="mb-16">{{ activeTeam?.name }} Günlük Faaliyet Raporu</h3>
          <div v-if="!currentTeamReport?.logs?.length" class="empty-state">
            <div class="empty-state-text">Bu tarihte doldurulmuş {{ activeTeam?.name }} raporu bulunamadı.</div>
          </div>
          
          <div style="overflow-x: auto;" v-else>
            <!-- 1. PVC DİLİMLEME İÇİN ÖZEL TABLO -->
            <table v-if="isPvcTeam" class="data-table" id="team-pvc-table">
              <thead>
                <tr>
                  <th>Görev / Sipariş</th>
                  <th>Kalem</th>
                  <th>Personel</th>
                  <th>Renk</th>
                  <th>Rulo Boy</th>
                  <th>Metre</th>
                  <th>Kesim Ölçüsü</th>
                  <th>Ek Açıklama</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(l, i) in currentTeamReport.logs" :key="i">
                  <td>{{ l.task_title }}</td>
                  <td style="font-weight: 500; color: var(--accent-blue);">{{ l.model_code }}</td>
                  <td>{{ l.worker }}</td>
                  <td>{{ l.pvc_color || '-' }}</td>
                  <td>{{ l.pvc_roll_size || '-' }}</td>
                  <td style="font-weight: 600;">{{ l.pvc_meters || '-' }}</td>
                  <td>{{ l.pvc_cut_size || '-' }}</td>
                  <td style="font-size: 0.85rem; color: var(--text-muted);">{{ l.activity_notes || '-' }}</td>
                </tr>
              </tbody>
            </table>

            <!-- 2. GİBEN İÇİN ÖZEL TABLO -->
            <table v-else-if="isGibenTeam" class="data-table" id="team-giben-table">
              <thead>
                <tr>
                  <th>Görev / Sipariş</th>
                  <th>Kalem</th>
                  <th>Personel</th>
                  <th>Yapılan İş</th>
                  <th>Tabaka Ölçüsü</th>
                  <th class="text-right">Adet</th>
                  <th>Ek Açıklama</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(l, i) in currentTeamReport.logs" :key="i">
                  <td>{{ l.task_title }}</td>
                  <td style="font-weight: 500; color: var(--accent-blue);">{{ l.model_code }}</td>
                  <td>{{ l.worker }}</td>
                  <td style="white-space: pre-wrap; font-size: 0.9rem;">{{ l.work_description || '-' }}</td>
                  <td>{{ l.giben_plate_size || '-' }}</td>
                  <td class="text-right" style="color: var(--accent-green); font-weight: bold;">{{ l.produced_qty }}</td>
                  <td style="font-size: 0.85rem; color: var(--text-muted);">{{ l.activity_notes || '-' }}</td>
                </tr>
              </tbody>
            </table>

            <!-- 3. CNC VE DİĞER STANDART EKİPLER İÇİN TABLO -->
            <table v-else class="data-table" id="team-standard-table">
              <thead>
                <tr>
                  <th>Görev / Sipariş</th>
                  <th>Kalem (Model)</th>
                  <th>Personel</th>
                  <th>Çalışılan Saat</th>
                  <th>Yapılan İş Detayı</th>
                  <th class="text-right">Üretilen / Fire</th>
                  <th>Fire Nerede?</th>
                  <th>Ek Açıklama</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(l, i) in currentTeamReport.logs" :key="i">
                  <td>{{ l.task_title }}</td>
                  <td style="font-weight: 500; color: var(--accent-blue);">{{ l.model_code }}</td>
                  <td>{{ l.worker }}</td>
                  <td style="font-weight: 600;">{{ l.working_hours }} sa</td>
                  <td style="white-space: pre-wrap; font-size: 0.9rem;">{{ l.work_description || '-' }}</td>
                  <td class="text-right">
                    <span style="color: var(--accent-green); font-weight: bold;">{{ l.produced_qty }}</span> / 
                    <span style="color: var(--accent-red); font-weight: bold;">{{ l.scrap_qty }}</span>
                  </td>
                  <td>{{ l.scrap_location || '-' }}</td>
                  <td style="font-size: 0.85rem; color: var(--text-muted);">{{ l.activity_notes || '-' }}</td>
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
import { ref, onMounted, watch, computed } from 'vue'
import api from '../api'
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

const activeTab = ref('task')
const loading = ref(false)
const teams = ref([])

const taskFilters = ref({ year: new Date().getFullYear(), month: '', status: '' })
const prodFilters = ref({ date: new Date().toISOString().slice(0, 10) })
const teamDate = ref(new Date().toISOString().slice(0, 10))

const taskReport = ref(null)
const prodReport = ref(null)
const currentTeamReport = ref(null)
const monthNames = [
  'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
  'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık',
]

onMounted(async () => {
  await fetchTeams()
  fetchTaskReport()
})

// Dynamic tab checking helpers
const activeTeam = computed(() => {
  if (!activeTab.value.startsWith('team_')) return null
  const id = parseInt(activeTab.value.replace('team_', ''))
  return teams.value.find(t => t.id === id) || null
})

const isPvcTeam = computed(() => {
  return activeTeam.value?.name?.toUpperCase().includes('PVC') || false
})

const isGibenTeam = computed(() => {
  const name = activeTeam.value?.name?.toUpperCase() || ''
  return name.includes('GIBEN') || name.includes('GİBEN')
})

watch(activeTab, () => {
  if (activeTab.value === 'task' && !taskReport.value) fetchTaskReport()
  if (activeTab.value === 'production' && !prodReport.value) fetchProductionReport()
  if (activeTab.value.startsWith('team_')) fetchTeamReport()
})

async function fetchTeams() {
  try {
    const res = await api.get('/tasks/teams/')
    teams.value = res.data.results || res.data
  } catch (err) {
    console.error('Ekipler yüklenemedi', err)
  }
}

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

async function fetchTeamReport() {
  if (!activeTeam.value) return
  loading.value = true
  try {
    const res = await api.get(`/tasks/reports/team-reports/`, {
      params: {
        team_id: activeTeam.value.id,
        date: teamDate.value
      }
    })
    currentTeamReport.value = res.data
  } catch (err) {
    console.error('Ekip raporu çekilemedi', err)
  } finally {
    loading.value = false
  }
}

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
    
    autoTable(doc, {
      startY: 35,
      head: [[tr2en('Baslik'), 'Durum', 'Oncelik', 'Ekip', 'Atanan', 'Kalem', 'Plan.(sa)', 'Gerc.(sa)']],
      body: rows,
      theme: 'grid',
      headStyles: { fillColor: [79, 110, 247] }
    })
    doc.save(`Gorev_Raporu_${new Date().getTime()}.pdf`)
    
  } else if (activeTab.value === 'production') {
    doc.text(tr2en('Uretim Raporu - ' + prodFilters.value.date), 14, 20)
    doc.setFontSize(11)
    doc.text(tr2en(`Saglam Cikan: ${prodReport.value?.aggregate?.total_produced || 0} | Islenen: ${prodReport.value?.aggregate?.total_processed || 0} | Fire: ${prodReport.value?.aggregate?.total_scrap || 0}`), 14, 28)
    
    const rows = prodReport.value?.logs?.map(l => [
      tr2en(l.task_title), tr2en(l.model_code), tr2en(l.team), tr2en(l.worker),
      l.target_qty, l.produced_qty, l.scrap_qty
    ]) || []
    
    autoTable(doc, {
      startY: 35,
      head: [['Gorev', 'Kalem Kodu', 'Ekip', 'Isci', 'Hedef', 'Islenen', 'Fire']],
      body: rows,
      theme: 'grid',
      headStyles: { fillColor: [40, 167, 69] }
    })
    doc.save(`Uretim_Raporu_${prodFilters.value.date}.pdf`)
    
  } else if (activeTab.value.startsWith('team_')) {
    const teamName = activeTeam.value?.name || 'Ekip'
    doc.text(tr2en(`${teamName} Raporu - ${teamDate.value}`), 14, 20)
    doc.setFontSize(11)
    doc.text(tr2en(`Kayit Sayisi: ${currentTeamReport.value?.logs?.length || 0}`), 14, 28)
    
    let head = []
    let body = []
    let themeColor = [79, 110, 247] // Standard blue

    if (isPvcTeam.value) {
      head = [['Gorev/Siparis', 'Kalem', 'Personel', 'Renk', 'Rulo Boy', 'Metre', 'Kesim Olcusu', 'Aciklama']]
      body = currentTeamReport.value?.logs?.map(l => [
        tr2en(l.task_title), tr2en(l.model_code), tr2en(l.worker),
        tr2en(l.pvc_color), tr2en(l.pvc_roll_size), l.pvc_meters,
        tr2en(l.pvc_cut_size), tr2en(l.activity_notes)
      ]) || []
      themeColor = [16, 185, 129] // Emerald green
    } else if (isGibenTeam.value) {
      head = [['Gorev/Siparis', 'Kalem', 'Personel', 'Yapilan Is', 'Tabaka Olcusu', 'Adet', 'Aciklama']]
      body = currentTeamReport.value?.logs?.map(l => [
        tr2en(l.task_title), tr2en(l.model_code), tr2en(l.worker),
        tr2en(l.work_description), tr2en(l.giben_plate_size),
        l.produced_qty, tr2en(l.activity_notes)
      ]) || []
      themeColor = [245, 158, 11] // Amber orange
    } else {
      // Standard / CNC Ekipleri
      head = [['Gorev/Siparis', 'Kalem', 'Personel', 'Saat', 'Yapilan Is', 'Uret / Fire', 'Fire Yeri', 'Aciklama']]
      body = currentTeamReport.value?.logs?.map(l => [
        tr2en(l.task_title), tr2en(l.model_code), tr2en(l.worker),
        l.working_hours, tr2en(l.work_description),
        `${l.produced_qty} / ${l.scrap_qty}`, tr2en(l.scrap_location),
        tr2en(l.activity_notes)
      ]) || []
      themeColor = [139, 92, 246] // Purple
    }

    autoTable(doc, {
      startY: 35,
      head: head,
      body: body,
      theme: 'grid',
      headStyles: { fillColor: themeColor }
    })
    doc.save(`${tr2en(teamName.replace(/\s+/g, '_'))}_Raporu_${teamDate.value}.pdf`)
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
