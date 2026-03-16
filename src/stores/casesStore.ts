/**
 * Cases Store — Jenan BIZ
 * Manages all cases with stage workflow, assignments, notes, approvals
 */

import { reactive, computed } from 'vue'
import type { UserRole } from '../types/roles'
import type {
  Case,
  RequestStage,
  StageHistoryEntry,
  InternalNote,
  StageApproval,
  Notification,
  CaseAssignment,
} from '../types/stages'
import {
  createNewCase,
  isValidTransition,
  isGatedStage,
  STAGES_ORDER,
  getStageProgress,
} from '../types/stages'
import { currentUser } from './authStore'

const CASES_KEY = 'jenanbiz_cases'
const NOTIF_KEY = 'jenanbiz_notifications'

// ─── UID Generator ─────────────────────────────────────
function uid(): string {
  return Date.now().toString(36).toUpperCase() + '-' + Math.random().toString(36).slice(2, 6).toUpperCase()
}

// ─── Persistence ───────────────────────────────────────
function loadCases(): Case[] {
  try {
    const raw = localStorage.getItem(CASES_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return []
}

function saveCases(cases: Case[]) {
  try {
    localStorage.setItem(CASES_KEY, JSON.stringify(cases))
  } catch { /* ignore */ }
}

function loadNotifications(): Notification[] {
  try {
    const raw = localStorage.getItem(NOTIF_KEY)
    if (raw) return JSON.parse(raw)
  } catch { /* ignore */ }
  return []
}

function saveNotifications(notifs: Notification[]) {
  try {
    localStorage.setItem(NOTIF_KEY, JSON.stringify(notifs))
  } catch { /* ignore */ }
}

// ─── State ─────────────────────────────────────────────
interface CasesState {
  cases: Case[]
  notifications: Notification[]
}

const state = reactive<CasesState>({
  cases: loadCases(),
  notifications: loadNotifications(),
})

// ─── Seed Demo Data ────────────────────────────────────
function seedDemoData() {
  if (state.cases.length > 0) return

  const now = new Date()
  const demoPartners = [
    { id: 'USR-PARTNER-001', name: 'أحمد الشريك' },
    { id: 'USR-PARTNER-002', name: 'سعد العمري' },
    { id: 'USR-PARTNER-003', name: 'نواف الحربي' },
  ]

  const demoCompanies = [
    { name: 'مؤسسة الأفق للتجارة', reg: '4030012345', type: 'مؤسسة فردية', age: 14 },
    { name: 'شركة المسار المحدودة', reg: '1010067890', type: 'شركة ذات مسؤولية محدودة', age: 8 },
    { name: 'مؤسسة بناء الخليج', reg: '4030098765', type: 'مؤسسة فردية', age: 24 },
    { name: 'شركة التقنية المتقدمة', reg: '1010054321', type: 'شركة مساهمة', age: 6 },
    { name: 'مؤسسة النجاح للمقاولات', reg: '4030011111', type: 'مؤسسة فردية', age: 3 },
  ]

  const stages: RequestStage[] = [
    'completing_request',
    'fee_contract_signed',
    'submitted',
    'approved',
    'analyzing',
  ]

  demoCompanies.forEach((company, i) => {
    const partner = demoPartners[i % demoPartners.length]
    const c = createNewCase(partner.id, partner.name)
    c.companyName = company.name
    c.registrationNumber = company.reg
    c.entityType = company.type
    c.ageInMonths = company.age
    c.isEligible = company.age >= 6
    c.crFileName = 'cr_' + company.reg + '.pdf'
    c.bsFileName = company.age >= 6 ? 'bs_' + company.reg + '.xlsx' : ''
    c.entityName = ['بنك الأول', 'بنك الرياض', 'البنك الأهلي', 'بنك الراجحي', 'بنك الإنماء'][i]

    // Set stage
    const targetStage = stages[i % stages.length]
    if (company.age < 6) {
      c.stage = 'rejected'
      c.resultSummary = 'عمر المنشأة أقل من 6 أشهر'
    } else {
      c.stage = targetStage
      // Build stage history up to current stage
      const stageIdx = STAGES_ORDER.indexOf(targetStage)
      for (let si = 0; si <= stageIdx; si++) {
        const ts = new Date(now.getTime() - (stageIdx - si) * 3600000 * 24).toISOString()
        if (si > 0) {
          c.stageHistory.push({
            id: uid(),
            stage: STAGES_ORDER[si],
            timestamp: ts,
            updatedBy: si % 2 === 0 ? 'USR-EMP-001' : 'USR-SUP-001',
            updatedByRole: si % 2 === 0 ? 'employee' : 'supervisor',
            updatedByName: si % 2 === 0 ? 'خالد الموظف' : 'فهد المشرف',
            note: 'تم الانتقال للمرحلة',
            attachments: [],
          })
        }
        c.lastStageChangeAt = ts
      }
      c.analysisProgress = 100
    }

    // Assign some to employee
    if (i < 3) {
      c.assignedTo = 'USR-EMP-001'
      c.assignedToName = 'خالد الموظف'
    }

    const created = new Date(now.getTime() - (5 - i) * 86400000).toISOString()
    c.createdAt = created
    c.updatedAt = c.lastStageChangeAt

    state.cases.push(c)
  })

  saveCases(state.cases)
}

seedDemoData()

// ─── Computed ──────────────────────────────────────────

/** All cases sorted newest first */
export const allCases = computed(() =>
  [...state.cases].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  )
)

/** Cases for a specific partner */
export function casesForPartner(partnerId: string) {
  return computed(() =>
    allCases.value.filter(c => c.partnerId === partnerId)
  )
}

/** Unassigned cases */
export const unassignedCases = computed(() =>
  allCases.value.filter(c => !c.assignedTo && c.stage !== 'rejected' && c.stage !== 'fees_received')
)

/** Cases assigned to a specific employee */
export function casesAssignedTo(employeeId: string) {
  return computed(() =>
    allCases.value.filter(c => c.assignedTo === employeeId)
  )
}

/** Cases needing partner info */
export const casesNeedingInfo = computed(() =>
  allCases.value.filter(c => c.stage === 'completing_request')
)

/** Cases with pending approvals */
export const casesPendingApproval = computed(() =>
  allCases.value.filter(c =>
    c.pendingApprovals.some(a => a.status === 'pending')
  )
)

/** All notifications for a user */
export function notificationsForUser(userId: string) {
  return computed(() =>
    state.notifications
      .filter(n => n.targetUserId === userId)
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  )
}

/** Unread notification count for a user */
export function unreadCount(userId: string) {
  return computed(() =>
    state.notifications.filter(n => n.targetUserId === userId && !n.read).length
  )
}

/** All notifications */
export const allNotifications = computed(() =>
  [...state.notifications].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  )
)

// ─── KPI Computeds (for Supervisor) ────────────────────

export const kpiCounts = computed(() => {
  const counts: Record<string, number> = {}
  for (const c of state.cases) {
    counts[c.stage] = (counts[c.stage] || 0) + 1
  }
  return counts
})

export const kpiTotal = computed(() => state.cases.length)

export const kpiCompleted = computed(() =>
  state.cases.filter(c => c.stage === 'fees_received').length
)

export const kpiRejected = computed(() =>
  state.cases.filter(c => c.stage === 'rejected').length
)

export const kpiAvgTransitionHours = computed(() => {
  let total = 0
  let count = 0
  for (const c of state.cases) {
    for (let i = 1; i < c.stageHistory.length; i++) {
      const diff = new Date(c.stageHistory[i].timestamp).getTime() - new Date(c.stageHistory[i - 1].timestamp).getTime()
      total += diff
      count++
    }
  }
  return count > 0 ? Math.round(total / count / 3600000) : 0
})

/** Cases where SLA is exceeded (> 48 hours without stage change) */
export const overdueCases = computed(() => {
  const threshold = 48 * 3600000 // 48 hours
  const now = Date.now()
  return allCases.value.filter(c => {
    if (c.stage === 'fees_received' || c.stage === 'rejected') return false
    return now - new Date(c.lastStageChangeAt).getTime() > threshold
  })
})

/** Hours since last stage change */
export function hoursSinceUpdate(c: Case): number {
  return Math.round((Date.now() - new Date(c.lastStageChangeAt).getTime()) / 3600000)
}

// ─── Mutations ─────────────────────────────────────────

/** Create a new case (from partner wizard) */
export function createCase(partnerId: string, partnerName: string): Case {
  const c = createNewCase(partnerId, partnerName)
  state.cases.push(c)
  saveCases(state.cases)
  return c
}

/** Get case by ID */
export function getCaseById(id: string): Case | undefined {
  return state.cases.find(c => c.id === id)
}

/** Update case fields */
export function updateCase(id: string, updates: Partial<Case>) {
  const idx = state.cases.findIndex(c => c.id === id)
  if (idx !== -1) {
    Object.assign(state.cases[idx], updates, { updatedAt: new Date().toISOString() })
    saveCases(state.cases)
  }
}

/** Advance stage (direct — non-gated or supervisor) */
export function advanceStage(
  caseId: string,
  toStage: RequestStage,
  userId: string,
  userRole: UserRole,
  userName: string,
  note: string = ''
): boolean {
  const c = getCaseById(caseId)
  if (!c) return false
  if (!isValidTransition(c.stage, toStage)) return false

  c.stage = toStage
  c.lastStageChangeAt = new Date().toISOString()
  c.updatedAt = c.lastStageChangeAt

  c.stageHistory.push({
    id: uid(),
    stage: toStage,
    timestamp: c.lastStageChangeAt,
    updatedBy: userId,
    updatedByRole: userRole,
    updatedByName: userName,
    note: note || `تم الانتقال إلى: ${toStage}`,
    attachments: [],
  })

  saveCases(state.cases)

  // Notify partner of stage change
  addNotification({
    type: 'stage_change',
    targetUserId: c.partnerId,
    targetRole: 'partner',
    caseId: c.id,
    message: `تم تحديث مرحلة الطلب ${c.id} إلى مرحلة جديدة`,
  })

  return true
}

/** Request stage transition (employee → supervisor approval) */
export function requestStageApproval(
  caseId: string,
  toStage: RequestStage,
  employeeId: string,
  employeeName: string,
  note: string = ''
): StageApproval | null {
  const c = getCaseById(caseId)
  if (!c) return null

  // Check there's no pending approval already
  if (c.pendingApprovals.some(a => a.status === 'pending')) return null

  const approval: StageApproval = {
    id: uid(),
    caseId,
    stage: toStage,
    requestedBy: employeeId,
    requestedByName: employeeName,
    requestedAt: new Date().toISOString(),
    approvedBy: null,
    approvedByName: null,
    approvedAt: null,
    status: 'pending',
    note,
  }

  c.pendingApprovals.push(approval)
  c.updatedAt = new Date().toISOString()
  saveCases(state.cases)

  // Notify all supervisors
  addNotification({
    type: 'approval_requested',
    targetUserId: 'USR-SUP-001',
    targetRole: 'supervisor',
    caseId,
    message: `الموظف ${employeeName} يطلب اعتماد انتقال مرحلة للطلب ${caseId}`,
  })

  return approval
}

/** Approve a pending stage transition (supervisor) */
export function approveStageTransition(
  caseId: string,
  approvalId: string,
  supervisorId: string,
  supervisorName: string
): boolean {
  const c = getCaseById(caseId)
  if (!c) return false

  const approval = c.pendingApprovals.find(a => a.id === approvalId)
  if (!approval || approval.status !== 'pending') return false

  approval.status = 'approved'
  approval.approvedBy = supervisorId
  approval.approvedByName = supervisorName
  approval.approvedAt = new Date().toISOString()

  // Actually advance the stage
  advanceStage(caseId, approval.stage, supervisorId, 'supervisor', supervisorName, `اعتماد: ${approval.note}`)

  // Notify requesting employee
  addNotification({
    type: 'approval_granted',
    targetUserId: approval.requestedBy,
    targetRole: 'employee',
    caseId,
    message: `تمت الموافقة على طلب الانتقال للطلب ${caseId}`,
  })

  saveCases(state.cases)
  return true
}

/** Reject a pending stage transition (supervisor) */
export function rejectStageTransition(
  caseId: string,
  approvalId: string,
  supervisorId: string,
  supervisorName: string,
  reason: string = ''
): boolean {
  const c = getCaseById(caseId)
  if (!c) return false

  const approval = c.pendingApprovals.find(a => a.id === approvalId)
  if (!approval || approval.status !== 'pending') return false

  approval.status = 'rejected'
  approval.approvedBy = supervisorId
  approval.approvedByName = supervisorName
  approval.approvedAt = new Date().toISOString()
  approval.note += reason ? ` | سبب الرفض: ${reason}` : ''

  c.updatedAt = new Date().toISOString()
  saveCases(state.cases)

  addNotification({
    type: 'approval_rejected',
    targetUserId: approval.requestedBy,
    targetRole: 'employee',
    caseId,
    message: `تم رفض طلب الانتقال للطلب ${caseId}${reason ? ': ' + reason : ''}`,
  })

  return true
}

/** Assign case to employee */
export function assignCase(
  caseId: string,
  employeeId: string,
  employeeName: string,
  assignedBy: string
) {
  const c = getCaseById(caseId)
  if (!c) return

  c.assignedTo = employeeId
  c.assignedToName = employeeName
  c.updatedAt = new Date().toISOString()
  saveCases(state.cases)

  addNotification({
    type: 'assignment',
    targetUserId: employeeId,
    targetRole: 'employee',
    caseId,
    message: `تم تعيين الطلب ${caseId} لك`,
  })
}

/** Claim case (employee assigns to self) */
export function claimCase(caseId: string, employeeId: string, employeeName: string) {
  assignCase(caseId, employeeId, employeeName, employeeId)
}

/** Add internal note */
export function addInternalNote(
  caseId: string,
  authorId: string,
  authorName: string,
  authorRole: UserRole,
  note: string
) {
  const c = getCaseById(caseId)
  if (!c) return

  c.internalNotes.push({
    id: uid(),
    authorId,
    authorName,
    authorRole,
    note,
    createdAt: new Date().toISOString(),
  })
  c.updatedAt = new Date().toISOString()
  saveCases(state.cases)
}

/** Request completion from partner (sends notification) */
export function requestCompletionFromPartner(
  caseId: string,
  requiredItems: string,
  requestedBy: string
) {
  const c = getCaseById(caseId)
  if (!c) return

  // Move to completing_request stage if not already
  if (c.stage !== 'completing_request') {
    c.stage = 'completing_request'
    c.lastStageChangeAt = new Date().toISOString()
    c.stageHistory.push({
      id: uid(),
      stage: 'completing_request',
      timestamp: c.lastStageChangeAt,
      updatedBy: requestedBy,
      updatedByRole: 'employee',
      updatedByName: '',
      note: `طلب استكمال: ${requiredItems}`,
      attachments: [],
    })
  }

  c.updatedAt = new Date().toISOString()
  saveCases(state.cases)

  addNotification({
    type: 'completion_required',
    targetUserId: c.partnerId,
    targetRole: 'partner',
    caseId,
    message: `مطلوب استكمال بيانات للطلب ${caseId}: ${requiredItems}`,
  })
}

/** Reject case (supervisor/owner) */
export function rejectCase(
  caseId: string,
  userId: string,
  userRole: UserRole,
  userName: string,
  reason: string
) {
  const c = getCaseById(caseId)
  if (!c) return

  c.stage = 'rejected'
  c.resultSummary = reason
  c.lastStageChangeAt = new Date().toISOString()
  c.updatedAt = c.lastStageChangeAt

  c.stageHistory.push({
    id: uid(),
    stage: 'rejected',
    timestamp: c.lastStageChangeAt,
    updatedBy: userId,
    updatedByRole: userRole,
    updatedByName: userName,
    note: `تم الرفض: ${reason}`,
    attachments: [],
  })

  saveCases(state.cases)

  addNotification({
    type: 'stage_change',
    targetUserId: c.partnerId,
    targetRole: 'partner',
    caseId,
    message: `للأسف، تم رفض الطلب ${caseId}`,
  })
}

// ─── Notifications ─────────────────────────────────────

function addNotification(opts: Omit<Notification, 'id' | 'read' | 'createdAt'>) {
  state.notifications.push({
    ...opts,
    id: uid(),
    read: false,
    createdAt: new Date().toISOString(),
  })
  saveNotifications(state.notifications)
}

export function markNotificationRead(id: string) {
  const n = state.notifications.find(x => x.id === id)
  if (n) {
    n.read = true
    saveNotifications(state.notifications)
  }
}

export function markAllRead(userId: string) {
  state.notifications.forEach(n => {
    if (n.targetUserId === userId) n.read = true
  })
  saveNotifications(state.notifications)
}

/** Check if any case is analyzing for a partner */
export function hasAnalyzingCaseForPartner(partnerId: string): boolean {
  return state.cases.some(c => c.partnerId === partnerId && c.stage === 'analyzing')
}
