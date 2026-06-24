import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/splash', name: 'Splash', component: () => import('../views/Splash.vue') },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue') },
  { path: '/verify', name: 'Verify', component: () => import('../views/VerifyCode.vue') },
  { path: '/forgot-password', name: 'ForgotPassword', component: () => import('../views/ForgotPassword.vue') },
  { path: '/reset-password', name: 'ResetPassword', component: () => import('../views/ForgotPassword.vue') },
  {
    path: '/',
    component: () => import('../views/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'Dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'nodes', name: 'Nodes', component: () => import('../views/Nodes.vue') },
      { path: 'plans', name: 'Plans', component: () => import('../views/Plans.vue') },
      { path: 'recharge', name: 'Recharge', component: () => import('../views/Recharge.vue') },
      { path: 'subscription', name: 'Subscription', component: () => import('../views/Subscription.vue') },
      { path: 'tutorials', name: 'Tutorials', component: () => import('../views/Tutorials.vue') },
      { path: 'invite', name: 'Invite', component: () => import('../views/Invite.vue') },
      { path: 'contact', name: 'Contact', component: () => import('../views/Contact.vue') },
      { path: 'notifications', name: 'Notifications', component: () => import('../views/Notifications.vue') },
      { path: 'notifications/:id', name: 'NotificationDetail', component: () => import('../views/NotificationDetail.vue') },
      {
        path: 'admin',
        children: [
          { path: '', name: 'AdminHome', component: () => import('../views/AdminHome.vue') },
          { path: 'users', name: 'AdminUsers', component: () => import('../views/AdminUsers.vue') },
          { path: 'nodes', name: 'AdminNodes', component: () => import('../views/AdminNodes.vue') },
          { path: 'plans', name: 'AdminPlans', component: () => import('../views/AdminPlans.vue') },
          { path: 'recharges', name: 'AdminRecharges', component: () => import('../views/AdminRecharges.vue') },
          { path: 'invite', name: 'AdminInvite', component: () => import('../views/AdminInvite.vue') },
          { path: 'notifications', name: 'AdminNotifications', component: () => import('../views/AdminNotifications.vue') },
          { path: 'contact', name: 'AdminContact', component: () => import('../views/AdminContact.vue') },
          { path: 'payment-qr', name: 'AdminPaymentQr', component: () => import('../views/AdminPaymentQr.vue') },
          { path: 'payment-settings', name: 'AdminPaymentSettings', component: () => import('../views/AdminPaymentSettings.vue') },
        ],
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, _from, next) => {
  const token = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !token) {
    next('/splash')
  } else if (to.path === '/splash' && token) {
    next('/')
  } else if (to.path.startsWith('/admin') && token) {
    try {
      const { default: api } = await import('../api')
      const { data } = await api.get('/auth/profile/')
      if (!data.is_staff) {
        next('/')
        return
      }
    } catch {
      next('/login')
      return
    }
    next()
  } else {
    next()
  }
})

export default router
