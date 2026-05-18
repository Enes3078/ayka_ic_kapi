<template>
  <div class="login-page">
    <div class="login-bg-effect"></div>
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">⚙</div>
        <h1 class="login-title">MES</h1>
        <p class="login-subtitle">Endüstriyel Üretim Yönetim Sistemi</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label class="form-label">Kullanıcı Adı</label>
          <input
            v-model="username"
            type="text"
            class="form-input"
            placeholder="admin"
            required
            autofocus
          />
        </div>
        <div class="form-group">
          <label class="form-label">Şifre</label>
          <input
            v-model="password"
            type="password"
            class="form-input"
            placeholder="••••••"
            required
          />
        </div>

        <div v-if="error" class="login-error">{{ error }}</div>

        <button type="submit" class="btn btn-primary w-full" :disabled="loading">
          <span v-if="loading" class="spinner" style="width:18px;height:18px;border-width:2px;"></span>
          <span v-else>Giriş Yap</span>
        </button>
      </form>

      <p class="login-hint">Varsayılan: admin / admin123</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    if (auth.user?.role === 'worker') {
      router.push('/my-team-queue')
    } else {
      router.push('/')
    }
  } catch (err) {
    error.value = err.response?.data?.non_field_errors?.[0]
      || err.response?.data?.detail
      || 'Giriş başarısız. Bilgilerinizi kontrol edin.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  position: relative;
  overflow: hidden;
}

.login-bg-effect {
  position: absolute;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(79,110,247,0.12) 0%, transparent 70%);
  top: -100px;
  right: -100px;
  pointer-events: none;
}

.login-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: var(--shadow-lg);
  animation: slideUp var(--transition-slow);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}
.login-logo {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  box-shadow: 0 4px 20px rgba(79,110,247,0.3);
}
.login-title {
  font-size: 1.8rem;
  font-weight: 800;
  letter-spacing: 2px;
  background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.login-subtitle {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-top: 4px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.login-error {
  background: var(--accent-red-bg);
  color: var(--accent-red);
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  border: 1px solid #ef444433;
}

.login-hint {
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 20px;
}
</style>
