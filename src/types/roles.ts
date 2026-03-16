/**
 * Roles & RBAC Types — Jenan BIZ
 */

export type UserRole = 'partner' | 'employee' | 'supervisor' | 'owner'

export interface User {
  id: string
  name: string
  role: UserRole
  phone: string
  createdAt: string
}

export const ROLE_LABELS: Record<UserRole, string> = {
  partner: 'شريك',
  employee: 'موظف',
  supervisor: 'مشرف',
  owner: 'مدير النظام',
}

export const ROLE_COLORS: Record<UserRole, { text: string; bg: string }> = {
  partner: { text: 'text-blue', bg: 'bg-blue/10' },
  employee: { text: 'text-brand', bg: 'bg-brand/10' },
  supervisor: { text: 'text-warning', bg: 'bg-warning/10' },
  owner: { text: 'text-success', bg: 'bg-success/10' },
}
