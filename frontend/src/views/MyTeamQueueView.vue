<template>
  <div class="page-content">
    <div class="page-header">
      <h2 class="page-title">İş Kuyruğum (Saha Ekranı)</h2>
      <button class="btn btn-secondary" @click="fetchQueue">🔄 Yenile</button>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
    </div>
    
    <div v-else-if="queue.length === 0" class="empty-state">
      <div class="empty-state-icon">✅</div>
      <div class="empty-state-text">Şu an ekibinizin sırasında bekleyen bir üretim kalemi bulunmuyor.</div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-16">
      <div v-for="item in queue" :key="item.id" class="card" style="border-top: 4px solid var(--primary-color);">
        <img v-if="item.image_base64" :src="item.image_base64" alt="Ürün Görseli" style="width: 100%; height: 160px; object-fit: cover; border-radius: 4px; margin-bottom: 12px; border: 1px solid var(--border-color);" />
        
        <div class="flex justify-between items-start mb-12">
          <h3 style="font-size: 1.1rem; font-weight: 700;">{{ item.model_code }}</h3>
          <span class="badge badge-high" style="font-size: 0.9rem;">Hedef: {{ item.quantity }} {{ item.unit_type }}</span>
        </div>
        
        <div class="text-sm text-muted mb-16" style="min-height: 40px;">
          <p v-if="item.brief_intro">{{ item.brief_intro }}</p>
          <p v-else>Açıklama girilmemiş.</p>
        </div>

        <div class="flex justify-between items-center mb-16">
          <div class="text-sm">
            Üretilen: <strong style="color: var(--accent-green); font-size: 1.1rem;">{{ item.qty_produced }}</strong>
          </div>
          <div class="text-sm">
            Fire: <strong style="color: var(--accent-red); font-size: 1.1rem;">{{ item.fire_qty }}</strong>
          </div>
        </div>
        
        <div class="w-full bg-slate-100 rounded-full h-8 mb-16">
          <div class="bg-primary h-8 rounded-full transition-all" :style="{ width: item.completion_rate + '%' }"></div>
        </div>

        <button class="btn btn-primary w-full" @click="openLogModal(item)">
          ⚙️ Üretim Kaydı & Devret
        </button>
      </div>
    </div>

    <!-- Log Production Modal -->
    <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
      <div class="modal-content" style="max-width: 400px;">
        <div class="modal-header">
          <h2>Üretim Kaydı</h2>
          <button class="btn btn-ghost btn-icon" @click="showModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="mb-16 pb-12" style="border-bottom: 1px solid var(--border-color);">
            <img v-if="selectedItem?.image_base64" :src="selectedItem.image_base64" alt="Ürün Görseli" style="width: 100%; max-height: 200px; object-fit: contain; border-radius: 4px; margin-bottom: 16px; background: #f8fafc; border: 1px solid var(--border-color);" />
            
            <div class="text-sm text-muted">Ürün Kodu</div>
            <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 8px;">{{ selectedItem?.model_code }}</div>
            
            <div class="grid grid-cols-2 gap-8 text-sm">
              <div v-if="selectedItem?.variant"><span class="text-muted">Varyant:</span> <strong style="color: var(--accent-blue);">{{ selectedItem.variant }}</strong></div>
              <div v-if="selectedItem?.dimension"><span class="text-muted">Ölçü:</span> <strong>{{ selectedItem.dimension }}</strong></div>
              <div v-if="selectedItem?.color"><span class="text-muted">Renk:</span> <strong>{{ selectedItem.color }} <span v-if="selectedItem.product_color_code">({{ selectedItem.product_color_code }})</span></strong></div>
            </div>
            
            <div v-if="selectedItem?.brief_intro" class="mt-8 p-8 bg-slate-50 rounded text-sm" style="border-left: 2px solid var(--accent-blue);">
              <strong>Açıklama/Talimat:</strong><br/>
              {{ selectedItem.brief_intro }}
            </div>
          </div>
          <form @submit.prevent="submitLog">
            <div class="form-group mb-12">
              <label class="form-label">Üretilen Miktar ({{ selectedItem?.unit_type }}) *</label>
              <input v-model.number="form.qty_produced" type="number" min="0" class="form-input" required autofocus />
            </div>
            <div class="form-group mb-12">
              <label class="form-label">Fire Miktarı ({{ selectedItem?.unit_type }})</label>
              <input v-model.number="form.fire_qty" type="number" min="0" class="form-input" />
            </div>
            <div class="form-group mb-16" v-if="form.fire_qty > 0">
              <label class="form-label">Fire Sebebi</label>
              <input v-model="form.fire_reason" type="text" class="form-input" placeholder="Kısaca açıklayın..." required />
            </div>
            
            <div class="form-group mb-24">
              <label class="flex items-center gap-8" style="cursor: pointer;">
                <input type="checkbox" v-model="form.handover" style="width: 20px; height: 20px;" />
                <span style="font-weight: 600; color: var(--accent-orange);">Bölümü Bitir / Sonraki Ekibe Devret (Handover)</span>
              </label>
              <p class="text-sm text-muted mt-4 ml-28">Bu seçeneği işaretlediğinizde ürün sizin kuyruğunuzdan çıkar ve sıradaki ekibe geçer.</p>
            </div>

            <div v-if="error" class="login-error mb-12">{{ error }}</div>
            
            <div class="flex justify-end gap-12">
              <button type="button" class="btn btn-secondary" @click="showModal = false">İptal</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">Kaydet</button>
            </div>
          </form>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import api from '../api'

const showToast = inject('showToast')
const queue = ref([])
const loading = ref(true)

const showModal = ref(false)
const selectedItem = ref(null)
const form = ref({ qty_produced: 0, fire_qty: 0, fire_reason: '', handover: false })
const saving = ref(false)
const error = ref('')

onMounted(() => {
  fetchQueue()
})

async function fetchQueue() {
  loading.value = true
  try {
    const res = await api.get('/tasks/my-team-queue/')
    queue.value = res.data
  } catch (err) {
    showToast('Kuyruk yüklenirken hata oluştu.', 'error')
  } finally {
    loading.value = false
  }
}

function openLogModal(item) {
  selectedItem.value = item
  form.value = { qty_produced: 0, fire_qty: 0, fire_reason: '', handover: false }
  error.value = ''
  showModal.value = true
}

async function submitLog() {
  saving.value = true
  error.value = ''
  try {
    await api.post(`/tasks/product-lines/${selectedItem.value.id}/log-production/`, form.value)
    showToast(form.value.handover ? 'Ürün devredildi.' : 'Üretim kaydedildi.', 'success')
    showModal.value = false
    await fetchQueue()
  } catch (err) {
    error.value = err.response?.data?.detail || 'İşlem başarısız oldu.'
  } finally {
    saving.value = false
  }
}
</script>
