<template>
  <div class="page-content">
    <div class="page-header">
      <h2 class="page-title">{{ selectedTask ? '← ' + selectedTask.task_title : 'Görevlerim' }}</h2>
      <div class="flex gap-12">
        <button v-if="selectedTask" class="btn btn-secondary" @click="selectedTask = null">← Görev Listesine Dön</button>
        <button class="btn btn-secondary" @click="fetchQueue">🔄 Yenile</button>
        <button class="btn btn-primary" style="font-size: 1.1rem; padding: 10px 20px;" @click="openBulkReportModal">🌅 Gün Sonu Raporu Doldur</button>
      </div>
    </div>

    <div v-if="loading" class="loading-container"><div class="spinner"></div></div>

    <!-- ═══════════ GÖREV LİSTESİ ═══════════ -->
    <div v-else-if="!selectedTask">
      <div v-if="tasks.length === 0" class="empty-state">
        <div class="empty-state-icon">✅</div>
        <div class="empty-state-text">Şu an ekibinizde bekleyen görev bulunmuyor.</div>
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-16">
        <div v-for="t in tasks" :key="t.task_id" class="card task-card" @click="selectedTask = t">
          <div class="flex justify-between items-start mb-8">
            <span :class="['badge', `badge-${t.task_priority}`]">{{ priorityLabel(t.task_priority) }}</span>
            <span v-if="t.product_lines.every(pl => pl.is_upcoming)" class="badge" style="background:#fef08a;color:#854d0e;">⏳ Yaklaşan</span>
            <span v-else :class="['badge', `badge-${t.task_status.replace('_','-')}`]">{{ statusLabel(t.task_status) }}</span>
          </div>
          <h3 class="task-card-title">{{ t.task_title }}</h3>
          <p v-if="t.task_description" class="text-sm text-muted mb-12" style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">{{ t.task_description }}</p>
          <div class="flex justify-between text-sm mb-8">
            <span>📦 {{ t.total_items }} kalem</span>
            <span style="color:var(--accent-orange);">⏳ Kalan: {{ t.total_remaining }}</span>
          </div>
          <div class="progress-bar-bg"><div class="progress-bar-fill" :style="{ width: t.total_progress + '%' }"></div></div>
          <div class="text-xs text-muted mt-4 text-right">{{ t.total_progress }}% tamamlandı</div>
          <div v-if="t.task_due_date" class="text-xs mt-8" style="color:var(--accent-orange);">📅 Son Tarih: {{ formatDate(t.task_due_date) }}</div>
        </div>
      </div>
    </div>

    <!-- ═══════════ GÖREV DETAY (KALEMLER) ═══════════ -->
    <div v-else>
      <div class="card mb-16" style="border-left:4px solid var(--primary-color);">
        <div class="flex justify-between items-center">
          <div>
            <div class="text-sm text-muted">Görev Sahibi: {{ selectedTask.task_owner }}</div>
            <div class="text-sm text-muted mt-4" v-if="selectedTask.task_description">{{ selectedTask.task_description }}</div>
          </div>
          <div class="text-right">
            <div class="text-sm">Toplam İlerleme</div>
            <div style="font-size:1.4rem;font-weight:800;color:var(--primary-color);">{{ selectedTask.total_progress }}%</div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-16">
        <div v-for="pl in selectedTask.product_lines" :key="pl.id" class="card" style="border-top:3px solid var(--accent-blue);">
          <img v-if="pl.image_base64" :src="pl.image_base64" alt="Ürün" style="width:100%;height:140px;object-fit:cover;border-radius:4px;margin-bottom:12px;border:1px solid var(--border-color);" />
          <div class="flex justify-between items-start mb-8">
            <h3 style="font-size:1.05rem;font-weight:700;">{{ pl.model_code }}</h3>
            <span class="badge badge-high">Hedef: {{ pl.quantity }} {{ pl.unit_type }}</span>
          </div>
          <div v-if="pl.variant || pl.dimension || pl.color" class="text-sm text-muted mb-8">
            <span v-if="pl.variant">Varyant: {{ pl.variant }} | </span>
            <span v-if="pl.color">Renk: {{ pl.color }} | </span>
            <span v-if="pl.dimension">Ölçü: {{ pl.dimension }}</span>
          </div>
          <div v-if="pl.brief_intro" class="text-sm mb-12 p-8 rounded" style="background:var(--bg-input);border-left:3px solid var(--accent-blue);">{{ pl.brief_intro }}</div>

          <div class="stats-row mb-12">
            <div class="stat-item stat-green"><span class="stat-label">Üretilen</span><span class="stat-value">{{ pl.qty_produced }}</span></div>
            <div class="stat-item stat-orange"><span class="stat-label">Kalan</span><span class="stat-value">{{ pl.remaining }}</span></div>
            <div class="stat-item stat-red"><span class="stat-label">Fire</span><span class="stat-value">{{ pl.fire_qty }}</span></div>
          </div>

          <div class="progress-bar-bg"><div class="progress-bar-fill" :style="{ width: pl.completion_rate + '%' }"></div></div>
        </div>
      </div>
    </div>

    <!-- ═══════════ GÜN SONU RAPORU MODALI (TOPLU GİRİŞ) ═══════════ -->
    <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
      <div class="modal-content" style="max-width:1100px; width: 95%; max-height: 90vh; overflow-y: auto;">
        <div class="modal-header sticky top-0 bg-white z-10 pb-12 mb-16" style="border-bottom:1px solid var(--border-color);">
          <h2>🌅 Gün Sonu Raporu</h2>
          <button class="btn btn-ghost btn-icon" @click="showModal = false">✕</button>
        </div>
        
        <div class="modal-body">
          <p class="text-sm text-muted mb-16">Bugün üretim yaptığınız kalemlerin karşısına miktarları girin. İşlem yapmadığınız kalemleri boş bırakın.</p>
          
          <form @submit.prevent="submitBulkReport">
            <!-- 1. TABLO KISMI: Görevler ve Kalemler -->
            <div class="table-container mb-24" style="max-height: 400px; overflow-y: auto; border: 1px solid var(--border-color); border-radius: var(--radius-sm);">
              <table class="w-full text-left border-collapse">
                <thead class="bg-slate-50 sticky top-0 z-10" style="box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                  <tr>
                    <th class="p-12 text-sm font-bold text-slate-600 border-b">Görev & Kalem</th>
                    <th class="p-12 text-sm font-bold text-slate-600 border-b w-24">Hedef</th>
                    <th class="p-12 text-sm font-bold text-slate-600 border-b w-24">Kalan</th>
                    <th v-if="!canFillPvcReport" class="p-12 text-sm font-bold text-slate-600 border-b w-32">Üretilen</th>
                    <th v-else class="p-12 text-sm font-bold text-slate-600 border-b w-32 text-center">İşlem</th>
                    <th class="p-12 text-sm font-bold text-slate-600 border-b w-32">Fire</th>
                    <th class="p-12 text-sm font-bold text-slate-600 border-b text-center w-24">Devret</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="t in tasks" :key="'t-'+t.task_id">
                    <!-- Görev Başlığı Satırı -->
                    <tr class="bg-slate-100/50">
                      <td colspan="6" class="p-12 font-bold text-sm" style="color: var(--accent-blue); border-bottom: 1px solid var(--border-color);">
                        📁 {{ t.task_title }}
                      </td>
                    </tr>
                    <!-- Kalem Satırları -->
                    <template v-for="pl in t.product_lines" :key="pl.id">
                      <tr class="border-b transition-colors" :class="pl.is_upcoming ? 'bg-slate-100 opacity-70' : 'hover:bg-slate-50'">
                        <td class="p-12">
                          <div style="font-weight: 600;">
                            <span v-if="pl.is_upcoming" class="text-xs font-bold text-orange-600 mr-4">⏳ Yaklaşan</span>
                            {{ pl.model_code }}
                          </div>
                          <div class="text-xs text-muted" v-if="pl.variant || pl.color || pl.dimension">
                            {{ pl.variant }} {{ pl.color }} {{ pl.dimension }}
                          </div>
                        </td>
                        <td class="p-12 font-bold text-slate-600">{{ pl.quantity }} {{ pl.unit_type }}</td>
                        <td class="p-12 font-bold text-orange-600">{{ pl.remaining }}</td>
                        <td v-if="!canFillPvcReport" class="p-12">
                          <input v-model.number="bulkData[pl.id].qty_produced" type="number" min="0" :max="pl.remaining" class="form-input text-center" style="width: 80px;" placeholder="0" :disabled="pl.is_upcoming" />
                        </td>
                        <td v-else class="p-12 text-center">
                          <label class="flex items-center justify-center gap-4 cursor-pointer" :class="{'opacity-50': pl.is_upcoming}">
                            <input v-model="bulkData[pl.id].is_processed" type="checkbox" style="width: 18px; height: 18px;" :disabled="pl.is_upcoming" />
                            <span class="text-xs font-bold text-slate-600">Seç</span>
                          </label>
                        </td>
                        <td class="p-12">
                          <input v-model.number="bulkData[pl.id].fire_qty" type="number" min="0" class="form-input text-center" style="width: 80px;" placeholder="0" :disabled="pl.is_upcoming" />
                        </td>
                        <td class="p-12 text-center">
                          <input v-model="bulkData[pl.id].handover" type="checkbox" style="width: 18px; height: 18px; cursor: pointer;" :disabled="pl.is_upcoming" />
                        </td>
                      </tr>
                      
                      <!-- Accordion Detay Satırı (Üretim veya Fire Varsa) -->
                      <tr v-if="bulkData[pl.id].qty_produced > 0 || bulkData[pl.id].fire_qty > 0 || bulkData[pl.id].is_processed" class="bg-slate-50 border-b">
                        <td colspan="6" class="p-12">
                          <div class="grid grid-cols-1 md:grid-cols-2 gap-8 pl-16" style="border-left: 3px solid var(--primary-color);">
                            <div v-if="bulkData[pl.id].qty_produced > 0 || bulkData[pl.id].is_processed" class="form-group flex flex-col mb-0">
                              <label class="text-xs text-muted mb-4 font-bold">Yapılan İş Açıklaması</label>
                              <input v-model="bulkData[pl.id].work_description" type="text" class="form-input text-sm" placeholder="Yapılan işi kısaca açıklayın (örn: 2 takım ebatlandı)" />
                            </div>
                            <div v-if="bulkData[pl.id].fire_qty > 0" class="form-group flex flex-col mb-0">
                              <label class="text-xs text-red-600 mb-4 font-bold">Fire Sebebi *</label>
                              <input v-model="bulkData[pl.id].fire_reason" type="text" class="form-input text-sm border-red-300" placeholder="Fire neden oldu?" required />
                            </div>
                            <div v-if="bulkData[pl.id].fire_qty > 0" class="form-group flex flex-col mb-0">
                              <label class="text-xs text-red-600 mb-4 font-bold">Fire Nerede (Hangi Aşamada)? *</label>
                              <input v-model="bulkData[pl.id].scrap_location" type="text" class="form-input text-sm border-red-300" placeholder="Örn: Kesim makinesinde" required />
                            </div>
                          </div>
                        </td>
                      </tr>
                    </template>
                  </template>
                </tbody>
              </table>
            </div>

            <!-- 2. ORTAK FAALİYET RAPORU KISMI -->
            <h3 class="font-bold text-lg mb-12 border-b pb-8">Genel Faaliyet Raporu</h3>

            <!-- Standart Faaliyet Raporu -->
            <div v-if="canFillStandardReport" class="report-section report-standard">
              <div class="form-group mb-12">
                <label class="form-label">Çalıştığım Saat Toplamı *</label>
                <input v-model.number="commonForm.working_hours" type="number" step="0.5" min="0.5" class="form-input" placeholder="Örn: 8.5" required />
              </div>
              <div class="form-group">
                <label class="form-label">Genel Ek Açıklamalar</label>
                <textarea v-model="commonForm.activity_notes" class="form-textarea" placeholder="Sorumluya iletmek istediğiniz notlar..." rows="2"></textarea>
              </div>
            </div>

            <!-- PVC Faaliyet Raporu -->
            <div v-if="canFillPvcReport" class="report-section report-pvc">
              <div class="grid grid-cols-2 gap-12 mb-12">
                <div class="form-group"><label class="form-label">Kullanılan Ana Renk</label><input v-model="commonForm.pvc_color" type="text" class="form-input" placeholder="Ant. 2060" /></div>
                <div class="form-group"><label class="form-label">Rulo Boy (Genel)</label><input v-model="commonForm.pvc_roll_size" type="text" class="form-input" placeholder="1/141cm" /></div>
              </div>
              <div class="grid grid-cols-2 gap-12 mb-12">
                <div class="form-group"><label class="form-label">Toplam Metre</label><input v-model.number="commonForm.pvc_meters" type="number" step="0.1" min="0" class="form-input" /></div>
                <div class="form-group"><label class="form-label">Genel Kesim Ölçüsü</label><input v-model="commonForm.pvc_cut_size" type="text" class="form-input" /></div>
              </div>
              <div class="form-group"><label class="form-label">Genel Ek Açıklamalar</label><textarea v-model="commonForm.activity_notes" class="form-textarea" rows="2"></textarea></div>
            </div>

            <!-- Giben Faaliyet Raporu -->
            <div v-if="canFillGibenReport" class="report-section report-giben">
              <div class="form-group mb-12"><label class="form-label">Kullanılan Tabaka Ölçüsü (Genel)</label><input v-model="commonForm.giben_plate_size" type="text" class="form-input" placeholder="2800 x 2100 x 6mm" /></div>
              <div class="form-group"><label class="form-label">Genel Ek Açıklamalar</label><textarea v-model="commonForm.activity_notes" class="form-textarea" rows="2"></textarea></div>
            </div>

            <!-- Stok Kullanımı (Giben/PVC vb.) -->
            <div v-if="canUseStock" class="report-section report-stock mt-12">
              <h4 class="font-bold text-md mb-8 text-purple-700">📦 Stoktan Toplam Kullanım</h4>
              
              <div v-for="(stock, index) in commonForm.used_stocks" :key="index" class="flex gap-12 items-end mb-8 pb-8" :class="{'border-b border-purple-100': commonForm.used_stocks.length > 1}">
                <div class="flex-1">
                  <label class="form-label" v-if="index === 0">Kullanılan Stok Kalemi</label>
                  <select v-model="stock.item_id" class="form-select">
                    <option :value="null">-- Stok Seçilmedi --</option>
                    <option v-for="st in stockItems" :key="st.id" :value="st.id">{{ st.name }} (Mevcut: {{ st.current_quantity }} {{ st.unit }})</option>
                  </select>
                </div>
                <div style="width: 120px;">
                  <label class="form-label" v-if="index === 0">Miktar</label>
                  <input v-model.number="stock.quantity" type="number" step="0.01" min="0.01" class="form-input" placeholder="0.00" />
                </div>
                <div v-if="commonForm.used_stocks.length > 1">
                  <button type="button" class="btn btn-ghost" style="color:red; padding: 8px;" @click="removeStock(index)">✕</button>
                </div>
              </div>
              <button type="button" class="btn btn-secondary text-sm mt-4" @click="addStock">+ Yeni Stok Ekle</button>
            </div>

            <div v-if="error" class="login-error my-12">{{ error }}</div>
            
            <div class="flex justify-end gap-12 mt-24 pt-16" style="border-top:1px solid var(--border-color);">
              <button type="button" class="btn btn-secondary" @click="showModal = false">İptal</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                <span v-if="saving" class="spinner" style="width:16px;height:16px;border-width:2px;"></span>
                <span v-else>💾 Tüm Girdileri Kaydet</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject, computed } from 'vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const showToast = inject('showToast')

const tasks = ref([])
const loading = ref(true)
const selectedTask = ref(null)

const showModal = ref(false)
const bulkData = ref({}) // Format: { productLineId: { qty_produced: 0, fire_qty: 0, handover: false } }
const commonForm = ref({})
const saving = ref(false)
const error = ref('')
const stockItems = ref([])

const myTeamName = computed(() => auth.user?.department || '')
const canUseStock = computed(() => { const n = myTeamName.value.toUpperCase(); return n.includes('GIBEN') || n.includes('GİBEN') || n.includes('PVC') })
const canFillPvcReport = computed(() => myTeamName.value.toUpperCase().includes('PVC'))
const canFillGibenReport = computed(() => { const n = myTeamName.value.toUpperCase(); return n.includes('GIBEN') || n.includes('GİBEN') })
const canFillStandardReport = computed(() => !canFillPvcReport.value && !canFillGibenReport.value)

onMounted(() => {
  fetchQueue()
  if (canUseStock.value) fetchStockItems()
})

async function fetchQueue() {
  loading.value = true
  try {
    const res = await api.get('/tasks/my-team-queue/')
    tasks.value = res.data
    // Seçili görev varsa verisini de güncelle
    if (selectedTask.value) {
      const updated = tasks.value.find(t => t.task_id === selectedTask.value.task_id)
      selectedTask.value = updated || null
    }
    
    // Bulk form data initialize
    bulkData.value = {}
    tasks.value.forEach(t => {
      t.product_lines.forEach(pl => {
        bulkData.value[pl.id] = { qty_produced: null, fire_qty: null, is_processed: false, handover: false, work_description: '', fire_reason: '', scrap_location: '' }
      })
    })

  } catch (err) {
    showToast('Görevler yüklenirken hata oluştu.', 'error')
  } finally {
    loading.value = false
  }
}

async function fetchStockItems() {
  try {
    const res = await api.get('/stock/items/')
    stockItems.value = res.data.results || res.data
  } catch (err) { console.error('Stok yüklenemedi', err) }
}

function openBulkReportModal() {
  if (tasks.value.length === 0) {
    showToast('Bekleyen göreviniz bulunmuyor.', 'info')
    return
  }

  // Auto-fill form verilerini topla (Renk ve Ebat)
  const colors = new Set()
  const dimensions = new Set()
  
  tasks.value.forEach(t => {
    t.product_lines.forEach(pl => {
      // Sadece çalışanın işlem yapabileceği (yaklaşan olmayan) kalemlerin verilerini al
      if (!pl.is_upcoming) {
        if (pl.color) colors.add(pl.color.trim())
        if (pl.dimension) dimensions.add(pl.dimension.trim())
      }
    })
  })

  // Reset bulk form
  Object.keys(bulkData.value).forEach(k => {
    bulkData.value[k] = { qty_produced: null, fire_qty: null, is_processed: false, handover: false, work_description: '', fire_reason: '', scrap_location: '' }
  })

  // Reset common form & Auto-fill
  commonForm.value = {
    working_hours: null, activity_notes: '',
    pvc_color: Array.from(colors).join(', '),
    pvc_roll_size: '', 
    pvc_meters: null, 
    pvc_cut_size: Array.from(dimensions).join(', '),
    giben_plate_size: Array.from(dimensions).join(', '),
    used_stocks: [{ item_id: null, quantity: null }]
  }
  
  error.value = ''
  showModal.value = true
}

function addStock() {
  if (!commonForm.value.used_stocks) commonForm.value.used_stocks = []
  commonForm.value.used_stocks.push({ item_id: null, quantity: null })
}

function removeStock(index) {
  if (commonForm.value.used_stocks) {
    commonForm.value.used_stocks.splice(index, 1)
  }
}

async function submitBulkReport() {
  // 1. Hangi kalemler doldurulmuş bul (qty > 0 veya fire > 0 veya handover == true)
  const linesToSubmit = []
  for (const plId in bulkData.value) {
    const d = bulkData.value[plId]
    const q = d.qty_produced || 0
    const f = d.fire_qty || 0
    const p = d.is_processed || false
    if (q > 0 || f > 0 || d.handover || p) {
      
      // Doğrulama: Fire varsa sebep ve konum zorunlu
      if (f > 0 && (!d.fire_reason?.trim() || !d.scrap_location?.trim())) {
        error.value = 'Lütfen fire girdiğiniz kalemler için "Fire Sebebi" ve "Fire Nerede" alanlarını eksiksiz doldurun.'
        return
      }

      linesToSubmit.push({
        id: plId,
        qty_produced: p && q === 0 ? 0 : q, // Eğer sadece Seç işaretlendiyse 0 gönder
        fire_qty: f,
        handover: d.handover,
        work_description: d.work_description || '',
        fire_reason: d.fire_reason || '',
        scrap_location: d.scrap_location || ''
      })
    }
  }

  if (linesToSubmit.length === 0) {
    error.value = 'Lütfen tablodan en az bir kaleme üretim/fire miktarı girin veya devret seçeneğini işaretleyin.'
    return
  }

  saving.value = true
  error.value = ''

  try {
    // 2. Her bir kalem için log-production API isteği oluştur
    const promises = linesToSubmit.map(item => {
      // API'ye gönderilecek payload (Ortak Faaliyet Bilgileri + Bu Kaleme Özel Üretim Bilgisi)
      const payload = {
        ...commonForm.value,
        qty_produced: item.qty_produced,
        fire_qty: item.fire_qty,
        handover: item.handover,
        work_description: item.work_description,
        fire_reason: item.fire_reason,
        scrap_location: item.scrap_location,
        used_stocks: commonForm.value.used_stocks ? commonForm.value.used_stocks.filter(s => s.item_id && s.quantity) : []
      }
      return api.post(`/tasks/product-lines/${item.id}/log-production/`, payload)
    })

    // 3. Tüm istekleri aynı anda (paralel) gönder ve bekle
    await Promise.all(promises)

    showToast(`${linesToSubmit.length} kalem için gün sonu raporu başarıyla kaydedildi.`, 'success')
    showModal.value = false
    await fetchQueue()
    
  } catch (err) {
    console.error(err)
    let backendMsg = ''
    if (err.response && err.response.data) {
        if (typeof err.response.data === 'string') backendMsg = err.response.data
        else if (err.response.data.detail) backendMsg = err.response.data.detail
        else backendMsg = JSON.stringify(err.response.data)
    }
    error.value = backendMsg ? `Kayıt Hatası: ${backendMsg}` : 'Kaydetme sırasında bir hata oluştu. Lütfen sayfayı yenileyip kontrol edin.'
  } finally {
    saving.value = false
  }
}

const statusLabels = { todo: 'Yapılacak', in_progress: 'Devam Ediyor', done: 'Tamamlandı' }
const priorityLabels = { low: 'Düşük', medium: 'Orta', high: 'Yüksek', urgent: 'Acil' }
const statusLabel = s => statusLabels[s] || s
const priorityLabel = p => priorityLabels[p] || p
function formatDate(d) { if (!d) return ''; return new Date(d).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' }) }
</script>

<style scoped>
.task-card { cursor: pointer; padding: 20px; transition: transform 0.15s, box-shadow 0.15s; }
.task-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.12); }
.task-card-title { font-size: 1.05rem; font-weight: 700; margin-bottom: 8px; line-height: 1.3; }

.progress-bar-bg { width: 100%; height: 8px; background: var(--bg-input); border-radius: 999px; overflow: hidden; }
.progress-bar-fill { height: 100%; background: linear-gradient(90deg, var(--accent-blue), var(--accent-green)); border-radius: 999px; transition: width 0.4s ease; }

.stats-row { display: flex; gap: 12px; }
.stat-item { flex: 1; padding: 8px 12px; border-radius: var(--radius-sm); text-align: center; }
.stat-label { display: block; font-size: 0.7rem; font-weight: 500; opacity: 0.8; }
.stat-value { display: block; font-size: 1.1rem; font-weight: 800; }
.stat-green { background: #f0fdf4; color: #15803d; }
.stat-orange { background: #fff7ed; color: #c2410c; }
.stat-red { background: #fef2f2; color: #dc2626; }
.stat-blue { background: #eff6ff; color: #1d4ed8; }

.report-section { margin-bottom: 16px; padding: 16px; background: var(--bg-input); border-radius: var(--radius-sm); border: 1px solid var(--border-color); }
.report-standard { border-left: 4px solid var(--accent-blue); }
.report-pvc { border-left: 4px solid var(--accent-green); }
.report-giben { border-left: 4px solid var(--accent-orange); }
.report-stock { border-left: 4px solid var(--accent-purple); }
</style>
