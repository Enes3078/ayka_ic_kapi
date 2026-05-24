<template>
  <div class="page-content">
    <div class="page-header" style="flex-direction: column; align-items: flex-start; gap: 16px;">
      <h2 class="page-title">Sistem Ayarları</h2>
      
      <!-- Sekmeler (Tabs) -->
      <div class="tabs">
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'users' }" 
          @click="activeTab = 'users'">
          Kullanıcı Yönetimi
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'products' }" 
          @click="activeTab = 'products'">
          Ürün Kataloğu
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'teams' }" 
          @click="activeTab = 'teams'">
          Görev Alanları
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'templates' }" 
          @click="activeTab = 'templates'">
          İş Akışı Şablonları
        </button>
        <button 
          class="tab-btn" 
          :class="{ active: activeTab === 'general' }" 
          @click="activeTab = 'general'">
          Genel Ayarlar
        </button>
      </div>
    </div>

    <!-- GÖREV ALANLARI SEKMESİ -->
    <div v-if="activeTab === 'teams'">
      <div class="flex justify-end mb-16">
        <button class="btn btn-primary" @click="openCreateModal('team')">
          ＋ Yeni Görev Alanı Ekle
        </button>
      </div>

      <div class="card">
        <div v-if="loadingTeams" class="loading-container">
          <div class="spinner"></div>
        </div>
        <div v-else-if="teams.length === 0" class="empty-state">
          <div class="empty-state-icon">🏭</div>
          <div class="empty-state-text">Henüz görev alanı oluşturulmamış.</div>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Görev Alanı</th>
              <th>Grup / Departman</th>
              <th>Atanan Kişi</th>
              <th class="text-right">İşlemler</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="team in teams" :key="team.id">
              <td style="font-weight: 700;">{{ team.name }}</td>
              <td>
                <span v-if="team.department" class="badge badge-medium">{{ team.department }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td><span class="badge badge-done">{{ team.member_count || 0 }} kişi</span></td>
              <td class="text-right">
                <button class="btn btn-ghost btn-sm" @click="openEditModal('team', team)" title="Düzenle">✏️</button>
                <button class="btn btn-ghost btn-sm" style="color: var(--accent-red);" @click="confirmDelete('team', team)" title="Sil">🗑</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- GENEL AYARLAR SEKMESİ -->
    <div v-if="activeTab === 'general'">
      <div class="card">
        <h3 class="mb-16 border-b pb-8">Mesai Saatleri ve Çalışma Günleri</h3>
        <div v-if="loadingSettings" class="loading-container">
          <div class="spinner"></div>
        </div>
        <form v-else @submit.prevent="handleSettingsSave">
          <div class="grid grid-cols-2 gap-16 mb-24">
            <div class="form-group">
              <label class="form-label font-bold text-slate-700">Mesai Başlangıç Saati *</label>
              <input v-model="settingsForm.work_start_time" type="time" class="form-input" required />
            </div>
            <div class="form-group">
              <label class="form-label font-bold text-slate-700">Mesai Bitiş Saati *</label>
              <input v-model="settingsForm.work_end_time" type="time" class="form-input" required />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-16 mb-24 bg-slate-50 p-16 rounded border border-slate-200">
            <div class="col-span-2">
              <h4 class="font-bold text-sm text-slate-800 mb-8">Öğle Molası</h4>
              <p class="text-xs text-muted">Bu aralık planlanan çalışma süresinden düşülür.</p>
            </div>
            <div class="form-group mb-0">
              <label class="form-label">Öğle Molası Başlangıç *</label>
              <input v-model="settingsForm.lunch_break_start_time" type="time" class="form-input" required />
            </div>
            <div class="form-group mb-0">
              <label class="form-label">Öğle Molası Bitiş *</label>
              <input v-model="settingsForm.lunch_break_end_time" type="time" class="form-input" required />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-16 mb-24 bg-slate-50 p-16 rounded border border-slate-200">
            <div class="col-span-2">
              <h4 class="font-bold text-sm text-slate-800 mb-8">Fazla Mesai (Opsiyonel)</h4>
            </div>
            <div class="form-group mb-0">
              <label class="form-label">Fazla Mesai Başlangıç</label>
              <input v-model="settingsForm.overtime_start_time" type="time" class="form-input" />
            </div>
            <div class="form-group mb-0">
              <label class="form-label">Fazla Mesai Bitiş</label>
              <input v-model="settingsForm.overtime_end_time" type="time" class="form-input" />
            </div>
          </div>
          <div class="form-group mb-24">
            <label class="form-label font-bold text-slate-700">Çalışma Günleri *</label>
            <div class="flex gap-16 flex-wrap mt-8">
              <label class="flex items-center gap-4 cursor-pointer" v-for="(day, i) in ['Pazartesi','Salı','Çarşamba','Perşembe','Cuma','Cumartesi','Pazar']" :key="i">
                <input type="checkbox" :value="i.toString()" v-model="selectedWorkDays" class="form-checkbox" />
                <span :class="{'text-red-600': i===6}">{{ day }}</span>
              </label>
            </div>
            <p class="text-xs text-muted mt-8">İşaretlenmeyen günler tatil sayılır ve bitiş süreleri bir sonraki iş gününe kayar.</p>
          </div>
          <div class="flex justify-end pt-16 border-t">
            <button type="submit" class="btn btn-primary" :disabled="saving">
              <span v-if="saving" class="spinner" style="width:16px;height:16px;border-width:2px;"></span>
              <span v-else>💾 Ayarları Kaydet</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- KULLANICI YÖNETİMİ SEKMESİ -->
    <div v-if="activeTab === 'users'">
      <div class="flex justify-end mb-16">
        <button class="btn btn-primary" @click="openCreateModal('user')">
          ＋ Yeni Kullanıcı Ekle
        </button>
      </div>

      <div class="card">
        <div v-if="loadingUsers" class="loading-container">
          <div class="spinner"></div>
        </div>
        <div v-else-if="users.length === 0" class="empty-state">
          <div class="empty-state-icon">👥</div>
          <div class="empty-state-text">Sistemde henüz kayıtlı kullanıcı yok.</div>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Kullanıcı Adı</th>
              <th>Ad Soyad</th>
              <th>Rol</th>
              <th>Görev Yeri / Alanları</th>
              <th>Durum</th>
              <th class="text-right">İşlemler</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td style="font-weight: 600;">{{ user.username }}</td>
              <td>{{ user.first_name }} {{ user.last_name }}</td>
              <td>
                <span class="badge" :class="{
                  'badge-urgent': user.role === 'admin',
                  'badge-high': user.role === 'manager',
                  'badge-done': user.role === 'worker'
                }">
                  {{ roleLabel(user.role) }}
                </span>
              </td>
              <td>
                <div class="flex flex-wrap gap-4">
                  <span v-if="user.department" class="badge badge-medium">{{ user.department }}</span>
                  <span
                    v-for="teamName in displayTeamNames(user)"
                    :key="teamName"
                    class="badge badge-done"
                  >
                    {{ teamName }}
                  </span>
                  <span v-if="!user.department && !(user.assigned_team_names || []).length" class="text-muted">—</span>
                </div>
              </td>
              <td>
                <span v-if="user.is_active" style="color: var(--accent-green); font-weight: 600;">Aktif</span>
                <span v-else style="color: var(--accent-red); font-weight: 600;">Pasif</span>
              </td>
              <td class="text-right">
                <button class="btn btn-ghost btn-sm" @click="openEditModal('user', user)" title="Düzenle">✏️</button>
                <button v-if="user.id !== auth.user?.id" class="btn btn-ghost btn-sm" style="color: var(--accent-red);" @click="confirmDelete('user', user)" title="Sil">🗑</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ÜRÜN KATALOĞU SEKMESİ -->
    <div v-if="activeTab === 'products'">
      <div class="flex justify-end mb-16">
        <button class="btn btn-primary" @click="openCreateModal('product')">
          ＋ Yeni Ürün Ekle
        </button>
      </div>

      <div class="card">
        <div v-if="loadingProducts" class="loading-container">
          <div class="spinner"></div>
        </div>
        <div v-else-if="products.length === 0" class="empty-state">
          <div class="empty-state-icon">📦</div>
          <div class="empty-state-text">Kataloga henüz ürün eklenmemiş.</div>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Ürün Kodu</th>
              <th>Model Adı</th>
              <th>Süre (dk)</th>
              <th>Ölçüler (EnxBoyxKalınlık)</th>
              <th>Bıçak Min/Max</th>
              <th class="text-right">İşlemler</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="product in products" :key="product.id">
              <td style="font-weight: 600; color: var(--accent-blue);">{{ product.code }}</td>
              <td style="font-weight: 500;">{{ product.name }}</td>
              <td><span class="badge badge-medium">{{ product.duration_minutes }} dk</span></td>
              <td class="text-muted text-sm">
                {{ product.width_mm || '-' }} x {{ product.length_mm || '-' }} x {{ product.thickness_mm || '-' }} mm
              </td>
              <td class="text-muted text-sm">
                {{ product.blade_min_mm || '-' }} / {{ product.blade_max_mm || '-' }} mm
              </td>
              <td class="text-right">
                <button class="btn btn-ghost btn-sm" @click="openEditModal('product', product)" title="Düzenle">✏️</button>
                <button class="btn btn-ghost btn-sm" style="color: var(--accent-red);" @click="confirmDelete('product', product)" title="Sil">🗑</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- İŞ AKIŞI ŞABLONLARI SEKMESİ -->
    <div v-if="activeTab === 'templates'">
      <div class="flex justify-end mb-16">
        <button class="btn btn-primary" @click="openCreateModal('template')">
          ＋ Yeni Şablon Ekle
        </button>
      </div>

      <div class="card">
        <div v-if="loadingTemplates" class="loading-container">
          <div class="spinner"></div>
        </div>
        <div v-else-if="workflowTemplates.length === 0" class="empty-state">
          <div class="empty-state-icon">📋</div>
          <div class="empty-state-text">Henüz iş akışı şablonu oluşturulmamış.</div>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Şablon Adı</th>
              <th>Adım Sayısı</th>
              <th class="text-right">İşlemler</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="tpl in workflowTemplates" :key="tpl.id">
              <td style="font-weight: 600; color: var(--accent-purple);">{{ tpl.name }}</td>
              <td><span class="badge badge-medium">{{ tpl.steps.length }} Adım</span></td>
              <td class="text-right">
                <button class="btn btn-ghost btn-sm" @click="openEditModal('template', tpl)" title="Düzenle">✏️</button>
                <button class="btn btn-ghost btn-sm" style="color: var(--accent-red);" @click="confirmDelete('template', tpl)" title="Sil">🗑</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Team Create/Edit Modal -->
    <div v-if="showTeamModal" class="modal-backdrop" @click.self="showTeamModal = false">
      <div class="modal-content" style="max-width: 480px;">
        <div class="modal-header">
          <h2>{{ editingTeam ? 'Görev Alanını Düzenle' : 'Yeni Görev Alanı Oluştur' }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showTeamModal = false">✕</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="handleTeamSave">
            <div class="form-group mb-12">
              <label class="form-label">Görev Alanı Adı *</label>
              <input v-model="teamForm.name" class="form-input" placeholder="Örn: CNC" required />
            </div>

            <div class="form-group mb-16">
              <label class="form-label">Grup / Departman</label>
              <input v-model="teamForm.department" class="form-input" placeholder="Örn: Üretim" />
            </div>

            <div v-if="error" class="login-error mb-12">{{ error }}</div>

            <div class="flex justify-end gap-12">
              <button type="button" class="btn btn-secondary" @click="showTeamModal = false">İptal</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                {{ editingTeam ? 'Güncelle' : 'Kaydet' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- User Create/Edit Modal -->
    <div v-if="showUserModal" class="modal-backdrop" @click.self="showUserModal = false">
      <div class="modal-content" style="max-width: 500px;">
        <div class="modal-header">
          <h2>{{ editingUser ? 'Kullanıcıyı Düzenle' : 'Yeni Kullanıcı Oluştur' }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showUserModal = false">✕</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="handleUserSave">
            <div class="form-row mb-12" style="display:flex;gap:12px;">
              <div class="form-group" style="flex:1">
                <label class="form-label">Ad</label>
                <input v-model="userForm.first_name" class="form-input" />
              </div>
              <div class="form-group" style="flex:1">
                <label class="form-label">Soyad</label>
                <input v-model="userForm.last_name" class="form-input" />
              </div>
            </div>
            
            <div class="form-group mb-12">
              <label class="form-label">Kullanıcı Adı *</label>
              <input v-model="userForm.username" class="form-input" required :disabled="editingUser" />
            </div>

            <div class="form-group mb-12">
              <label class="form-label">E-posta</label>
              <input v-model="userForm.email" type="email" class="form-input" />
            </div>

            <div class="form-group mb-12">
              <label class="form-label">{{ editingUser ? 'Şifre (Değiştirmek istemiyorsanız boş bırakın)' : 'Şifre *' }}</label>
              <input v-model="userForm.password" type="password" class="form-input" :required="!editingUser" minlength="6" />
            </div>

            <div class="form-row mb-12" style="display:flex;gap:12px;">
              <div class="form-group" style="flex:1">
                <label class="form-label">Rol</label>
                <select v-model="userForm.role" class="form-select">
                  <option value="worker">Çalışan (Worker)</option>
                  <option value="manager">Müdür (Manager)</option>
                  <option value="admin">Yönetici (Admin)</option>
                </select>
              </div>
              <div class="form-group" style="flex:1">
                <label class="form-label">Ana Görev Yeri</label>
                <select v-model="userForm.department" class="form-select">
                  <option value="">Atanmadı</option>
                  <option v-for="t in teams" :key="t.id" :value="t.name">{{ t.name }}</option>
                </select>
              </div>
            </div>

            <div class="form-group mb-16">
              <label class="form-label">Görev Alanları</label>
              <div class="team-checkbox-grid">
                <label v-for="t in teams" :key="t.id" class="team-checkbox">
                  <input type="checkbox" :value="t.id" v-model="userForm.team_ids" />
                  <span>{{ t.name }}</span>
                </label>
              </div>
            </div>

            <div class="form-group mb-16">
              <label class="flex items-center gap-8" style="cursor: pointer;">
                <input type="checkbox" v-model="userForm.is_active" style="width: 20px; height: 20px;" />
                <span style="font-weight: 600;">Hesap Aktif</span>
              </label>
            </div>

            <div v-if="error" class="login-error mb-12">{{ error }}</div>
            
            <div class="flex justify-end gap-12">
              <button type="button" class="btn btn-secondary" @click="showUserModal = false">İptal</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                {{ editingUser ? 'Güncelle' : 'Kaydet' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Product Create/Edit Modal -->
    <div v-if="showProductModal" class="modal-backdrop" @click.self="showProductModal = false">
      <div class="modal-content" style="max-width: 600px;">
        <div class="modal-header">
          <h2>{{ editingProduct ? 'Ürünü Düzenle' : 'Yeni Ürün Oluştur' }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showProductModal = false">✕</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="handleProductSave">
            <div class="form-row mb-12" style="display:flex;gap:12px;">
              <div class="form-group" style="flex:1">
                <label class="form-label">Ürün Kodu *</label>
                <input v-model="productForm.code" class="form-input" placeholder="AY-01" required />
              </div>
              <div class="form-group" style="flex:2">
                <label class="form-label">Model Adı *</label>
                <input v-model="productForm.name" class="form-input" placeholder="Model adını girin..." required />
              </div>
            </div>
            
            <div class="form-group mb-12">
              <label class="form-label">Üretim Süresi (Dakika) *</label>
              <input v-model.number="productForm.duration_minutes" type="number" min="0" class="form-input" required />
              <span class="text-xs text-muted">Bu süre otomatik planlama için kullanılacaktır.</span>
            </div>

            <div class="form-row mb-12" style="display:flex;gap:12px;">
              <div class="form-group" style="flex:1">
                <label class="form-label">En (mm)</label>
                <input v-model.number="productForm.width_mm" type="number" class="form-input" />
              </div>
              <div class="form-group" style="flex:1">
                <label class="form-label">Boy (mm)</label>
                <input v-model.number="productForm.length_mm" type="number" class="form-input" />
              </div>
              <div class="form-group" style="flex:1">
                <label class="form-label">Kalınlık (mm)</label>
                <input v-model.number="productForm.thickness_mm" type="number" step="0.1" class="form-input" />
              </div>
            </div>

            <div class="form-group mb-12">
              <label class="form-label">Ek Ölçüler</label>
              <input v-model="productForm.additional_dimensions" class="form-input" placeholder="Örn: 73x210, 83x210..." />
            </div>

            <div class="form-row mb-16" style="display:flex;gap:12px;">
              <div class="form-group" style="flex:1">
                <label class="form-label">Bıçak Min (mm)</label>
                <input v-model.number="productForm.blade_min_mm" type="number" step="0.1" class="form-input" />
              </div>
              <div class="form-group" style="flex:1">
                <label class="form-label">Bıçak Max (mm)</label>
                <input v-model.number="productForm.blade_max_mm" type="number" step="0.1" class="form-input" />
              </div>
            </div>

            <div v-if="error" class="login-error mb-12">{{ error }}</div>
            
            <div class="flex justify-end gap-12">
              <button type="button" class="btn btn-secondary" @click="showProductModal = false">İptal</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                {{ editingProduct ? 'Güncelle' : 'Kaydet' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Template Create/Edit Modal -->
    <div v-if="showTemplateModal" class="modal-backdrop" @click.self="showTemplateModal = false">
      <div class="modal-content" style="max-width: 500px;">
        <div class="modal-header">
          <h2>{{ editingTemplate ? 'Şablonu Düzenle' : 'Yeni Şablon Oluştur' }}</h2>
          <button class="btn btn-ghost btn-icon" @click="showTemplateModal = false">✕</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="handleTemplateSave">
            <div class="form-group mb-16">
              <label class="form-label">Şablon Adı *</label>
              <input v-model="templateForm.name" class="form-input" placeholder="Örn: Standart Ahşap Kapı Üretimi" required />
            </div>

            <div class="form-group mb-12">
              <label class="form-label">İş Akışı Adımları (Ekipler)</label>
              <div class="flex flex-col gap-8 mt-8">
                <div v-for="(step, sIndex) in templateForm.steps" :key="sIndex" class="flex items-center gap-8">
                  <span class="text-sm font-bold" style="color: var(--accent-blue);">{{ sIndex + 1 }}.</span>
                  <select v-model="templateForm.steps[sIndex]" class="form-select" style="flex:1;" required>
                    <option :value="null">Ekip Seçin</option>
                    <option v-for="t in teams" :key="t.id" :value="t.id">{{ t.name }}</option>
                  </select>
                  <button type="button" class="btn btn-ghost btn-sm" style="color: var(--accent-red);" @click="templateForm.steps.splice(sIndex, 1)">✕</button>
                </div>
                <button type="button" class="btn btn-secondary btn-sm" style="align-self: flex-start; margin-top: 4px;" @click="templateForm.steps.push(null)">
                  ＋ Adım Ekle
                </button>
              </div>
            </div>

            <div v-if="error" class="login-error mb-12">{{ error }}</div>
            
            <div class="flex justify-end gap-12 mt-16">
              <button type="button" class="btn btn-secondary" @click="showTemplateModal = false">İptal</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                {{ editingTemplate ? 'Güncelle' : 'Kaydet' }}
              </button>
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
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const showToast = inject('showToast')

const activeTab = ref('users') // 'users' veya 'products'

// State (Kullanıcılar)
const users = ref([])
const teams = ref([])
const loadingUsers = ref(true)
const loadingTeams = ref(true)
const showUserModal = ref(false)
const editingUser = ref(null)
const showTeamModal = ref(false)
const editingTeam = ref(null)

// State (Ürünler)
const products = ref([])
const loadingProducts = ref(true)
const showProductModal = ref(false)
const editingProduct = ref(null)

// State (Şablonlar)
const workflowTemplates = ref([])
const loadingTemplates = ref(true)
const showTemplateModal = ref(false)
const editingTemplate = ref(null)

const saving = ref(false)
const error = ref('')

// State (Genel Ayarlar)
const loadingSettings = ref(true)
const settingsForm = ref({
  work_start_time: '08:30:00',
  work_end_time: '18:30:00',
  lunch_break_start_time: '12:30:00',
  lunch_break_end_time: '13:30:00',
  overtime_start_time: null,
  overtime_end_time: null,
  work_days: '0,1,2,3,4,5'
})
const selectedWorkDays = ref(['0','1','2','3','4','5'])

// Forms
const userForm = ref({
  first_name: '', last_name: '', username: '', email: '',
  password: '', role: 'worker', department: '', team_ids: [], is_active: true
})

const teamForm = ref({
  name: '',
  department: 'Üretim'
})

const productForm = ref({
  code: '', name: '', duration_minutes: 0,
  width_mm: null, length_mm: null, thickness_mm: null,
  additional_dimensions: '', blade_min_mm: null, blade_max_mm: null
})

const templateForm = ref({
  name: '', steps: []
})

onMounted(() => {
  fetchUsers()
  fetchTeams()
  fetchProducts()
  fetchTemplates()
  fetchSettings()
})

// === GENEL AYARLAR ===
async function fetchSettings() {
  loadingSettings.value = true
  try {
    const res = await api.get('/tasks/settings/')
    settingsForm.value = res.data
    if (res.data.work_days) {
      selectedWorkDays.value = res.data.work_days.split(',')
    }
  } catch (err) {
    console.error('Ayarlar yüklenemedi:', err)
  } finally {
    loadingSettings.value = false
  }
}

async function handleSettingsSave() {
  saving.value = true
  settingsForm.value.work_days = selectedWorkDays.value.sort().join(',')
  try {
    await api.put('/tasks/settings/', settingsForm.value)
    showToast('Genel ayarlar başarıyla kaydedildi.', 'success')
  } catch (err) {
    console.error(err)
    showToast('Ayarlar kaydedilemedi.', 'error')
  } finally {
    saving.value = false
  }
}

// === USER YÖNETİMİ ===
async function fetchUsers() {
  loadingUsers.value = true
  try {
    const res = await api.get('/auth/users/')
    users.value = res.data.results || res.data
  } catch (err) {
    showToast('Kullanıcılar yüklenemedi.', 'error')
  } finally {
    loadingUsers.value = false
  }
}

async function fetchTeams() {
  loadingTeams.value = true
  try {
    const res = await api.get('/tasks/teams/')
    teams.value = res.data.results || res.data
  } catch (err) {
    console.error('Ekipler yüklenemedi', err)
    showToast('Görev alanları yüklenemedi.', 'error')
  } finally {
    loadingTeams.value = false
  }
}

function roleLabel(role) {
  const map = { admin: 'Yönetici', manager: 'Müdür', worker: 'Çalışan' }
  return map[role] || role
}

function displayTeamNames(user) {
  return (user.assigned_team_names || []).filter(teamName => teamName !== user.department)
}

// === ÜRÜN YÖNETİMİ ===
async function fetchProducts() {
  loadingProducts.value = true
  try {
    const res = await api.get('/tasks/products/')
    products.value = res.data.results || res.data
  } catch (err) {
    showToast('Ürünler yüklenemedi.', 'error')
  } finally {
    loadingProducts.value = false
  }
}

// === ŞABLON YÖNETİMİ ===
async function fetchTemplates() {
  loadingTemplates.value = true
  try {
    const res = await api.get('/tasks/workflow-templates/')
    workflowTemplates.value = res.data.results || res.data
  } catch (err) {
    showToast('Şablonlar yüklenemedi.', 'error')
  } finally {
    loadingTemplates.value = false
  }
}

// === ORTAK MODAL İŞLEMLERİ ===
function openCreateModal(type) {
  error.value = ''
  if (type === 'user') {
    editingUser.value = null
    userForm.value = { first_name: '', last_name: '', username: '', email: '', password: '', role: 'worker', department: '', team_ids: [], is_active: true }
    showUserModal.value = true
  } else if (type === 'team') {
    editingTeam.value = null
    teamForm.value = { name: '', department: 'Üretim' }
    showTeamModal.value = true
  } else if (type === 'product') {
    editingProduct.value = null
    productForm.value = { code: '', name: '', duration_minutes: 0, width_mm: null, length_mm: null, thickness_mm: null, additional_dimensions: '', blade_min_mm: null, blade_max_mm: null }
    showProductModal.value = true
  } else {
    editingTemplate.value = null
    templateForm.value = { name: '', steps: [null] }
    showTemplateModal.value = true
  }
}

function openEditModal(type, item) {
  error.value = ''
  if (type === 'user') {
    editingUser.value = item
    userForm.value = { ...item, password: '', team_ids: [...(item.assigned_team_ids || [])] }
    showUserModal.value = true
  } else if (type === 'team') {
    editingTeam.value = item
    teamForm.value = { name: item.name, department: item.department || '' }
    showTeamModal.value = true
  } else if (type === 'product') {
    editingProduct.value = item
    productForm.value = { ...item }
    showProductModal.value = true
  } else {
    editingTemplate.value = item
    templateForm.value = { ...item, steps: [...item.steps] }
    showTemplateModal.value = true
  }
}

async function handleUserSave() {
  saving.value = true
  error.value = ''
  const payload = { ...userForm.value }
  const primaryTeam = teams.value.find(t => t.name === payload.department)
  if (primaryTeam && !payload.team_ids.includes(primaryTeam.id)) {
    payload.team_ids = [...payload.team_ids, primaryTeam.id]
  }
  if (!payload.password) delete payload.password

  try {
    if (editingUser.value) {
      await api.put(`/auth/users/${editingUser.value.id}/`, payload)
      showToast('Kullanıcı güncellendi.', 'success')
    } else {
      await api.post('/auth/users/', payload)
      showToast('Yeni kullanıcı eklendi.', 'success')
    }
    showUserModal.value = false
    await fetchUsers()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Kullanıcı adı benzersiz olmalıdır.'
  } finally {
    saving.value = false
  }
}

async function handleTeamSave() {
  saving.value = true
  error.value = ''
  const payload = {
    name: teamForm.value.name.trim(),
    department: teamForm.value.department.trim()
  }

  try {
    if (editingTeam.value) {
      await api.patch(`/tasks/teams/${editingTeam.value.id}/`, payload)
      showToast('Görev alanı güncellendi.', 'success')
    } else {
      await api.post('/tasks/teams/', payload)
      showToast('Yeni görev alanı eklendi.', 'success')
    }
    showTeamModal.value = false
    await fetchTeams()
    await fetchUsers()
  } catch (err) {
    const data = err.response?.data
    if (typeof data === 'object') {
      error.value = Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join(' | ')
    } else {
      error.value = 'Görev alanı kaydedilemedi.'
    }
  } finally {
    saving.value = false
  }
}

async function handleProductSave() {
  saving.value = true
  error.value = ''
  
  try {
    if (editingProduct.value) {
      await api.put(`/tasks/products/${editingProduct.value.id}/`, productForm.value)
      showToast('Ürün güncellendi.', 'success')
    } else {
      await api.post('/tasks/products/', productForm.value)
      showToast('Kataloga yeni ürün eklendi.', 'success')
    }
    showProductModal.value = false
    await fetchProducts()
  } catch (err) {
    const data = err.response?.data
    if (typeof data === 'object') {
      error.value = Object.entries(data).map(([k,v]) => `${k}: ${v}`).join(' | ')
    } else {
      error.value = 'Kaydetme sırasında bir hata oluştu.'
    }
  } finally {
    saving.value = false
  }
}

async function handleTemplateSave() {
  saving.value = true
  error.value = ''
  
  // Boş adımları (null) filtrele
  const payload = { ...templateForm.value, steps: templateForm.value.steps.filter(s => s !== null) }

  if (payload.steps.length === 0) {
    error.value = 'Şablon için en az 1 adım (ekip) seçmelisiniz.'
    saving.value = false
    return
  }
  
  try {
    if (editingTemplate.value) {
      await api.put(`/tasks/workflow-templates/${editingTemplate.value.id}/`, payload)
      showToast('Şablon güncellendi.', 'success')
    } else {
      await api.post('/tasks/workflow-templates/', payload)
      showToast('Yeni şablon eklendi.', 'success')
    }
    showTemplateModal.value = false
    await fetchTemplates()
  } catch (err) {
    error.value = 'Kaydetme sırasında bir hata oluştu. Şablon adı benzersiz olmalıdır.'
  } finally {
    saving.value = false
  }
}

async function confirmDelete(type, item) {
  if (type === 'user') {
    if (confirm(`${item.first_name} ${item.last_name} (${item.username}) kullanıcısını silmek istediğinize emin misiniz?`)) {
      try {
        await api.delete(`/auth/users/${item.id}/`)
        showToast('Kullanıcı silindi.', 'success')
        await fetchUsers()
      } catch (err) {
        showToast('Kullanıcı silinemedi.', 'error')
      }
    }
  } else if (type === 'team') {
    if (confirm(`"${item.name}" görev alanını silmek istediğinize emin misiniz? Bu alan kullanıcı atamalarından da kaldırılır.`)) {
      try {
        await api.delete(`/tasks/teams/${item.id}/`)
        showToast('Görev alanı silindi.', 'success')
        await fetchTeams()
        await fetchUsers()
      } catch (err) {
        showToast('Görev alanı silinemedi.', 'error')
      }
    }
  } else if (type === 'product') {
    if (confirm(`"${item.code} - ${item.name}" ürününü katalogdan silmek istediğinize emin misiniz?`)) {
      try {
        await api.delete(`/tasks/products/${item.id}/`)
        showToast('Ürün katalogdan silindi.', 'success')
        await fetchProducts()
      } catch (err) {
        showToast('Ürün silinemedi.', 'error')
      }
    }
  } else if (type === 'template') {
    if (confirm(`"${item.name}" şablonunu silmek istediğinize emin misiniz?`)) {
      try {
        await api.delete(`/tasks/workflow-templates/${item.id}/`)
        showToast('Şablon silindi.', 'success')
        await fetchTemplates()
      } catch (err) {
        showToast('Şablon silinemedi.', 'error')
      }
    }
  }
}
</script>

<style scoped>
.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  background: var(--bg-card);
  padding: 6px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}
.tab-btn {
  background: transparent;
  border: none;
  padding: 10px 20px;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}
.tab-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}
.tab-btn.active {
  background: var(--accent-blue);
  color: white;
  box-shadow: 0 2px 8px rgba(79, 110, 247, 0.3);
}
.team-checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
  margin-top: 8px;
}
.team-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  cursor: pointer;
  background: var(--bg-body);
}
.team-checkbox input {
  width: 16px;
  height: 16px;
}
</style>
