<template>
  <div class="page-content">
    <div class="page-header">
      <h2 class="page-title">MDF Stok Yönetimi</h2>
      <div class="flex gap-12">
        <button class="btn btn-secondary" @click="downloadPDF">
          📄 Rapor İndir
        </button>
        <button class="btn btn-secondary" @click="openHistoryModal">
          📜 İşlem Geçmişi
        </button>
        <button v-if="auth.isAdminOrManager" class="btn btn-primary" @click="openCreateModal">
          ＋ Yeni Stok Kartı
        </button>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-grid mb-24">
      <div class="stat-card">
        <div class="stat-label">Toplam Kalem</div>
        <div class="stat-value">{{ stockStore.dashboardStats?.total_items || 0 }}</div>
      </div>
      <div class="stat-card" style="border-color: rgba(239, 68, 68, 0.3);">
        <div class="stat-label" style="color: var(--accent-red);">Kritik Stok</div>
        <div class="stat-value" style="color: var(--accent-red);">{{ stockStore.dashboardStats?.critical_items || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Bu Ay Giriş</div>
        <div class="stat-value" style="color: var(--accent-green);">+{{ stockStore.dashboardStats?.entries_30d || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Bu Ay Çıkış</div>
        <div class="stat-value" style="color: var(--accent-orange);">-{{ stockStore.dashboardStats?.exits_30d || 0 }}</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-bar mb-16">
      <input
        v-model="searchQuery"
        type="text"
        class="form-input filter-search"
        placeholder="🔍 Stok adı veya kodu ara..."
        style="max-width: 300px;"
        @input="debouncedFetch"
      />
      <label class="flex items-center gap-8 ml-16" style="cursor:pointer;">
        <input type="checkbox" v-model="filterCritical" @change="fetchItems" />
        <span class="text-sm">Sadece Kritik Stokları Göster</span>
      </label>
    </div>

    <!-- Stock List -->
    <div class="card">
      <div v-if="stockStore.loading" class="loading-container">
        <div class="spinner"></div>
      </div>
      <div v-else-if="stockStore.items.length === 0" class="empty-state">
        <div class="empty-state-icon">📦</div>
        <div class="empty-state-text">Stok kalemi bulunamadı.</div>
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>SKU / Kod</th>
            <th>Ürün Adı</th>
            <th>Mevcut Miktar</th>
            <th>Min. Eşik</th>
            <th>Durum</th>
            <th class="text-right">İşlemler</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in stockStore.items" :key="item.id">
            <td class="text-muted" style="font-family: monospace;">{{ item.sku }}</td>
            <td style="font-weight: 600;">{{ item.name }}</td>
            <td>
              <span :style="{ color: item.is_critical ? 'var(--accent-red)' : 'inherit', fontSize: '1.1rem', fontWeight: 700 }">
                {{ item.current_quantity }}
              </span>
              <span class="text-sm text-muted ml-4">{{ item.unit }}</span>
            </td>
            <td class="text-muted">{{ item.min_threshold }}</td>
            <td>
              <span v-if="item.stock_status === 'out_of_stock'" class="badge badge-urgent">Tükendi</span>
              <span v-else-if="item.stock_status === 'critical'" class="badge badge-high">Kritik</span>
              <span v-else class="badge badge-done">Normal</span>
            </td>
            <td class="text-right">
              <div class="flex gap-8 justify-end">
                <button class="btn btn-secondary btn-sm" style="color: var(--accent-green);" @click="openTransactionModal(item, 'entry')" title="Stok Giriş">
                  📥 Giriş
                </button>
                <button class="btn btn-secondary btn-sm" style="color: var(--accent-orange);" @click="openTransactionModal(item, 'exit')" title="Stok Çıkış">
                  📤 Çıkış
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create/Edit Modal -->
    <div v-if="showCreateModal" class="modal-backdrop" @click.self="showCreateModal = false">
      <div class="modal-content" style="max-width: 480px;">
        <div class="modal-header">
          <h2>Yeni Stok Kartı Oluştur</h2>
          <button class="btn btn-ghost btn-icon" @click="showCreateModal = false">✕</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="handleCreateSubmit">
            <div class="form-group mb-12">
              <label class="form-label">Ürün Adı *</label>
              <input v-model="form.name" class="form-input" required />
            </div>
            <div class="form-row mb-12" style="display:flex;gap:12px;">
              <div class="form-group" style="flex:1">
                <label class="form-label">Birim</label>
                <select v-model="form.unit" class="form-select">
                  <option value="adet">Adet</option>
                  <option value="m2">m²</option>
                  <option value="kg">Kilogram</option>
                </select>
              </div>
              <div class="form-group" style="flex:1">
                <label class="form-label">Min. Eşik</label>
                <input v-model.number="form.min_threshold" type="number" step="0.01" class="form-input" required />
              </div>
            </div>
            <div class="form-group mb-16">
              <label class="form-label">Açıklama</label>
              <textarea v-model="form.description" class="form-textarea" style="min-height: 60px;"></textarea>
            </div>
            <div v-if="error" class="login-error mb-12">{{ error }}</div>
            <div class="flex justify-end gap-12">
              <button type="button" class="btn btn-secondary" @click="showCreateModal = false">İptal</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">Kaydet</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Transaction Modal (Entry/Exit) -->
    <div v-if="showTransactionModal" class="modal-backdrop" @click.self="showTransactionModal = false">
      <div class="modal-content" style="max-width: 400px;">
        <div class="modal-header">
          <h2>{{ transactionType === 'entry' ? '📥 Stok Girişi' : '📤 Stok Çıkışı' }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showTransactionModal = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="mb-16">
            <div class="text-sm text-muted">Ürün</div>
            <div style="font-weight: 700; font-size: 1.1rem;">{{ selectedItem.name }}</div>
            <div class="text-sm mt-4">Mevcut: <strong :style="{ color: selectedItem.is_critical ? 'var(--accent-red)' : 'var(--accent-green)' }">{{ selectedItem.current_quantity }} {{ selectedItem.unit }}</strong></div>
          </div>
          <form @submit.prevent="handleTransactionSubmit">
            <div class="form-group mb-12">
              <label class="form-label">Miktar ({{ selectedItem.unit }}) *</label>
              <input v-model.number="txForm.quantity" type="number" step="0.01" min="0.01" class="form-input" required autofocus />
            </div>
            <div v-if="transactionType === 'exit'" class="form-group mb-12">
              <label class="form-label">Kullanım Yeri *</label>
              <input v-model="txForm.usage_location" class="form-input" placeholder="Hangi bölümde/görevde kullanıldı?" :required="transactionType === 'exit'" />
            </div>
            <div class="form-group mb-16">
              <label class="form-label">Notlar (Opsiyonel)</label>
              <input v-model="txForm.notes" class="form-input" placeholder="İşlem açıklaması..." />
            </div>
            <div v-if="error" class="login-error mb-12">{{ error }}</div>
            <div class="flex justify-end gap-12">
              <button type="button" class="btn btn-secondary" @click="showTransactionModal = false">İptal</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                {{ transactionType === 'entry' ? 'Giriş Yap' : 'Çıkış Yap' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- History Modal -->
    <div v-if="showHistoryModal" class="modal-backdrop" @click.self="showHistoryModal = false">
      <div class="modal-content" style="max-width: 800px;">
        <div class="modal-header">
          <h2>📜 Stok İşlem Geçmişi (Son 100)</h2>
          <button class="btn btn-ghost btn-icon" @click="showHistoryModal = false">✕</button>
        </div>
        <div class="modal-body" style="padding: 0;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Tarih</th>
                <th>Tip</th>
                <th>Ürün</th>
                <th>Miktar</th>
                <th>Yapan Kişi</th>
                <th>Notlar</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tx in stockStore.history" :key="tx.id">
                <td class="text-sm text-muted">{{ formatDate(tx.created_at) }}</td>
                <td>
                  <span v-if="tx.transaction_type === 'entry'" class="badge badge-done">📥 Giriş</span>
                  <span v-else class="badge badge-high">📤 Çıkış</span>
                </td>
                <td style="font-weight: 500;">{{ tx.stock_item_name }}</td>
                <td :style="{ color: tx.transaction_type === 'entry' ? 'var(--accent-green)' : 'var(--accent-orange)', fontWeight: 700 }">
                  {{ tx.transaction_type === 'entry' ? '+' : '-' }}{{ tx.quantity }}
                </td>
                <td class="text-sm text-muted">{{ tx.performed_by_name }}</td>
                <td class="text-sm">{{ tx.notes || '—' }}</td>
              </tr>
              <tr v-if="stockStore.history.length === 0">
                <td colspan="6" class="text-center py-24 text-muted">Geçmiş işlem bulunamadı.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { useStockStore } from '../stores/stock'
import { useAuthStore } from '../stores/auth'

const stockStore = useStockStore()
const auth = useAuthStore()
const showToast = inject('showToast')

const searchQuery = ref('')
const filterCritical = ref(false)
let debounceTimer = null

const showCreateModal = ref(false)
const showTransactionModal = ref(false)
const showHistoryModal = ref(false)
const transactionType = ref('entry')
const selectedItem = ref(null)

const saving = ref(false)
const error = ref('')

const form = ref({ name: '', unit: 'adet', min_threshold: 0, description: '' })
const txForm = ref({ quantity: null, notes: '', usage_location: '' })

onMounted(() => {
  fetchItems()
  stockStore.fetchDashboard()
})

function fetchItems() {
  const params = {}
  if (searchQuery.value) params.search = searchQuery.value
  if (filterCritical.value) params.critical = 'true'
  stockStore.fetchItems(params)
}

function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchItems, 300)
}

function openCreateModal() {
  form.value = { name: '', unit: 'adet', min_threshold: 0, description: '' }
  error.value = ''
  showCreateModal.value = true
}

async function handleCreateSubmit() {
  saving.value = true
  error.value = ''
  try {
    await stockStore.createItem(form.value)
    showCreateModal.value = false
    showToast('Stok kartı başarıyla oluşturuldu.', 'success')
  } catch (err) {
    error.value = 'Kart oluşturulamadı. Lütfen bilgileri kontrol edin.'
  } finally {
    saving.value = false
  }
}

function openTransactionModal(item, type) {
  selectedItem.value = item
  transactionType.value = type
  txForm.value = { quantity: null, notes: '', usage_location: '' }
  error.value = ''
  showTransactionModal.value = true
}

async function handleTransactionSubmit() {
  saving.value = true
  error.value = ''
  try {
    if (transactionType.value === 'entry') {
      await stockStore.stockEntry(selectedItem.value.id, txForm.value.quantity, txForm.value.notes)
      showToast('Stok girişi başarılı.', 'success')
    } else {
      await stockStore.stockExit(selectedItem.value.id, txForm.value.quantity, txForm.value.notes, txForm.value.usage_location)
      showToast('Stok çıkışı başarılı.', 'success')
    }
    showTransactionModal.value = false
    stockStore.fetchDashboard() // Update stats
  } catch (err) {
    error.value = err.response?.data?.detail || 'İşlem başarısız oldu.'
  } finally {
    saving.value = false
  }
}

async function openHistoryModal() {
  await stockStore.fetchHistory()
  showHistoryModal.value = true
}

function formatDate(d) {
  if (!d) return ''
  const date = new Date(d)
  return date.toLocaleDateString('tr-TR') + ' ' + date.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
}

async function downloadPDF() {
  try {
    const token = localStorage.getItem('access')
    const response = await fetch('http://127.0.0.1:8000/api/stock/export-pdf/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) throw new Error('Rapor indirilemedi.')
    
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'stok_raporu.pdf'
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  } catch(err) {
    showToast('PDF Raporu indirilirken hata oluştu', 'error')
  }
}
</script>
