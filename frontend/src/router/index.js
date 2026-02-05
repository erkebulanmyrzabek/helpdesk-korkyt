import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import TeacherDashboard from '../views/TeacherDashboard.vue'
import HelpdeskDashboard from '../views/HelpdeskDashboard.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import AdminReviews from '../views/AdminReviews.vue'
import AdminSettings from '../views/AdminSettings.vue'
import AdminReports from '../views/AdminReports.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/teacher',
      name: 'teacher',
      component: TeacherDashboard,
      meta: { requiresAuth: true, role: 'teacher' }
    },
    {
      path: '/helpdesk',
      name: 'helpdesk',
      component: HelpdeskDashboard,
      meta: { requiresAuth: true, role: 'helpdesk' }
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminDashboard,
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/admin/reviews',
      name: 'admin-reviews',
      component: AdminReviews,
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/admin/settings',
      name: 'admin-settings',
      component: AdminSettings,
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/admin/reports',
      name: 'admin-reports',
      component: AdminReports,
      meta: { requiresAuth: true, role: 'admin' }
    }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.role && authStore.user?.role !== to.meta.role) {
    // Redirect to correct dashboard if wrong role
    if (authStore.isTeacher) next('/teacher')
    else if (authStore.isHelpdesk) next('/helpdesk')
    else if (authStore.isAdmin) next('/admin')
    else next('/login')
  } else {
    next()
  }
})

export default router
