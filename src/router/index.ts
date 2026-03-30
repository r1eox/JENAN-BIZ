import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import type { UserRole } from '../types/roles'
import { isLoggedIn, userRole } from '../stores/authStore'

// ─── Route Meta Types ─────────────────────────────────
declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: UserRole[]
  }
}

const routes: RouteRecordRaw[] = [
  // ─── Public ──────────────────────────
  {
    path: '/',
    name: 'Landing',
    component: () => import('../views/LandingPage.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginPage.vue'),
  },
  {
    path: '/signup',
    name: 'Signup',
    component: () => import('../views/SignupPage.vue'),
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('../views/ForgotPassword.vue'),
  },

  // ─── Partner ─────────────────────────
  {
    path: '/partner',
    name: 'PartnerDashboard',
    component: () => import('../views/partner/PartnerDashboard.vue'),
    meta: { requiresAuth: true, roles: ['partner', 'owner'] },
  },
  {
    path: '/partner/request/new',
    name: 'RequestWizard',
    component: () => import('../views/partner/RequestWizard.vue'),
    meta: { requiresAuth: true, roles: ['partner', 'owner'] },
  },
  {
    path: '/partner/documents/:id',
    name: 'DocumentUpload',
    component: () => import('../views/partner/DocumentUpload.vue'),
    props: true,
    meta: { requiresAuth: true, roles: ['partner', 'owner'] },
  },

  // ─── Employee ────────────────────────
  {
    path: '/employee',
    name: 'EmployeeDashboard',
    component: () => import('../views/employee/EmployeeDashboard.vue'),
    meta: { requiresAuth: true, roles: ['employee', 'supervisor', 'owner'] },
  },

  // ─── Supervisor ──────────────────────
  {
    path: '/supervisor',
    name: 'SupervisorDashboard',
    component: () => import('../views/supervisor/SupervisorDashboard.vue'),
    meta: { requiresAuth: true, roles: ['supervisor', 'owner'] },
  },

  // ─── Owner ───────────────────────────
  {
    path: '/owner',
    name: 'OwnerDashboard',
    component: () => import('../views/owner/OwnerDashboard.vue'),
    meta: { requiresAuth: true, roles: ['owner'] },
  },
  {
    path: '/owner/entities',
    name: 'EntitySettings',
    component: () => import('../views/owner/EntitySettings.vue'),
    meta: { requiresAuth: true, roles: ['owner'] },
  },
  {
    path: '/owner/users',
    name: 'UserManagement',
    component: () => import('../views/owner/UserManagement.vue'),
    meta: { requiresAuth: true, roles: ['owner'] },
  },
  {
    path: '/owner/contacts',
    name: 'ContactList',
    component: () => import('../views/owner/ContactList.vue'),
    meta: { requiresAuth: true, roles: ['owner'] },
  },
  {
    path: '/owner/campaigns',
    name: 'CampaignManager',
    component: () => import('../views/owner/CampaignManager.vue'),
    meta: { requiresAuth: true, roles: ['owner'] },
  },
  {
    path: '/owner/permissions',
    name: 'PermissionsManager',
    component: () => import('../views/owner/PermissionsManager.vue'),
    meta: { requiresAuth: true, roles: ['owner'] },
  },

  // ─── Shared ──────────────────────────
  {
    path: '/case/:id',
    name: 'CaseDetail',
    component: () => import('../views/shared/CaseDetail.vue'),
    props: true,
    meta: { requiresAuth: true },
  },

  // ─── Notifications ───────────────────
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('../views/NotificationsPage.vue'),
    meta: { requiresAuth: true },
  },

  // ─── 404 Catch-all ───────────────────
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// ─── Navigation Guards ─────────────────────────────────
router.beforeEach((to, _from, next) => {
  const needsAuth = to.meta.requiresAuth === true
  const allowedRoles = to.meta.roles as UserRole[] | undefined
  const publicOnlyPaths = ['/', '/login', '/signup', '/forgot-password']

  // If logged in and trying to access a public-only page → go to own dashboard
  if (isLoggedIn.value && publicOnlyPaths.includes(to.path)) {
    return next(getRoleLanding(userRole.value))
  }

  // Public page — allow
  if (!needsAuth) return next()

  // Not logged in — redirect to login
  if (!isLoggedIn.value) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }

  // Check role permission
  if (allowedRoles && allowedRoles.length > 0) {
    const role = userRole.value
    if (role && allowedRoles.includes(role)) {
      return next()
    }
    // Wrong role — redirect to their own dashboard
    return next(getRoleLanding(userRole.value))
  }

  // Auth required but no specific role restriction
  return next()
})

/** Map role → default landing path */
function getRoleLanding(role: UserRole | null): string {
  switch (role) {
    case 'partner':    return '/partner'
    case 'employee':   return '/employee'
    case 'supervisor': return '/supervisor'
    case 'owner':      return '/owner'
    default:           return '/'
  }
}

export default router
