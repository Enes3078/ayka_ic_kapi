import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('../views/TasksView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/tasks/:id',
    name: 'TaskDetail',
    component: () => import('../views/TaskDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/worker-tracking',
    name: 'WorkerTracking',
    component: () => import('../views/WorkerTrackingView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/worker-tracking/:id',
    name: 'WorkerDetail',
    component: () => import('../views/WorkerDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/my-team-queue',
    name: 'MyTeamQueue',
    component: () => import('../views/MyTeamQueueView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/my-past-tasks',
    name: 'MyPastTasks',
    component: () => import('../views/MyPastTasksView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/stock',
    name: 'Stock',
    component: () => import('../views/StockView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/reporting',
    name: 'Reporting',
    component: () => import('../views/ReportingView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')
  const userStr = localStorage.getItem('user_data')
  let isWorker = false // Varsayılanı false yap, login olan admin ise engellenmesin
  if (userStr) {
    try {
      const u = JSON.parse(userStr)
      isWorker = u.role === 'worker'
    } catch (e) {}
  }

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.guest && token) {
    next(isWorker ? '/my-team-queue' : '/')
  } else {
    // Çalışan sadece kendi ekranlarına girebilir
    const allowedWorkerPaths = ['/my-team-queue', '/my-past-tasks', '/login']
    if (token && isWorker && !allowedWorkerPaths.includes(to.path)) {
      next('/my-team-queue')
    } else {
      next()
    }
  }
})

export default router
