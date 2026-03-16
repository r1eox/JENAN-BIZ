/**
 * Request Stages & Workflow — Jenan BIZ
 *
 * Stages flow:
 *   1. التحليل → 2. استكمال الطلب → 3. تم توقيع عقد الأتعاب → 4. استكمال نماذج التسهيلات
 *   → 5. تم الرفع → 6. تمت الموافقة → 7. تم التوقيع → 8. تم تحويل التسهيلات
 *   → 9. تم استلام الأتعاب
 *   At any point (after analysis): ❌ تم الرفض
 */

import type { UserRole } from './roles'

// ─── Stages ────────────────────────────────────────────

export type RequestStage =
  | 'analyzing'            // 1. التحليل (auto)
  | 'completing_request'   // 2. استكمال الطلب
  | 'fee_contract_signed'  // 3. تم توقيع عقد الأتعاب
  | 'completing_forms'     // 4. استكمال نماذج التسهيلات
  | 'submitted'            // 5. تم الرفع
  | 'approved'             // 6. تمت الموافقة
  | 'signed'               // 7. تم التوقيع
  | 'facilities_transferred' // 8. تم تحويل التسهيلات
  | 'fees_received'        // 9. تم استلام الأتعاب
  | 'rejected'             // ❌ تم الرفض

/** Ordered list for progress tracking */
export const STAGES_ORDER: RequestStage[] = [
  'analyzing',
  'completing_request',
  'fee_contract_signed',
  'completing_forms',
  'submitted',
  'approved',
  'signed',
  'facilities_transferred',
  'fees_received',
]

export interface StageConfig {
  label: string
  color: string
  bgColor: string
  icon: string
  index: number
}

export const STAGE_MAP: Record<RequestStage, StageConfig> = {
  analyzing: {
    label: 'التحليل',
    color: 'text-blue',
    bgColor: 'bg-blue/10',
    icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
    index: 0,
  },
  completing_request: {
    label: 'استكمال الطلب',
    color: 'text-warning',
    bgColor: 'bg-warning/10',
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    index: 1,
  },
  fee_contract_signed: {
    label: 'تم توقيع عقد الأتعاب',
    color: 'text-blue',
    bgColor: 'bg-blue/10',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    index: 2,
  },
  completing_forms: {
    label: 'استكمال نماذج التسهيلات',
    color: 'text-warning',
    bgColor: 'bg-warning/10',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
    index: 3,
  },
  submitted: {
    label: 'تم الرفع',
    color: 'text-blue',
    bgColor: 'bg-blue/10',
    icon: 'M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12',
    index: 4,
  },
  approved: {
    label: 'تمت الموافقة',
    color: 'text-success',
    bgColor: 'bg-success/10',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    index: 5,
  },
  signed: {
    label: 'تم التوقيع',
    color: 'text-success',
    bgColor: 'bg-success/10',
    icon: 'M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z',
    index: 6,
  },
  facilities_transferred: {
    label: 'تم تحويل التسهيلات',
    color: 'text-success',
    bgColor: 'bg-success/10',
    icon: 'M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z',
    index: 7,
  },
  fees_received: {
    label: 'تم استلام الأتعاب',
    color: 'text-success',
    bgColor: 'bg-success/10',
    icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    index: 8,
  },
  rejected: {
    label: 'تم الرفض',
    color: 'text-danger',
    bgColor: 'bg-danger/10',
    icon: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
    index: -1,
  },
}

/** Get stage index for progress calculation */
export function getStageIndex(stage: RequestStage): number {
  if (stage === 'rejected') return -1
  return STAGES_ORDER.indexOf(stage)
}

/** Get stage progress percentage (0–100) */
export function getStageProgress(stage: RequestStage): number {
  if (stage === 'rejected') return 0
  const idx = STAGES_ORDER.indexOf(stage)
  if (idx === -1) return 0
  return Math.round(((idx + 1) / STAGES_ORDER.length) * 100)
}

// ─── Gated Stages (require supervisor approval) ────────

export const GATED_STAGES: RequestStage[] = [
  'submitted',
  'approved',
  'signed',
  'facilities_transferred',
  'fees_received',
  'rejected',
]

export function isGatedStage(stage: RequestStage): boolean {
  return GATED_STAGES.includes(stage)
}

/** Get next allowed stage from current */
export function getNextStage(current: RequestStage): RequestStage | null {
  if (current === 'rejected' || current === 'fees_received') return null
  const idx = STAGES_ORDER.indexOf(current)
  if (idx === -1 || idx >= STAGES_ORDER.length - 1) return null
  return STAGES_ORDER[idx + 1]
}

/** Check if transition from → to is valid (sequential only, or rejected) */
export function isValidTransition(from: RequestStage, to: RequestStage): boolean {
  if (to === 'rejected') return from !== 'analyzing' // can reject after analysis
  if (to === 'completing_request') return from === 'analyzing' || STAGES_ORDER.indexOf(from) > 0 // can return to completing
  const fromIdx = STAGES_ORDER.indexOf(from)
  const toIdx = STAGES_ORDER.indexOf(to)
  return toIdx === fromIdx + 1
}

// ─── Stage History ─────────────────────────────────────

export interface StageHistoryEntry {
  id: string
  stage: RequestStage
  timestamp: string       // ISO
  updatedBy: string       // user ID
  updatedByRole: UserRole
  updatedByName: string
  note: string
  attachments: string[]   // file names
}

// ─── Internal Notes ────────────────────────────────────

export interface InternalNote {
  id: string
  authorId: string
  authorName: string
  authorRole: UserRole
  note: string
  createdAt: string
}

// ─── Stage Approvals (Gated Stages) ───────────────────

export type ApprovalStatus = 'pending' | 'approved' | 'rejected'

export interface StageApproval {
  id: string
  caseId: string
  stage: RequestStage
  requestedBy: string      // employee ID
  requestedByName: string
  requestedAt: string
  approvedBy: string | null
  approvedByName: string | null
  approvedAt: string | null
  status: ApprovalStatus
  note: string
}

// ─── Case Assignment ──────────────────────────────────

export interface CaseAssignment {
  caseId: string
  employeeId: string
  employeeName: string
  assignedAt: string
  assignedBy: string       // supervisor or self
}

// ─── Notifications ────────────────────────────────────

export type NotificationType =
  | 'stage_change'
  | 'completion_required'
  | 'assignment'
  | 'reassignment'
  | 'approval_requested'
  | 'approval_granted'
  | 'approval_rejected'

export interface Notification {
  id: string
  type: NotificationType
  targetUserId: string
  targetRole: UserRole
  caseId: string
  message: string
  read: boolean
  createdAt: string
}

// ─── Enhanced Case (extends PartnerRequest) ───────────

export interface Case {
  id: string
  createdAt: string
  updatedAt: string

  // Partner info
  partnerId: string
  partnerName: string

  // Company info
  companyName: string
  registrationNumber: string
  entityType: string
  issueDate: string
  ageInMonths: number

  // New workflow fields
  facilityType: string          // 'pos' | 'cash' | 'fleet'
  hasPos: boolean | null
  hasInvoices: boolean | null
  partnerCount: number
  isSaudi: boolean | null
  activity: string
  preFilterPassed: string[] | null
  matchedProductCode: string
  requiredBsMonths: number

  // Stage workflow
  stage: RequestStage
  stageHistory: StageHistoryEntry[]
  analysisProgress: number

  // Assignment
  assignedTo: string | null       // employee ID
  assignedToName: string | null

  // Files
  crFileName: string
  bsFileName: string

  // Internal
  internalNotes: InternalNote[]
  pendingApprovals: StageApproval[]

  // Result
  isEligible: boolean
  resultSummary: string

  // Offer code (entity name hidden — only owner sees real name)
  offerCode: string               // e.g. "PRD-001"
  entityName: string              // real entity name — ONLY for owner role

  // SLA
  lastStageChangeAt: string       // for SLA tracking
}

/** Generate unique ID */
function uid(): string {
  return Date.now().toString(36).toUpperCase() + '-' + Math.random().toString(36).slice(2, 6).toUpperCase()
}

/** Create a new case from partner submission */
export function createNewCase(partnerId: string, partnerName: string): Case {
  const now = new Date().toISOString()
  return {
    id: 'CASE-' + uid(),
    createdAt: now,
    updatedAt: now,
    partnerId,
    partnerName,
    companyName: '',
    registrationNumber: '',
    entityType: '',
    issueDate: '',
    ageInMonths: 0,
    facilityType: '',
    hasPos: null,
    hasInvoices: null,
    partnerCount: 1,
    isSaudi: null,
    activity: '',
    preFilterPassed: null,
    matchedProductCode: '',
    requiredBsMonths: 0,
    stage: 'analyzing',
    stageHistory: [{
      id: uid(),
      stage: 'analyzing',
      timestamp: now,
      updatedBy: partnerId,
      updatedByRole: 'partner',
      updatedByName: partnerName,
      note: 'تم إنشاء الطلب',
      attachments: [],
    }],
    analysisProgress: 0,
    assignedTo: null,
    assignedToName: null,
    crFileName: '',
    bsFileName: '',
    internalNotes: [],
    pendingApprovals: [],
    isEligible: false,
    resultSummary: '',
    offerCode: 'PRD-' + Math.floor(100 + Math.random() * 900),
    entityName: '',
    lastStageChangeAt: now,
  }
}
