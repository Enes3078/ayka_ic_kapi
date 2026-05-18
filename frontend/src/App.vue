<template>
  <div v-if="isLoginPage">
    <router-view />
  </div>
  <div v-else class="app-layout">
    <AppSidebar />
    <div class="app-main">
      <AppHeader />
      <router-view />
    </div>
  </div>
  <!-- Toast Notifications -->
  <div class="toast-container">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="['toast', `toast-${toast.type}`]"
    >
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { computed, ref, provide } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from './components/layout/AppSidebar.vue'
import AppHeader from './components/layout/AppHeader.vue'

const route = useRoute()
const isLoginPage = computed(() => route.name === 'Login')

// Global toast system
const toasts = ref([])
let toastId = 0

function showToast(message, type = 'success', duration = 3000) {
  const id = ++toastId
  toasts.value.push({ id, message, type })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, duration)
}

provide('showToast', showToast)
</script>

<style scoped>
/* App-level scoped styles are minimal; global styles handle the rest */
</style>
