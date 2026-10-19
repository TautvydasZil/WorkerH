import { createRouter, createWebHistory } from 'vue-router'
import API from '../api'

const routes = [
  { path: '/login', component: () => import('../views/LoginView.vue') },
  { path: '/register', component: () => import('../views/RegisterView.vue') },
  { path: '/reset-password', component: () => import('../views/ResetPasswordView.vue') },
  {
    path: '/',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true, allowedRoles: ['worker', 'manager'] }
  },
  {
    path: '/manager',
    component: () => import('../views/ManagerView.vue'),
    meta: { requiresAuth: true, allowedRoles: ['manager'] }
  },
  {
    path: '/admin',
    component: () => import('../views/AdminView.vue'),
    meta: { requiresAuth: true, allowedRoles: ['admin'] }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true

  try {
    const res = await API.get('/auth/me')
    const role = res.data?.role
    if (!role) return '/login'

    if (to.meta.allowedRoles && !to.meta.allowedRoles.includes(role)) {
      if (role === 'admin') return '/admin'
      if (role === 'manager') return '/manager'
      return '/'
    }

    return true
  } catch {
    return '/login'
  }
})

export default router
