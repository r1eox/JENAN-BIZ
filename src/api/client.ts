/**
 * Jenan BIZ — API Client
 * 
 * Centralized HTTP client for communicating with the FastAPI backend.
 * Handles JWT tokens, auto-refresh, error mapping, RTL error messages.
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// ─── Token Management ─────────────────────────────────

let accessToken: string | null = localStorage.getItem('access_token')
let refreshToken: string | null = localStorage.getItem('refresh_token')

export function setTokens(access: string, refresh: string) {
  accessToken = access
  refreshToken = refresh
  localStorage.setItem('access_token', access)
  localStorage.setItem('refresh_token', refresh)
}

export function clearTokens() {
  accessToken = null
  refreshToken = null
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export function getAccessToken() {
  return accessToken
}

// ─── HTTP Helpers ─────────────────────────────────────

interface ApiError {
  status: number
  message: string
  detail?: any
}

class ApiException extends Error {
  status: number
  detail: any
  
  constructor(status: number, message: string, detail?: any) {
    super(message)
    this.status = status
    this.detail = detail
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: any,
  options: { auth?: boolean; isFormData?: boolean } = {}
): Promise<T> {
  const { auth = true, isFormData = false } = options

  const headers: Record<string, string> = {}
  
  if (!isFormData) {
    headers['Content-Type'] = 'application/json'
  }

  if (auth && accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`
  }

  const fetchOptions: RequestInit = {
    method,
    headers,
  }

  if (body) {
    fetchOptions.body = isFormData ? body : JSON.stringify(body)
  }

  let response = await fetch(`${API_BASE}${path}`, fetchOptions)

  // Auto-refresh on 401
  if (response.status === 401 && auth && refreshToken) {
    const refreshed = await _refreshAccessToken()
    if (refreshed) {
      headers['Authorization'] = `Bearer ${accessToken}`
      fetchOptions.headers = headers
      response = await fetch(`${API_BASE}${path}`, fetchOptions)
    }
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new ApiException(
      response.status,
      errorBody.detail || 'حدث خطأ في الخادم',
      errorBody
    )
  }

  return response.json()
}

async function _refreshAccessToken(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (!res.ok) {
      clearTokens()
      window.location.href = '/JENAN-BIZ/login'
      return false
    }

    const data = await res.json()
    setTokens(data.access_token, data.refresh_token)
    return true
  } catch {
    clearTokens()
    window.location.href = '/JENAN-BIZ/login'
    return false
  }
}

// ─── Auth API ─────────────────────────────────────────

export interface UserResponse {
  id: string
  name: string
  phone: string
  role: string
  is_active: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: UserResponse
}

export const authApi = {
  async login(phone: string, password: string): Promise<TokenResponse> {
    const data = await request<TokenResponse>('POST', '/auth/login', { phone, password }, { auth: false })
    setTokens(data.access_token, data.refresh_token)
    return data
  },

  async register(name: string, phone: string, password: string): Promise<UserResponse> {
    return request('POST', '/auth/register', { name, phone, password }, { auth: false })
  },

  async me(): Promise<UserResponse> {
    return request('GET', '/auth/me')
  },

  logout() {
    clearTokens()
  },

  async forgotPassword(phone: string): Promise<{ message: string }> {
    return request('POST', '/auth/forgot-password', { phone }, { auth: false })
  },

  async verifyOtp(phone: string, code: string): Promise<{ reset_token: string }> {
    return request('POST', '/auth/verify-otp', { phone, code }, { auth: false })
  },

  async resetPassword(resetToken: string, newPassword: string): Promise<{ message: string }> {
    return request('POST', '/auth/reset-password', { reset_token: resetToken, new_password: newPassword }, { auth: false })
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    return request('POST', '/auth/change-password', { current_password: currentPassword, new_password: newPassword })
  },
}

// ─── Cases API ────────────────────────────────────────

export interface CaseResponse {
  id: string
  display_id: string
  partner_id: string
  company_name: string
  registration_number: string
  entity_type: string
  issue_date: string
  age_in_months: number
  stage: string
  is_eligible: boolean
  analysis_progress: number
  assigned_to: string | null
  partner_name: string
  assigned_to_name: string
  cr_file_name: string
  bs_file_name: string
  offer_code: string
  entity_name: string | null
  result_summary: string
  confidence_score: number
  last_stage_change_at: string
  created_at: string
  updated_at: string
  stage_history: any[]
  notes: any[]
  approvals: any[]
  // Override fields (owner)
  is_overridden?: boolean
  override_decision?: string
  override_reason?: string
  // Risk flags (from analysis_result.risk_flags)
  risk_flags?: Array<{ code: string; level: string; title_ar: string; detail_ar: string; value?: number; threshold?: number }>
  // Supplementary docs uploaded by partner
  supplementary_docs?: Array<{
    label: string
    original_name: string
    stored_name: string
    size: number
    uploaded_at: string
  }>
  // Analysis result (contains required_docs, ai_summary, financials, etc.)
  analysis_result?: Record<string, any>
}

export interface CaseListResponse {
  items: CaseResponse[]
  total: number
  page: number
  size: number
}

export const casesApi = {
  async list(params?: {
    stage?: string
    assigned_to?: string
    unassigned?: boolean
    page?: number
    size?: number
  }): Promise<CaseListResponse> {
    const searchParams = new URLSearchParams()
    if (params?.stage) searchParams.set('stage', params.stage)
    if (params?.assigned_to) searchParams.set('assigned_to', params.assigned_to)
    if (params?.unassigned) searchParams.set('unassigned', 'true')
    if (params?.page) searchParams.set('page', String(params.page))
    if (params?.size) searchParams.set('size', String(params.size))
    
    const qs = searchParams.toString()
    return request('GET', `/cases/${qs ? '?' + qs : ''}`)
  },

  async get(caseId: string): Promise<CaseResponse> {
    return request('GET', `/cases/${caseId}`)
  },

  async advance(caseId: string, note: string = ''): Promise<CaseResponse> {
    return request('POST', `/cases/${caseId}/advance`, { note })
  },

  async propose(caseId: string, targetStage: string, note: string = ''): Promise<any> {
    return request('POST', `/cases/${caseId}/propose`, { target_stage: targetStage, note })
  },

  async decideApproval(caseId: string, approvalId: string, approved: boolean, note: string = ''): Promise<CaseResponse> {
    return request('POST', `/cases/${caseId}/approvals/${approvalId}/decide`, { approved, note })
  },

  async reject(caseId: string, reason: string): Promise<CaseResponse> {
    return request('POST', `/cases/${caseId}/reject`, { reason })
  },

  async cancel(caseId: string): Promise<CaseResponse> {
    return request('POST', `/cases/${caseId}/cancel`)
  },

  async assign(caseId: string, employeeId: string): Promise<CaseResponse> {
    return request('POST', `/cases/${caseId}/assign`, { employee_id: employeeId })
  },

  async claim(caseId: string): Promise<CaseResponse> {
    return request('POST', `/cases/${caseId}/claim`)
  },

  async addNote(caseId: string, note: string): Promise<any> {
    return request('POST', `/cases/${caseId}/notes`, { note })
  },

  async requestCompletion(caseId: string, note: string): Promise<CaseResponse> {
    return request('POST', `/cases/${caseId}/request-completion`, { note })
  },

  async getKpis(): Promise<any> {
    return request('GET', '/cases/stats/kpi')
  },

  async getOwnerAnalytics(): Promise<any> {
    return request('GET', '/cases/stats/owner-analytics')
  },

  async overrideDecision(caseId: string, decision: string, reason: string): Promise<any> {
    return request('POST', `/cases/${caseId}/override`, { decision, reason })
  },

  async submitToEntity(caseId: string, note: string = ''): Promise<CaseResponse> {
    return request('POST', `/cases/${caseId}/submit-to-entity`, { note })
  },

  async downloadFile(caseId: string, fileType: 'cr' | 'bs'): Promise<Blob> {
    const headers: Record<string, string> = {}
    if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`
    const res = await fetch(`${API_BASE}/cases/${caseId}/download/${fileType}`, { headers })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new ApiException(res.status, err.detail || 'فشل تحميل الملف', err)
    }
    return res.blob()
  },

  async getNotifications(): Promise<any[]> {
    return request('GET', '/cases/notifications/list')
  },

  async markNotificationRead(notifId: string): Promise<void> {
    return request('POST', `/cases/notifications/${notifId}/read`)
  },

  async markAllNotificationsRead(): Promise<void> {
    return request('POST', '/cases/notifications/read-all')
  },
}

// ─── Analysis API ─────────────────────────────────────

export const analysisApi = {
  async createManualCase(facilityType: string): Promise<{ case_id: string; display_id: string }> {
    return request('POST', `/analysis/create-manual?facility_type=${encodeURIComponent(facilityType)}`)
  },

  async uploadCR(file: File, facilityType: string): Promise<{ case_id: string; display_id: string; ai_extracted?: Record<string, string> }> {
    const formData = new FormData()
    formData.append('file', file)
    return request('POST', `/analysis/upload-cr?facility_type=${encodeURIComponent(facilityType)}`, formData, { isFormData: true })
  },

  async aiAnalyzeCR(caseId: string): Promise<{ ai_extracted: Record<string, string>; age_in_months: number }> {
    return request('POST', `/analysis/${caseId}/ai-analyze-cr`)
  },

  async aiSummarize(caseId: string): Promise<{ ai_summary: string }> {
    return request('POST', `/analysis/${caseId}/ai-summarize`)
  },

  async updateCRInfo(caseId: string, info: {
    company_name?: string
    registration_number?: string
    entity_type?: string
    issue_date?: string
    age_in_months?: number
    activity?: string
  }): Promise<void> {
    const params = new URLSearchParams()
    Object.entries(info).forEach(([k, v]) => {
      if (v !== undefined) params.set(k, String(v))
    })
    return request('PATCH', `/analysis/${caseId}/cr-info?${params}`)
  },

  async updateQuestions(caseId: string, questions: {
    has_pos: boolean
    has_invoices: boolean
    partner_count: number
    is_saudi: boolean
  }): Promise<{ status: string }> {
    return request('PATCH', `/analysis/${caseId}/questions`, questions)
  },

  async saveFinancial(caseId: string, data: {
    monthly_income: number
    monthly_pos_sales: number
  }): Promise<void> {
    const params = new URLSearchParams()
    params.set('monthly_income', String(data.monthly_income))
    params.set('monthly_pos_sales', String(data.monthly_pos_sales))
    return request('PATCH', `/analysis/${caseId}/financial?${params}`)
  },

  async preFilter(caseId: string): Promise<{
    case_id: string
    has_eligible: boolean
    eligible_count: number
    required_bs_months: number
    rejected: boolean
  }> {
    return request('POST', `/analysis/${caseId}/pre-filter`)
  },

  async uploadBS(caseId: string, file: File): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)
    return request('POST', `/analysis/${caseId}/upload-bs`, formData, { isFormData: true })
  },

  async getStatus(caseId: string): Promise<{
    case_id: string
    stage: string
    analysis_progress: number
    is_eligible: boolean
    confidence_score: number
    result_summary: string
    offer_code: string
  }> {
    return request('GET', `/analysis/${caseId}/status`)
  },

  async getResult(caseId: string): Promise<any> {
    return request('GET', `/analysis/${caseId}/result`)
  },

  async getAuditLog(caseId: string): Promise<any[]> {
    return request('GET', `/analysis/${caseId}/audit`)
  },

  async uploadDocuments(caseId: string, files: File[]): Promise<{
    message: string
    files_count: number
    ai_summary: string
    next_stage: string
    uploaded_names: string[]
  }> {
    const fd = new FormData()
    for (const f of files) fd.append('files', f)
    const headers: Record<string, string> = {}
    if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`
    const res = await fetch(`${API_BASE}/analysis/${caseId}/upload-documents`, {
      method: 'POST',
      headers,
      body: fd,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new ApiException(res.status, err.detail || 'فشل رفع الملفات', err)
    }
    return res.json()
  },

  async downloadDoc(caseId: string, storedName: string, originalName: string): Promise<void> {
    const headers: Record<string, string> = {}
    if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`
    const res = await fetch(`${API_BASE}/analysis/${caseId}/docs/${encodeURIComponent(storedName)}`, { headers })
    if (!res.ok) throw new ApiException(res.status, 'فشل تحميل الملف')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = originalName
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },
}

// ─── Users API ────────────────────────────────────────

export const usersApi = {
  async list(params?: { role?: string; page?: number; size?: number }): Promise<any> {
    const searchParams = new URLSearchParams()
    if (params?.role) searchParams.set('role', params.role)
    if (params?.page) searchParams.set('page', String(params.page))
    if (params?.size) searchParams.set('size', String(params.size))
    const qs = searchParams.toString()
    return request('GET', `/users/${qs ? '?' + qs : ''}`)
  },

  async listEmployees(): Promise<{ id: string; name: string; phone: string }[]> {
    return request('GET', '/users/employees')
  },

  async create(data: { name: string; phone: string; password: string; role: string }): Promise<UserResponse> {
    return request('POST', '/users/', data)
  },

  async update(userId: string, data: { name?: string; phone?: string; role?: string; is_active?: boolean }): Promise<UserResponse> {
    return request('PATCH', `/users/${userId}`, data)
  },

  async deactivate(userId: string): Promise<void> {
    return request('DELETE', `/users/${userId}`)
  },

  async listPending(): Promise<{ items: any[]; total: number }> {
    return request('GET', '/users/pending')
  },

  async approveUser(userId: string): Promise<{ status: string; name: string }> {
    return request('POST', `/users/${userId}/approve`)
  },

  async rejectUser(userId: string): Promise<{ status: string }> {
    return request('POST', `/users/${userId}/reject`)
  },
}

// ─── Entity Rules API ─────────────────────────────────

export const entityRulesApi = {
  async list(): Promise<any[]> {
    return request('GET', '/entity-rules/')
  },

  async create(data: any): Promise<any> {
    return request('POST', '/entity-rules/', data)
  },

  async update(ruleId: string, data: any): Promise<any> {
    return request('PATCH', `/entity-rules/${ruleId}`, data)
  },

  async deactivate(ruleId: string): Promise<void> {
    return request('DELETE', `/entity-rules/${ruleId}`)
  },

  async reorder(items: { id: string; priority: number }[]): Promise<any[]> {
    return request('POST', '/entity-rules/reorder', { items })
  },

  async toggle(ruleId: string): Promise<{ status: string; is_active: boolean }> {
    return request('PATCH', `/entity-rules/${ruleId}/toggle`)
  },
}

// ─── Health check ─────────────────────────────────────

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`)
    return res.ok
  } catch {
    return false
  }
}

// ─── Notifications API ────────────────────────────────

export interface NotificationItem {
  id: string
  notification_type: string
  title: string
  message: string
  case_id: string | null
  is_read: boolean
  created_at: string
}

export interface NotificationListResponse {
  items: NotificationItem[]
  total: number
  unread: number
  page: number
  size: number
}

export const notificationsApi = {
  async list(page = 1, size = 20): Promise<NotificationListResponse> {
    return request('GET', `/notifications/?page=${page}&size=${size}`)
  },

  async unreadCount(): Promise<{ unread: number }> {
    return request('GET', '/notifications/unread')
  },

  async markRead(notifId: string): Promise<void> {
    return request('POST', `/notifications/${notifId}/read`)
  },

  async markAllRead(): Promise<void> {
    return request('POST', '/notifications/read-all')
  },

  async sendWhatsAppReminder(caseId: string, phone?: string, customMessage?: string): Promise<{ status: string; whatsapp_sent: boolean }> {
    return request('POST', `/notifications/send-whatsapp/${caseId}`, {
      phone: phone || '',
      custom_message: customMessage || '',
    })
  },

  async autoRemindMissingDocs(): Promise<{ total: number; sent: number; failed: number }> {
    return request('POST', '/notifications/auto-remind-missing-docs')
  },
}

// ─── Contacts API ─────────────────────────────────────

export interface ContactItem {
  id: string
  name: string
  phone: string
  company_name: string
  group_name: string
  notes: string
  tags: string[] | null
  is_active: boolean
  source: string
  created_at: string
}

export interface ContactListResponse {
  items: ContactItem[]
  total: number
  page: number
  size: number
}

export const contactsApi = {
  async list(params?: { group?: string; search?: string; page?: number; size?: number }): Promise<ContactListResponse> {
    const sp = new URLSearchParams()
    if (params?.group) sp.set('group', params.group)
    if (params?.search) sp.set('search', params.search)
    if (params?.page) sp.set('page', String(params.page))
    if (params?.size) sp.set('size', String(params.size))
    const qs = sp.toString()
    return request('GET', `/contacts/${qs ? '?' + qs : ''}`)
  },

  async groups(): Promise<{ groups: string[] }> {
    return request('GET', '/contacts/groups')
  },

  async create(data: { name?: string; phone: string; company_name?: string; group_name?: string; notes?: string; tags?: string[] }): Promise<ContactItem> {
    return request('POST', '/contacts/', data)
  },

  async update(id: string, data: { name?: string; phone?: string; company_name?: string; group_name?: string; notes?: string; tags?: string[]; is_active?: boolean }): Promise<ContactItem> {
    return request('PATCH', `/contacts/${id}`, data)
  },

  async remove(id: string): Promise<void> {
    return request('DELETE', `/contacts/${id}`)
  },

  async bulkImport(contacts: { name?: string; phone: string; company_name?: string; group_name?: string }[]): Promise<{ imported: number; skipped: number; errors: string[] }> {
    return request('POST', '/contacts/bulk', { contacts })
  },
}

// ─── Campaigns API ────────────────────────────────────

export interface CampaignItem {
  id: string
  title: string
  content_type: string
  content_text: string
  media_url: string
  media_caption: string
  target_audience: string
  target_group: string
  status: string
  total_recipients: number
  sent_count: number
  failed_count: number
  error_log: string[] | null
  sent_at: string | null
  created_at: string
  updated_at: string
}

export interface CampaignListResponse {
  items: CampaignItem[]
  total: number
  page: number
  size: number
}

export const campaignsApi = {
  async list(params?: { status?: string; page?: number; size?: number }): Promise<CampaignListResponse> {
    const sp = new URLSearchParams()
    if (params?.status) sp.set('status', params.status)
    if (params?.page) sp.set('page', String(params.page))
    if (params?.size) sp.set('size', String(params.size))
    const qs = sp.toString()
    return request('GET', `/campaigns/${qs ? '?' + qs : ''}`)
  },

  async get(id: string): Promise<CampaignItem> {
    return request('GET', `/campaigns/${id}`)
  },

  async create(data: {
    title: string
    content_type?: string
    content_text?: string
    media_url?: string
    media_caption?: string
    target_audience?: string
    target_group?: string
  }): Promise<CampaignItem> {
    return request('POST', '/campaigns/', data)
  },

  async update(id: string, data: any): Promise<CampaignItem> {
    return request('PATCH', `/campaigns/${id}`, data)
  },

  async remove(id: string): Promise<void> {
    return request('DELETE', `/campaigns/${id}`)
  },

  async send(id: string): Promise<{ status: string; total_recipients: number; message: string }> {
    return request('POST', `/campaigns/${id}/send`)
  },
}

export { ApiException }
