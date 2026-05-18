<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-content" style="max-width: 560px;">
      <div class="modal-header">
        <h2>📥 Excel'den İçe Aktar</h2>
        <button class="btn btn-ghost btn-icon" @click="$emit('close')">✕</button>
      </div>

      <div class="modal-body">
        <p class="text-muted mb-16">
          <strong>.xlsx</strong> dosyası yükleyin. Zorunlu başlıklar:
          ÜRETİLECEK ÜRÜN İSMİ, KATEGORİ KODU, SİPARİŞ SERİ/SIRA, ÜRETİM MİKTARI, AÇIKLAMA_1, AÇIKLAMA_2
        </p>

        <!-- Upload Area -->
        <div
          class="upload-area"
          :class="{ 'upload-area--active': isDragging }"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="handleDrop"
          @click="$refs.fileInput.click()"
        >
          <input
            ref="fileInput"
            type="file"
            accept=".xlsx,.xls"
            style="display:none"
            @change="handleFileSelect"
          />
          <div class="upload-icon">📄</div>
          <div v-if="!selectedFile" class="upload-text">
            Dosyayı sürükleyin veya tıklayın
          </div>
          <div v-else class="upload-text">
            <strong>{{ selectedFile.name }}</strong>
            <br />
            <span class="text-sm text-muted">{{ formatSize(selectedFile.size) }}</span>
          </div>
        </div>

        <!-- Warnings -->
        <div v-if="warnings.length" class="mt-12">
          <div v-for="(w, i) in warnings" :key="i" class="warning-item">
            ⚠️ {{ w }}
          </div>
        </div>

        <div v-if="error" class="login-error mt-12">{{ error }}</div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="$emit('close')">İptal</button>
        <button
          class="btn btn-primary"
          :disabled="!selectedFile || uploading"
          @click="handleUpload"
        >
          <span v-if="uploading" class="spinner" style="width:16px;height:16px;border-width:2px;"></span>
          <span v-else>İçe Aktar</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { useTaskStore } from '../../stores/tasks'

const emit = defineEmits(['close', 'imported'])
const taskStore = useTaskStore()
const showToast = inject('showToast')

const selectedFile = ref(null)
const isDragging = ref(false)
const uploading = ref(false)
const error = ref('')
const warnings = ref([])

function handleFileSelect(e) {
  const file = e.target.files[0]
  if (file) selectedFile.value = file
}

function handleDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
    selectedFile.value = file
  } else {
    error.value = 'Sadece .xlsx veya .xls dosyaları kabul edilir.'
  }
}

async function handleUpload() {
  if (!selectedFile.value) return
  error.value = ''
  warnings.value = []
  uploading.value = true

  try {
    const draft = await taskStore.importExcel(selectedFile.value)
    warnings.value = draft.warnings || []
    emit('imported', draft)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Dosya işlenirken hata oluştu.'
  } finally {
    uploading.value = false
  }
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<style scoped>
.upload-area {
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-lg);
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-fast);
}
.upload-area:hover,
.upload-area--active {
  border-color: var(--accent-blue);
  background: rgba(79, 110, 247, 0.05);
}
.upload-icon {
  font-size: 2.5rem;
  margin-bottom: 12px;
}
.upload-text {
  color: var(--text-secondary);
  font-size: 0.9rem;
}
.warning-item {
  background: var(--accent-yellow-bg);
  color: var(--accent-yellow);
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  margin-bottom: 6px;
  border: 1px solid #f59e0b22;
}
</style>
