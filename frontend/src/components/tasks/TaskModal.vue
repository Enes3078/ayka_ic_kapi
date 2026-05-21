<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-content" style="max-width: 800px;">
      <div class="modal-header">
        <h2>{{ isEdit ? 'Görevi Düzenle' : 'Yeni Görev Oluştur' }}</h2>
        <button class="btn btn-ghost btn-icon" @click="$emit('close')">✕</button>
      </div>

      <div class="modal-body">
        <!-- Task Fields -->
        <div class="form-row">
          <div class="form-group" style="flex:2">
            <label class="form-label">Başlık *</label>
            <input v-model="form.title" class="form-input" placeholder="Görev başlığı" required />
          </div>
          <div class="form-group" style="flex:1">
            <label class="form-label">Öncelik</label>
            <select v-model="form.priority" class="form-select">
              <option value="low">Düşük</option>
              <option value="medium">Orta</option>
              <option value="high">Yüksek</option>
              <option value="urgent">Acil</option>
            </select>
          </div>
        </div>

        <div class="form-group mt-12">
          <label class="form-label">Açıklama</label>
          <textarea v-model="form.description" class="form-textarea" placeholder="Görev açıklaması..."></textarea>
        </div>

        <div class="form-row mt-12">
          <div class="form-group">
            <label class="form-label">Durum</label>
            <select v-model="form.status" class="form-select">
              <option value="todo">Yapılacak</option>
              <option value="in_progress">Devam Ediyor</option>
              <option value="done">Tamamlandı</option>
            </select>
          </div>
        </div>

        <div class="form-row mt-12">
          <div class="form-group">
            <label class="form-label">Başlangıç</label>
            <input v-model="form.start_date" type="datetime-local" class="form-input" @change="recalculateTaskTimes" />
          </div>
          <div class="form-group">
            <label class="form-label">Bitiş (Tahmini)</label>
            <input v-model="form.end_date" type="datetime-local" class="form-input" />
            <span class="text-xs text-muted">Üretim kalemlerine göre otomatik hesaplanır.</span>
          </div>
          <div class="form-group">
            <label class="form-label">Planlanan İş Yükü</label>
            <input v-model.number="form.planned_hours" type="number" step="0.01" class="form-input" readonly style="background: var(--bg-body); cursor: not-allowed;" />
            <span class="text-xs text-muted">Saat cinsinden toplam süre.</span>
          </div>
        </div>

        <!-- Product Lines Section -->
        <div class="section-divider">
          <h3 class="section-title">Üretim Kalemleri</h3>
          <button class="btn btn-secondary btn-sm" @click="addProductLine">＋ Kalem Ekle</button>
        </div>

        <div v-if="form.product_lines.length === 0" class="empty-state" style="padding:24px;">
          <div class="empty-state-text">En az 1 üretim kalemi ekleyin.</div>
        </div>

        <div v-for="(pl, index) in form.product_lines" :key="index" class="product-line-row">
          <div class="pl-header">
            <span class="pl-index">#{{ index + 1 }}</span>
            <button class="btn btn-ghost btn-sm" style="color: var(--accent-red);" @click="removeProductLine(index)">🗑</button>
          </div>

          <div class="form-group mb-12">
            <label class="form-label" style="color: var(--accent-blue);">Katalogdan Hızlı Seçim</label>
            <select v-model="pl.product" class="form-select" @change="onProductSelected(index)">
              <option :value="null">-- Özel (Manuel Giriş) --</option>
              <option v-for="prod in products" :key="prod.id" :value="prod.id">
                {{ prod.code }} - {{ prod.name }} ({{ prod.duration_minutes }} dk)
              </option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Model Kodu *</label>
              <input v-model="pl.model_code" class="form-input" placeholder="MK-001" required />
            </div>
            <div class="form-group">
              <label class="form-label">Varyant / Renk</label>
              <input v-model="pl.variant" class="form-input" placeholder="Örn: Sol, Beyaz" />
            </div>
            <div class="form-group">
              <label class="form-label">Ölçü</label>
              <input v-model="pl.dimension" class="form-input" placeholder="100x200" />
            </div>
          </div>

          <div class="form-row mt-12">
            <div class="form-group">
              <label class="form-label">Birim Tipi</label>
              <select v-model="pl.unit_type" class="form-select">
                <option value="adet">Adet</option>
                <option value="metre">Metre</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Miktar *</label>
              <input v-model.number="pl.quantity" type="number" min="1" class="form-input" @input="recalculateTaskTimes" />
            </div>
            <div class="form-group">
              <label class="form-label">Birim Süre (dk)</label>
              <input v-model.number="pl.unit_duration_minutes" type="number" class="form-input" @input="pl.planning_mode='fixed'; recalculateTaskTimes()" />
            </div>
            <div class="form-group">
              <label class="form-label">Bıçak Derinliği</label>
              <input v-model.number="pl.blade_depth" type="number" step="0.01" class="form-input" />
            </div>
          </div>

          <div class="form-row mt-12">
            <div class="form-group" style="flex: 2;">
              <label class="form-label">Kısa Açıklama / Talimat *</label>
              <textarea v-model="pl.brief_intro" class="form-textarea" placeholder="Üretim talimatı/açıklaması..." required rows="2" maxlength="600"></textarea>
            </div>
            <div class="form-group" style="flex: 1;">
              <label class="form-label">Görsel (Opsiyonel)</label>
              <input type="file" accept="image/*" class="form-input" style="padding: 6px;" @change="handleImageUpload($event, index)" />
              <img v-if="pl.image_base64" :src="pl.image_base64" style="width: 100%; height: 50px; object-fit: cover; margin-top: 8px; border-radius: 4px; border: 1px solid var(--border-color);" />
            </div>
          </div>

          <div class="form-group mt-12">
            <div class="flex justify-between items-end mb-4">
              <label class="form-label">İş Akışı Rotası (Sırasıyla Görev Alacak Ekipler)</label>
              
              <div class="flex items-center gap-8" style="min-width: 250px;">
                <label class="form-label text-xs" style="margin: 0; color: var(--accent-purple);">Şablondan Yükle:</label>
                <select class="form-select" style="padding: 4px 8px; font-size: 0.85rem;" @change="loadTemplateToLine(pl, $event)">
                  <option value="">-- Şablon Seç --</option>
                  <option v-for="tpl in workflowTemplates" :key="tpl.id" :value="tpl.id">{{ tpl.name }}</option>
                </select>
              </div>
            </div>

            <div class="flex flex-col gap-8 mt-4">
              <div v-for="(step, sIndex) in pl.workflow_team_ids" :key="sIndex" class="flex items-center gap-8">
                <span class="text-sm font-bold" style="color: var(--accent-blue);">{{ sIndex + 1 }}.</span>
                <select v-model="pl.workflow_team_ids[sIndex]" class="form-select" style="flex:1;">
                  <option :value="null">Ekip Seçin</option>
                  <option v-for="t in teams" :key="t.id" :value="t.id">{{ t.name }}</option>
                </select>
                <button class="btn btn-ghost btn-sm" style="color: var(--accent-red);" @click="removeWorkflowStep(pl, sIndex)">✕</button>
              </div>
              <button class="btn btn-secondary btn-sm" style="align-self: flex-start; margin-top: 4px;" @click="addWorkflowStep(pl)">
                ＋ Adım Ekle
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer" style="display:flex; justify-content:space-between; align-items:center;">
        <div style="display:flex; align-items:center; gap: 12px;">
          <button v-if="isEdit" class="btn btn-ghost" style="color: var(--accent-red);" @click="confirmDelete" :disabled="saving">
            🗑 Görevi Sil
          </button>
          <div v-if="error" class="login-error">{{ error }}</div>
        </div>
        <div style="display:flex; gap: 12px;">
          <button class="btn btn-secondary" @click="$emit('close')">İptal</button>
          <button class="btn btn-primary" :disabled="saving" @click="handleSave">
            <span v-if="saving" class="spinner" style="width:16px;height:16px;border-width:2px;"></span>
            <span v-else>{{ isEdit ? 'Güncelle' : 'Oluştur' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useTaskStore } from '../../stores/tasks'
import { useAuthStore } from '../../stores/auth'
import api from '../../api'

const props = defineProps({
  task: { type: Object, default: null },
  draftData: { type: Object, default: null },
})
const emit = defineEmits(['close', 'saved'])

const taskStore = useTaskStore()
const auth = useAuthStore()
const showToast = inject('showToast')

const isEdit = computed(() => !!props.task)
const saving = ref(false)
const error = ref('')
const teams = ref([])
const products = ref([])
const workflowTemplates = ref([])
const systemSettings = ref(null)

const emptyProductLine = () => ({
  product: null,
  model_code: '',
  variant: '',
  dimension: '',
  image_base64: '',
  blade_depth: 0,
  brief_intro: '',
  unit_type: 'adet',
  quantity: 1,
  planning_mode: 'manual',
  unit_duration_minutes: 0,
  workflow_team_ids: [],
})

const form = ref({
  title: '',
  description: '',
  status: 'todo',
  priority: 'medium',
  start_date: '',
  end_date: '',
  planned_hours: 0,
  product_lines: [emptyProductLine()],
})

onMounted(async () => {
  teams.value = taskStore.teams.length ? taskStore.teams : await taskStore.fetchTeams()
  await fetchProducts()
  await fetchTemplates()
  await fetchSettings()

  if (props.task) {
    const t = props.task
    form.value = {
      title: t.title || '',
      description: t.description || '',
      status: t.status || 'todo',
      priority: t.priority || 'medium',
      start_date: t.start_date ? t.start_date.slice(0, 16) : '',
      end_date: t.end_date ? t.end_date.slice(0, 16) : '',
      planned_hours: t.planned_hours || 0,
      product_lines: t.product_lines?.length
        ? t.product_lines.map(pl => ({ ...pl }))
        : [emptyProductLine()],
    }
  } else if (props.draftData) {
    form.value.title = props.draftData.draft_title || ''
    form.value.description = props.draftData.draft_description || ''
    form.value.product_lines = props.draftData.product_lines?.length
      ? props.draftData.product_lines.map(pl => ({ ...pl, workflow_team_ids: pl.workflow_team_ids || [] }))
      : [emptyProductLine()]
  }
})

async function fetchProducts() {
  try {
    const res = await api.get('/tasks/products/')
    products.value = res.data.results || res.data
  } catch (err) {
    console.error('Ürünler yüklenemedi', err)
  }
}

async function fetchTemplates() {
  try {
    const res = await api.get('/tasks/workflow-templates/')
    workflowTemplates.value = res.data.results || res.data
  } catch (err) {
    console.error('Şablonlar çekilemedi', err)
  }
}

async function fetchSettings() {
  try {
    const res = await api.get('/tasks/settings/')
    systemSettings.value = res.data
  } catch (err) {
    console.error('Ayarlar çekilemedi', err)
  }
}

function onProductSelected(index) {
  const pl = form.value.product_lines[index]
  if (!pl.product) return

  const prod = products.value.find(p => p.id === pl.product)
  if (prod) {
    pl.model_code = `${prod.code} - ${prod.name}`
    pl.unit_duration_minutes = prod.duration_minutes
    pl.planning_mode = 'fixed'
    
    // Boyutları birleştir
    let dims = []
    if (prod.width_mm && prod.length_mm) {
      dims.push(`${prod.width_mm}x${prod.length_mm}`)
    }
    if (prod.thickness_mm) {
      dims.push(`k:${prod.thickness_mm}mm`)
    }
    if (prod.additional_dimensions) {
      dims.push(prod.additional_dimensions)
    }
    pl.dimension = dims.join(' | ')
    
    // Bıçak
    if (prod.blade_max_mm) {
      pl.blade_depth = parseFloat(prod.blade_max_mm)
    }

    recalculateTaskTimes()
  }
}

function handleImageUpload(event, index) {
  const file = event.target.files[0]
  if (!file) return

  // Sadece küçük resimler için FileReader (Base64)
  const reader = new FileReader()
  reader.onload = (e) => {
    form.value.product_lines[index].image_base64 = e.target.result
  }
  reader.readAsDataURL(file)
}

function addWorkingMinutes(startDate, minutesToAdd) {
  if (!systemSettings.value) {
    // Ayarlar yüklenmediyse düz saat ekle
    const sd = new Date(startDate)
    sd.setMinutes(sd.getMinutes() + minutesToAdd)
    return sd
  }
  
  const s = systemSettings.value
  const workDays = s.work_days ? s.work_days.split(',').map(Number) : [0,1,2,3,4,5]
  
  const [startH, startM] = s.work_start_time.split(':').map(Number)
  let endH, endM
  if (s.overtime_end_time) {
    [endH, endM] = s.overtime_end_time.split(':').map(Number)
  } else {
    [endH, endM] = s.work_end_time.split(':').map(Number)
  }

  let currentDate = new Date(startDate)
  let remainingMinutes = minutesToAdd
  
  // Maksimum sonsuz döngü koruması
  let loopCount = 0
  
  while (remainingMinutes > 0 && loopCount < 1000) {
    loopCount++
    const dayOfWeek = currentDate.getDay() // 0 Pazar, 1 Pzt
    const backendDay = (dayOfWeek + 6) % 7 // 0 Pzt, 6 Pazar
    
    // Tatil günüyse doğrudan ertesi gün mesai başına atla
    if (!workDays.includes(backendDay)) {
       currentDate.setDate(currentDate.getDate() + 1)
       currentDate.setHours(startH, startM, 0, 0)
       continue
    }
    
    const currentH = currentDate.getHours()
    const currentM = currentDate.getMinutes()
    const currentTotalM = currentH * 60 + currentM
    const shiftStartM = startH * 60 + startM
    const shiftEndM = endH * 60 + endM
    
    // Mesai başlamadıysa mesai başına al
    if (currentTotalM < shiftStartM) {
       currentDate.setHours(startH, startM, 0, 0)
       continue
    }
    
    // Mesai bittiyse ertesi gün mesai başına al
    if (currentTotalM >= shiftEndM) {
       currentDate.setDate(currentDate.getDate() + 1)
       currentDate.setHours(startH, startM, 0, 0)
       continue
    }
    
    // Mesai içindeyiz, bitişe ne kadar var?
    const minutesToShiftEnd = shiftEndM - currentTotalM
    if (remainingMinutes <= minutesToShiftEnd) {
       currentDate.setMinutes(currentDate.getMinutes() + remainingMinutes)
       remainingMinutes = 0
    } else {
       remainingMinutes -= minutesToShiftEnd
       currentDate.setDate(currentDate.getDate() + 1)
       currentDate.setHours(startH, startM, 0, 0)
    }
  }
  
  return currentDate
}

function recalculateTaskTimes() {
  let totalMinutes = 0
  
  form.value.product_lines.forEach(pl => {
    if (pl.unit_duration_minutes > 0) {
      totalMinutes += (pl.quantity * pl.unit_duration_minutes)
      pl.planning_mode = 'fixed'
    }
  })

  // Planlanan Saat
  form.value.planned_hours = parseFloat((totalMinutes / 60).toFixed(2))

  // Bitiş Tarihi Tahmini (Başlangıç varsa ve süre hesaplandıysa)
  if (form.value.start_date && totalMinutes > 0) {
    const finalDate = addWorkingMinutes(form.value.start_date, totalMinutes)
    
    // local string formata (YYYY-MM-DDThh:mm) çevirme
    const offset = finalDate.getTimezoneOffset()
    const localDate = new Date(finalDate.getTime() - (offset*60*1000))
    form.value.end_date = localDate.toISOString().slice(0,16)
  }
}

function addProductLine() {
  form.value.product_lines.push(emptyProductLine())
}

function removeProductLine(index) {
  if (form.value.product_lines.length <= 1) {
    showToast('En az 1 üretim kalemi gereklidir.', 'warning')
    return
  }
  form.value.product_lines.splice(index, 1)
  recalculateTaskTimes()
}

function addWorkflowStep(pl) { 
  if (!pl.workflow_team_ids) pl.workflow_team_ids = []
  pl.workflow_team_ids.push(null) 
}
function removeWorkflowStep(pl, sIndex) { 
  if (pl.workflow_team_ids) pl.workflow_team_ids.splice(sIndex, 1) 
}

function loadTemplateToLine(pl, event) {
  const templateId = event.target.value;
  if (!templateId) return
  const tpl = workflowTemplates.value.find(t => t.id == templateId)
  if (tpl) {
    pl.workflow_team_ids = [...tpl.steps]
  }
  // Reset select after applying so it can be re-selected if needed
  event.target.value = ""
}

async function handleSave() {
  error.value = ''

  // 1. Görev Başlığı Doğrulaması
  if (!form.value.title || !form.value.title.trim()) {
    error.value = 'Eksik veri girdiniz: Görev başlığı doldurulmalıdır.'
    showToast('Eksik veri girdiniz: Görev başlığı boş bırakılamaz.', 'error')
    return
  }

  // 2. Üretim Kalemleri Sayı Doğrulaması
  if (form.value.product_lines.length === 0) {
    error.value = 'Eksik veri girdiniz: En az 1 üretim kalemi eklemelisiniz.'
    showToast('Eksik veri girdiniz: En az 1 üretim kalemi gereklidir.', 'error')
    return
  }

  // 3. Her Bir Üretim Kaleminin Kendi Doğrulamaları
  for (let i = 0; i < form.value.product_lines.length; i++) {
    const pl = form.value.product_lines[i]
    const plNum = i + 1

    if (!pl.model_code || !pl.model_code.trim()) {
      error.value = `Eksik veri girdiniz: #${plNum} numaralı üretim kaleminin Model Kodu doldurulmalıdır.`
      showToast(`Eksik veri girdiniz: #${plNum} numaralı kalemin Model Kodu boş bırakılamaz.`, 'error')
      return
    }

    if (pl.quantity === undefined || pl.quantity === null || pl.quantity < 1) {
      error.value = `Eksik veri girdiniz: #${plNum} numaralı üretim kaleminin Miktarı en az 1 olmalıdır.`
      showToast(`Eksik veri girdiniz: #${plNum} numaralı kalemin Miktarı en az 1 olmalıdır.`, 'error')
      return
    }

    if (!pl.brief_intro || !pl.brief_intro.trim()) {
      error.value = `Eksik veri girdiniz: #${plNum} numaralı üretim kaleminin Kısa Açıklama / Talimat alanı doldurulmalıdır.`
      showToast(`Eksik veri girdiniz: #${plNum} numaralı kalemin Talimat alanı boş bırakılamaz.`, 'error')
      return
    }

    // İş akışı adımları eklendiyse, ekip seçimlerinin dolu olup olmadığını kontrol et
    if (pl.workflow_team_ids && pl.workflow_team_ids.length > 0) {
      if (pl.workflow_team_ids.some(id => id === null)) {
        error.value = `Eksik veri girdiniz: #${plNum} numaralı üretim kaleminin İş Akışı Rotasında seçilmemiş ekipler var.`
        showToast('Lütfen tüm ekipleri seçin veya boş adımları silin.', 'error')
        return
      }
    }
  }

  saving.value = true
  try {
    const payload = {
      ...form.value,
      owner: auth.user.id,
      start_date: form.value.start_date || null,
      end_date: form.value.end_date || null,
      product_lines: form.value.product_lines.map(pl => {
        const filteredTeams = pl.workflow_team_ids.filter(id => id !== null)
        return {
          ...pl,
          workflow_team_ids: filteredTeams
        }
      }).filter(pl => pl.model_code.trim()),
    }

    if (isEdit.value) {
      await taskStore.updateTask(props.task.id, payload)
    } else {
      await taskStore.createTask(payload)
    }
    emit('saved')
  } catch (err) {
    const data = err.response?.data
    if (typeof data === 'object') {
      error.value = Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ')
    } else {
      error.value = 'Kaydetme sırasında hata oluştu.'
    }
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  if (confirm(`"${form.value.title}" görevini silmek istediğinize emin misiniz?`)) {
    saving.value = true
    try {
      await taskStore.deleteTask(props.task.id)
      emit('saved')
      showToast('Görev başarıyla silindi.', 'success')
    } catch (err) {
      error.value = 'Silme işlemi başarısız oldu.'
    } finally {
      saving.value = false
    }
  }
}
</script>

<style scoped>
.form-row { display: flex; gap: 16px; }
.form-row .form-group { flex: 1; }

.section-divider {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 28px; margin-bottom: 16px; padding-top: 20px;
  border-top: 1px solid var(--border-color);
}
.section-title { font-size: 1rem; font-weight: 700; color: var(--accent-blue); }

.product-line-row {
  background: var(--bg-input); border: 1px solid var(--border-color);
  border-radius: var(--radius-md); padding: 16px; margin-bottom: 12px;
  animation: slideUp var(--transition-fast);
}
.pl-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.pl-index { font-size: 0.8rem; font-weight: 700; color: var(--accent-blue); }
</style>
