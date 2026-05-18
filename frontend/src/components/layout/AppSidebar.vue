<template>
  <aside class="sidebar">
    <div class="sidebar-logo">
      <div class="logo-icon">⚙</div>
      <div class="logo-text">
        <span class="logo-title">MES</span>
        <span class="logo-subtitle">Üretim Yönetimi</span>
      </div>
    </div>

    <nav class="sidebar-nav">
      <router-link v-if="auth.isAdminOrManager" to="/" class="nav-item" active-class="nav-item--active">
        <span class="nav-icon">📊</span>
        <span>Dashboard</span>
      </router-link>
      <router-link v-if="auth.isAdminOrManager" to="/reporting" class="nav-item" active-class="nav-item--active">
        <span class="nav-icon">📄</span>
        <span>Raporlar</span>
      </router-link>
      <router-link v-if="auth.isAdminOrManager" to="/tasks" class="nav-item" active-class="nav-item--active">
        <span class="nav-icon">📋</span>
        <span>Görevler</span>
      </router-link>
      <router-link v-if="auth.isAdminOrManager" to="/worker-tracking" class="nav-item" active-class="nav-item--active">
        <span class="nav-icon">👷</span>
        <span>Saha Takibi</span>
      </router-link>
      <router-link to="/my-team-queue" class="nav-item" active-class="nav-item--active">
        <span class="nav-icon">🏭</span>
        <span>İş Kuyruğum</span>
      </router-link>
      <router-link to="/my-past-tasks" class="nav-item" active-class="nav-item--active">
        <span class="nav-icon">✅</span>
        <span>Geçmiş Görevlerim</span>
      </router-link>
      <router-link v-if="auth.isAdminOrManager" to="/stock" class="nav-item" active-class="nav-item--active">
        <span class="nav-icon">📦</span>
        <span>Stok Yönetimi</span>
      </router-link>
      <router-link v-if="auth.isAdminOrManager" to="/settings" class="nav-item" active-class="nav-item--active">
        <span class="nav-icon">⚙️</span>
        <span>Ayarlar</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <div class="sidebar-user">
        <div class="user-avatar">{{ userInitials }}</div>
        <div class="user-info">
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
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 20px;
  border-bottom: 1px solid var(--border-color);
}
.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}
.logo-title {
  font-size: 1.1rem;
  font-weight: 800;
  letter-spacing: 1px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.logo-subtitle {
  display: block;
  font-size: 0.7rem;
  color: var(--text-muted);
  font-weight: 500;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 16px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
  transition: all var(--transition-fast);
  text-decoration: none;
}
.nav-item:hover {
  background: var(--bg-card);
  color: var(--text-primary);
}
.nav-item--active {
  background: var(--accent-blue) !important;
  color: white !important;
  box-shadow: 0 2px 8px rgba(79,110,247,0.3);
}
.nav-icon { font-size: 1.1rem; }

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-color);
}
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 12px;
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
.user-name { font-size: 0.85rem; font-weight: 600; }
.user-role { font-size: 0.7rem; color: var(--text-muted); }
</style>
