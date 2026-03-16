/**
 * Partner Request Types — Jenan BIZ
 * Updated for product-level workflow with pre-filtering.
 */

export type FacilityType = 'pos' | 'cash' | 'fleet'

export const FACILITY_TYPE_LABELS: Record<FacilityType, string> = {
  pos: 'نقاط بيع',
  cash: 'كاش',
  fleet: 'سيارات (أسطول)',
}

export type RequestStatus =
  | 'draft'
  | 'analyzing'
  | 'need_more_info'
  | 'eligible_need_docs'
  | 'not_eligible_currently'

export type EntityType =
  | 'مؤسسة فردية'
  | 'شركة ذات مسؤولية محدودة'
  | 'شركة مساهمة'
  | 'شركة تضامنية'
  | 'فرع شركة أجنبية'
  | 'شركة شخص واحد'
  | 'أخرى'

export interface CommercialRegistration {
  file: File | null
  fileName: string
  issueDate: string          // YYYY-MM-DD
  entityType: EntityType
  registrationNumber: string
  companyName: string
  activity: string
  ageInMonths: number
  isEligible: boolean
  requiredStatementMonths: number
  parsed: boolean
}

export interface MandatoryQuestions {
  has_pos: boolean | null
  has_invoices: boolean | null
  partner_count: number       // 1 or 2+
  is_saudi: boolean | null    // true=سعودي, false=مستثمر أجنبي
}

export interface PreFilterResult {
  has_eligible: boolean
  eligible_count: number
  required_bs_months: number
  rejected: boolean
}

export interface BankStatement {
  file: File | null
  fileName: string
  periodStart: string       // YYYY-MM-DD
  periodEnd: string         // YYYY-MM-DD
  coverageMonths: number
  hasRequiredColumns: boolean
  isValid: boolean
  parsed: boolean
}

export interface PartnerRequest {
  id: string
  createdAt: string          // ISO date
  updatedAt: string
  status: RequestStatus
  facilityType: FacilityType | null
  commercialReg: CommercialRegistration
  questions: MandatoryQuestions
  preFilter: PreFilterResult | null
  bankStatement: BankStatement | null
  analysisProgress: number   // 0–100
  resultSummary: string
  notes: string
}

/** Status display config */
export interface StatusConfig {
  label: string
  color: string
  bgColor: string
  icon: string
}

export const STATUS_MAP: Record<RequestStatus, StatusConfig> = {
  draft: {
    label: 'مسودة',
    color: 'text-gray-600',
    bgColor: 'bg-gray-100',
    icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
  },
  analyzing: {
    label: 'جاري التحليل',
    color: 'text-blue',
    bgColor: 'bg-blue/10',
    icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15',
  },
  need_more_info: {
    label: 'بحاجة لمعلومات إضافية',
    color: 'text-warning',
    bgColor: 'bg-warning/10',
    icon: 'M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  eligible_need_docs: {
    label: 'مؤهل — بانتظار المستندات',
    color: 'text-success',
    bgColor: 'bg-success/10',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  },
  not_eligible_currently: {
    label: 'غير مؤهل حالياً',
    color: 'text-danger',
    bgColor: 'bg-danger/10',
    icon: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
  },
}

/** Create empty commercial registration */
export function createEmptyCR(): CommercialRegistration {
  return {
    file: null,
    fileName: '',
    issueDate: '',
    entityType: 'أخرى',
    registrationNumber: '',
    companyName: '',
    activity: '',
    ageInMonths: 0,
    isEligible: false,
    requiredStatementMonths: 0,
    parsed: false,
  }
}

/** Create empty mandatory questions */
export function createEmptyQuestions(): MandatoryQuestions {
  return {
    has_pos: null,
    has_invoices: null,
    partner_count: 1,
    is_saudi: null,
  }
}

/** Create empty request */
export function createNewRequest(): PartnerRequest {
  const now = new Date().toISOString()
  return {
    id: 'REQ-' + Date.now().toString(36).toUpperCase(),
    createdAt: now,
    updatedAt: now,
    status: 'draft',
    facilityType: null,
    commercialReg: createEmptyCR(),
    questions: createEmptyQuestions(),
    preFilter: null,
    bankStatement: null,
    analysisProgress: 0,
    resultSummary: '',
    notes: '',
  }
}
