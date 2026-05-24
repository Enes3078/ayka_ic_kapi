<template>
  <aside class="sidebar" :class="{ 'sidebar--collapsed': collapsed }">
    <div class="sidebar-logo">
      <div class="logo-icon">⚙</div>
      <div class="logo-text" v-if="!collapsed">
        <span class="logo-title">MES</span>
        <span class="logo-subtitle">Üretim Yönetimi</span>
      </div>
    </div>

    <nav class="sidebar-nav">
      <button
        class="nav-item nav-toggle"
        type="button"
        :title="collapsed ? 'Menüyü büyüt' : 'Menüyü küçült'"
        @click="$emit('toggle')"
      >
        <span class="nav-icon">{{ collapsed ? '>' : '<' }}</span>
        <span v-if="!collapsed" class="nav-label">Menüyü Küçült</span>
      </button>
      <router-link v-if="auth.isAdminOrManager" to="/" class="nav-item" active-class="nav-item--active" title="Dashboard">
        <span class="nav-icon">📊</span>
        <span v-if="!collapsed" class="nav-label">Dashboard</span>
      </router-link>
      <router-link v-if="auth.isAdminOrManager" to="/reporting" class="nav-item" active-class="nav-item--active" title="Raporlar">
        <span class="nav-icon">📄</span>
        <span v-if="!collapsed" class="nav-label">Raporlar</span>
      </router-link>
      <router-link v-if="auth.isAdminOrManager" to="/tasks" class="nav-item" active-class="nav-item--active" title="Görevler">
        <span class="nav-icon">📋</span>
        <span v-if="!collapsed" class="nav-label">Görevler</span>
      </router-link>
      <router-link v-if="auth.isAdminOrManager" to="/worker-tracking" class="nav-item" active-class="nav-item--active" title="Saha Takibi">
        <span class="nav-icon">👷</span>
        <span v-if="!collapsed" class="nav-label">Saha Takibi</span>
      </router-link>
      <router-link to="/my-team-queue" class="nav-item" active-class="nav-item--active" title="İş Kuyruğum">
        <span class="nav-icon">🏭</span>
        <span v-if="!collapsed" class="nav-label">İş Kuyruğum</span>
      </router-link>
      <router-link to="/my-past-tasks" class="nav-item" active-class="nav-item--active" title="Geçmiş Görevlerim">
        <span class="nav-icon">✅</span>
        <span v-if="!collapsed" class="nav-label">Geçmiş Görevlerim</span>
      </router-link>
      <router-link v-if="auth.isAdminOrManager" to="/stock" class="nav-item" active-class="nav-item--active" title="Stok Yönetimi">
        <span class="nav-icon">📦</span>
        <span v-if="!collapsed" class="nav-label">Stok Yönetimi</span>
      </router-link>
      <router-link v-if="auth.isAdminOrManager" to="/settings" class="nav-item" active-class="nav-item--active" title="Ayarlar">
        <span class="nav-icon">⚙️</span>
        <span v-if="!collapsed" class="nav-label">Ayarlar</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <div class="sidebar-user">
        <div class="user-avatar">{{ userInitials }}</div>
        <div class="user-info" v-if="!collapsed">
          <div class="user-name">{{ userName }}</div>
          <div class="user-role">{{ userRole }}</div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '../../stores/auth'

defineProps({
  collapsed: {
    type: Boolean,
    default: false,
  },
})
defineEmits(['toggle'])

const auth = useAuthStore()
const userName = computed(() =>
  auth.user ? `${auth.user.first_name || ''} ${auth.user.last_name || ''}`.trim() || auth.user.username : ''
)
const userInitials = computed(() => {
  if (!auth.user) return '?'
  const f = auth.user.first_name?.[0] || ''
  const l = auth.user.last_name?.[0] || ''
  return (f + l).toUpperCase() || auth.user.username[0].toUpperCase()
})
const roleMap = { admin: 'Yönetici', manager: 'Müdür', worker: 'Çalışan' }
const userRole = computed(() => roleMap[auth.user?.role] || auth.user?.role || '')
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width var(--transition-base);
}
.sidebar--collapsed {
  width: var(--sidebar-collapsed-width);
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 20px;
  border-bottom: 1px solid var(--border-color);
  min-height: 81px;
}
.sidebar--collapsed .sidebar-logo {
  justify-content: center;
  padding: 20px 10px;
}
.logo-icon {
  width: 42px;
  height: 42px;
  background: var(--accent-blue);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 1.28rem;
  font-weight: 800;
  box-shadow: 0 8px 18px rgba(49,94,234,0.18);
}
.logo-title {
  font-size: 1.22rem;
  font-weight: 800;
  letter-spacing: 0.1px;
  color: var(--accent-blue);
  line-height: 1.1;
}
.logo-subtitle {
  display: block;
  font-size: 0.82rem;
  color: var(--text-secondary);
  font-weight: 700;
  line-height: 1.35;
  margin-top: 2px;
}
.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.sidebar--collapsed .sidebar-nav {
  padding: 18px 10px;
  align-items: center;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 16px;
  border-radius: var(--radius-md);
  color: var(--text-primary);
  background: transparent;
  border: 0;
  width: 100%;
  font-family: inherit;
  font-size: 0.98rem;
  font-weight: 700;
  line-height: 1.25;
  transition: all var(--transition-fast);
  text-decoration: none;
  min-height: 48px;
  cursor: pointer;
}
.sidebar--collapsed .nav-item {
  width: 52px;
  height: 52px;
  justify-content: center;
  padding: 0;
}
.nav-item:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}
.nav-toggle {
  color: var(--text-secondary);
  margin-bottom: 8px;
  border: 1px solid transparent;
}
.nav-toggle:hover {
  border-color: var(--border-color);
}
.sidebar--collapsed .nav-toggle {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  margin-bottom: 12px;
}
.nav-item--active {
  background: var(--accent-blue) !important;
  color: white !important;
  box-shadow: 0 2px 8px rgba(79,110,247,0.3);
}
.nav-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  min-width: 24px;
  font-size: 1.32rem;
  line-height: 1;
}
.nav-label {
  white-space: nowrap;
}
.sidebar--collapsed .nav-icon { font-size: 1.45rem; }

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
}
.sidebar--collapsed .sidebar-footer {
  padding: 14px 10px;
}
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 12px;
}
.sidebar--collapsed .sidebar-user {
  justify-content: center;
}
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  color: white;
}
.user-name {
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.25;
}
.user-role {
  font-size: 0.82rem;
  color: var(--text-secondary);
  font-weight: 700;
  line-height: 1.35;
}
@media (max-width: 768px) {
  .sidebar-logo {
    min-height: 72px;
  }
  .logo-icon {
    width: 42px;
    height: 42px;
  }
  .nav-item {
    min-height: 54px;
    font-size: 1rem;
    font-weight: 700;
  }
  .sidebar--collapsed .nav-item {
    width: 50px;
    height: 54px;
  }
  .nav-icon,
  .sidebar--collapsed .nav-icon {
    font-size: 1.35rem;
  }
  .user-avatar {
    width: 40px;
    height: 40px;
  }
}
</style>
