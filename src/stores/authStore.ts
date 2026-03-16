/**
 * Auth Store — Jenan BIZ
 * Real JWT-based authentication + RBAC permissions
 */

import { reactive, computed } from 'vue'
import type { UserRole, User } from '../types/roles'
import type { RequestStage } from '../types/stages'
import { isGatedStage } from '../types/stages'
import { authApi, setTokens, clearTokens, getAccessToken } from '../api/client'
import type { UserResponse } from '../api/client'

const STORAGE_KEY = 'jenanbiz_auth'

interface AuthState {
  user: User | null
  loading: boolean
}

function mapApiUser(u: UserResponse): User {
  return {
    id: u.id,
    name: u.name,
    role: u.role as UserRole,
    phone: u.phone,
    createdAt: u.created_at,
  }
}

function loadUser(): User | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return null
}

function saveUser(user: User | null) {
  if (user) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
  } else {
    localStorage.removeItem(STORAGE_KEY)
  }
}

const state = reactive<AuthState>({
  user: loadUser(),
  loading: false,
})

// ─── Exports ────────────────────────────────────────────

export const currentUser = computed(() => state.user)
export const isLoggedIn = computed(() => !!state.user && !!getAccessToken())
export const userRole = computed<UserRole | null>(() => state.user?.role ?? null)
export const authLoading = computed(() => state.loading)

/** Real login — calls backend API */
export async function login(phone: string, password: string): Promise<User> {
  state.loading = true
  try {
    const resp = await authApi.login(phone, password)
    const user = mapApiUser(resp.user)
    state.user = user
    saveUser(user)
    return user
  } finally {
    state.loading = false
  }
}

/** Real registration — calls backend API */
export async function register(name: string, phone: string, password: string): Promise<void> {
  state.loading = true
  try {
    await authApi.register(name, phone, password)
  } finally {
    state.loading = false
  }
}

/** Refresh user profile from backend */
export async function refreshProfile(): Promise<void> {
  if (!getAccessToken()) return
  try {
    const resp = await authApi.me()
    const user = mapApiUser(resp)
    state.user = user
    saveUser(user)
  } catch {
    // Token expired or invalid
    logout()
  }
}

/** Logout */
export function logout() {
  state.user = null
  saveUser(null)
  authApi.logout()
}

/** Get default landing route for a role */
export function getRoleLanding(role: UserRole): string {
  switch (role) {
    case 'partner': return '/partner'
    case 'employee': return '/employee'
    case 'supervisor': return '/supervisor'
    case 'owner': return '/owner'
    default: return '/'
  }
}

// ─── RBAC Permission Checks ─────────────────────────────

/** Can the current user see entity names? (Only Owner) */
export function canSeeEntityNames(): boolean {
  return state.user?.role === 'owner'
}

/** Can the user claim/assign a case to themselves? (Employee) */
export function canClaimCase(): boolean {
  return state.user?.role === 'employee'
}

/** Can the user add internal notes? (Employee, Supervisor, Owner) */
export function canAddInternalNote(): boolean {
  const r = state.user?.role
  return r === 'employee' || r === 'supervisor' || r === 'owner'
}

/** Can the user advance a stage? */
export function canAdvanceStage(toStage: RequestStage): boolean {
  const r = state.user?.role
  if (!r) return false

  // Partner can never advance stages
  if (r === 'partner') return false

  // Owner can do anything
  if (r === 'owner') return true

  // Supervisor can approve gated stages
  if (r === 'supervisor') return true

  // Employee can advance non-gated stages directly
  if (r === 'employee') return !isGatedStage(toStage)

  return false
}

/** Can the user propose a gated stage transition? (Employee proposes → Supervisor approves) */
export function canProposeStageTransition(): boolean {
  const r = state.user?.role
  return r === 'employee'
}

/** Can the user approve stage transitions? (Supervisor, Owner) */
export function canApproveTransitions(): boolean {
  const r = state.user?.role
  return r === 'supervisor' || r === 'owner'
}

/** Can reject a request? (Supervisor, Owner) */
export function canRejectCase(): boolean {
  const r = state.user?.role
  return r === 'supervisor' || r === 'owner'
}

/** Can assign/reassign cases to employees? (Supervisor, Owner) */
export function canAssignCases(): boolean {
  const r = state.user?.role
  return r === 'supervisor' || r === 'owner'
}

/** Can request completion from partner? (Employee, Supervisor, Owner) */
export function canRequestCompletion(): boolean {
  const r = state.user?.role
  return r === 'employee' || r === 'supervisor' || r === 'owner'
}

/** Can delete a case? Nobody except maybe owner for drafts */
export function canDeleteCase(): boolean {
  return state.user?.role === 'owner'
}

/** Can see audit log? (Supervisor, Owner) */
export function canSeeAuditLog(): boolean {
  const r = state.user?.role
  return r === 'supervisor' || r === 'owner'
}

/** Can see KPIs / reports? (Supervisor, Owner) */
export function canSeeReports(): boolean {
  const r = state.user?.role
  return r === 'supervisor' || r === 'owner'
}

/** Can override decisions? (Owner only) */
export function canOverrideDecision(): boolean {
  return state.user?.role === 'owner'
}
