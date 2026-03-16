/**
 * Partner Requests Store — Jenan BIZ
 * Simple reactive store using Vue's reactivity system
 */

import { reactive, computed } from 'vue'
import type { PartnerRequest, RequestStatus } from '../types/request'
import { createNewRequest } from '../types/request'

const STORAGE_KEY = 'jenanbiz_requests'

interface RequestsState {
  requests: PartnerRequest[]
  currentRequestId: string | null
}

function loadFromStorage(): PartnerRequest[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw) as PartnerRequest[]
      // Restore without File objects (can't be serialized)
      return parsed.map(r => ({
        ...r,
        commercialReg: { ...r.commercialReg, file: null },
        bankStatement: r.bankStatement
          ? { ...r.bankStatement, file: null }
          : null,
      }))
    }
  } catch { /* ignore */ }
  return []
}

function saveToStorage(requests: PartnerRequest[]) {
  try {
    // Serialize without File objects
    const serializable = requests.map(r => ({
      ...r,
      commercialReg: { ...r.commercialReg, file: null },
      bankStatement: r.bankStatement
        ? { ...r.bankStatement, file: null }
        : null,
    }))
    localStorage.setItem(STORAGE_KEY, JSON.stringify(serializable))
  } catch { /* ignore */ }
}

const state = reactive<RequestsState>({
  requests: loadFromStorage(),
  currentRequestId: null,
})

/** All requests sorted by newest first */
export const requests = computed(() =>
  [...state.requests].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  )
)

/** Current active request */
export const currentRequest = computed(() =>
  state.requests.find(r => r.id === state.currentRequestId) || null
)

/** Create new request and set as current */
export function createRequest(): PartnerRequest {
  const req = createNewRequest()
  state.requests.push(req)
  state.currentRequestId = req.id
  saveToStorage(state.requests)
  return req
}

/** Set current request by ID */
export function setCurrentRequest(id: string | null) {
  state.currentRequestId = id
}

/** Update request fields */
export function updateRequest(id: string, updates: Partial<PartnerRequest>) {
  const idx = state.requests.findIndex(r => r.id === id)
  if (idx !== -1) {
    Object.assign(state.requests[idx], updates, {
      updatedAt: new Date().toISOString(),
    })
    saveToStorage(state.requests)
  }
}

/** Update request status */
export function updateStatus(id: string, status: RequestStatus) {
  updateRequest(id, { status })
}

/** Check if any request is currently being processed */
export function hasProcessingRequest(): boolean {
  return state.requests.some(r => r.status === 'analyzing')
}

/** Get request by ID */
export function getRequestById(id: string): PartnerRequest | undefined {
  return state.requests.find(r => r.id === id)
}

/** Delete request (only drafts) */
export function deleteRequest(id: string) {
  const idx = state.requests.findIndex(r => r.id === id)
  if (idx !== -1 && state.requests[idx].status === 'draft') {
    state.requests.splice(idx, 1)
    if (state.currentRequestId === id) {
      state.currentRequestId = null
    }
    saveToStorage(state.requests)
  }
}
