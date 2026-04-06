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
  extra_permissions?: string[]
}

// Default permissions per role (mirrors backend ROLE_DEFAULT_PERMISSIONS)
export const ROLE_DEFAULT_PERMISSIONS: Record<UserRole, string[]> = {
  partner: [],
  employee: ['view_partner_files', 'update_case_stages'],
  supervisor: [
    'add_users', 'edit_users', 'approve_partners',
    'view_partner_files', 'view_employee_files', 'update_case_stages',
    'assign_cases', 'view_all_cases', 'view_analytics',
  ],
  owner: [
    'add_users', 'edit_users', 'promote_roles', 'approve_partners', 'manage_permissions',
    'view_partner_files', 'view_employee_files', 'update_case_stages', 'assign_cases',
    'view_all_cases', 'add_entities', 'edit_entities', 'send_campaigns', 'view_analytics',
    'view_entity_contacts', 'manage_entity_contacts',
    'view_brokers', 'manage_brokers',
    'view_business_registry', 'manage_business_registry',
    'view_employee_stats',
    'delete_cases', 'create_cases',
  ],
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
