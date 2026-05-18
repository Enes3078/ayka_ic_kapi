<template>
  <header class="app-header">
    <div class="header-left">
      <h1 class="header-page-title">{{ pageTitle }}</h1>
    </div>
    <div class="header-right">
      <button class="btn btn-ghost btn-sm" @click="auth.logout()">
        🚪 Çıkış Yap
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const auth = useAuthStore()

const pageTitles = {
  Dashboard: 'Dashboard',
  Tasks: 'Görevler',
}
const pageTitle = computed(() => pageTitles[route.name] || route.name || '')
</script>

<style scoped>
.app-header {
  height: var(--header-height);
  padding: 0 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
  position: sticky;
  top: 0;
  z-index: 50;
  backdrop-filter: blur(12px);
}
.header-page-title {
  font-size: 1.1rem;
  font-weight: 700;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
