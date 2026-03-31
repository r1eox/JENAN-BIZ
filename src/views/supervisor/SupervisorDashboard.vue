<template>
  <div class="min-h-screen min-h-dvh bg-bg">
    <!-- Top bar -->
    <header class="bg-white border-b border-border sticky top-0 z-30">
      <div class="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <img src="/logo.svg" alt="Jenan BIZ" class="h-8" />
          <span class="text-xs font-bold px-2 py-0.5 rounded-lg"
            :class="{
              'bg-brand/10 text-brand': currentUser?.role === 'employee',
              'bg-warning/10 text-warning': currentUser?.role === 'supervisor',
              'bg-success/10 text-success': currentUser?.role === 'owner',
            }">
            {{ currentUser?.role === 'employee' ? 'موظف' : currentUser?.role === 'owner' ? 'المالك' : 'مشرف' }}
          </span>
        </div>
        <div class="flex items-center gap-3">
          <!-- Owner entity settings link -->
          <router-link v-if="currentUser?.role === 'owner'" to="/owner/entities" class="text-xs font-semibold bg-blue/10 text-blue px-2.5 py-1 rounded-lg hover:bg-blue/20 transition-colors">
            إعدادات الجهات
          </router-link>
          <NotificationBell />
          <span class="text-sm text-text-light hidden sm:inline">{{ userName }}</span>
          <button @click="showChangePass = true" class="text-text-light hover:text-blue transition-colors cursor-pointer p-1" title="تغيير كلمة المرور">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
            </svg>
          </button>
          <button @click="handleLogout" class="text-text-light hover:text-danger transition-colors cursor-pointer p-1">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-5xl mx-auto px-4 pb-8">
      <!-- KPI Cards -->
      <div class="mt-5 grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div class="bg-white rounded-2xl border border-border p-4 text-center">
          <p class="text-2xl font-bold text-brand">{{ kpiTotal }}</p>
          <p class="text-xs text-text-light mt-1">إجمالي الطلبات</p>
        </div>
        <div class="bg-white rounded-2xl border border-border p-4 text-center">
          <p class="text-2xl font-bold text-success">{{ kpiCompleted }}</p>
          <p class="text-xs text-text-light mt-1">مكتمل</p>
        </div>
        <div class="bg-white rounded-2xl border border-border p-4 text-center">
          <p class="text-2xl font-bold text-danger">{{ kpiRejected }}</p>
          <p class="text-xs text-text-light mt-1">مرفوض</p>
        </div>
        <div class="bg-white rounded-2xl border border-border p-4 text-center">
          <p class="text-2xl font-bold text-blue">{{ kpiAvgHours }}h</p>
          <p class="text-xs text-text-light mt-1">متوسط الانتقال</p>
        </div>
      </div>

      <!-- Stage distribution -->
      <div class="mt-4 bg-white rounded-2xl border border-border p-4">
        <h3 class="text-sm font-bold text-brand mb-3">توزيع المراحل</h3>
        <div class="space-y-2">
          <div v-for="(count, stage) in stageDistribution" :key="stage" class="flex items-center gap-2">
            <span class="text-xs text-text-light w-36 truncate">{{ STAGE_MAP[stage as RequestStage]?.label ?? stage }}</span>
            <div class="flex-1 h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all" :class="stage === 'rejected' ? 'bg-danger' : 'bg-blue'" :style="{ width: kpiTotal > 0 ? (count / kpiTotal * 100) + '%' : '0%' }"></div>
            </div>
            <span class="text-xs font-bold text-brand w-6 text-center">{{ count }}</span>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="mt-5 flex gap-1 bg-white rounded-xl border border-border p-1 overflow-x-auto">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          class="flex-1 min-w-[80px] py-2.5 px-3 rounded-lg text-xs font-bold text-center transition-all cursor-pointer whitespace-nowrap"
          :class="activeTab === tab.key ? 'bg-blue text-white shadow-sm' : 'text-text-light hover:bg-bg'"
        >
          {{ tab.label }}
          <span class="inline-block mr-1 min-w-[18px] h-[18px] leading-[18px] rounded-full text-[10px] text-center"
            :class="activeTab === tab.key ? 'bg-white/20' : 'bg-gray-200'">
            {{ tab.count }}
          </span>
        </button>
      </div>

      <!-- Search & Stage Filter -->
      <div class="mt-4 flex gap-2">
        <div class="relative flex-1">
          <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-light" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="بحث بالمنشأة أو السجل..."
            class="w-full bg-white border border-border rounded-xl py-2.5 pr-9 pl-3 text-sm focus:outline-none focus:border-blue transition-colors"
          />
        </div>
        <select
          v-model="stageFilter"
          class="bg-white border border-border rounded-xl px-3 py-2.5 text-sm text-brand focus:outline-none focus:border-blue cursor-pointer"
        >
          <option value="">كل المراحل</option>
          <option v-for="(conf, key) in STAGE_MAP" :key="key" :value="key">{{ conf.label }}</option>
        </select>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="mt-8 text-center">
        <svg class="animate-spin w-8 h-8 mx-auto text-blue" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
        </svg>
        <p class="text-sm text-text-light mt-2">جاري تحميل الطلبات...</p>
      </div>

      <!-- Cases List -->
      <div v-else class="mt-4 space-y-3">
        <div v-if="filteredCases.length === 0" class="bg-white rounded-2xl border border-border p-8 text-center">
          <p class="text-sm text-text-light">لا توجد طلبات في هذا التصنيف</p>
        </div>

        <div
          v-for="c in filteredCases"
          :key="c.id"
          class="bg-white rounded-2xl border border-border p-4 hover:border-blue/30 hover:shadow-sm transition-all"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1 flex-wrap">
                <span class="text-xs font-mono text-text-light">{{ c.display_id }}</span>
                <span v-if="hoursSince(c) > 48" class="text-[10px] font-bold bg-danger/10 text-danger px-1.5 py-0.5 rounded">SLA متأخر</span>
                <span v-if="(c.approvals || []).some((a: any) => a.status === 'pending')" class="text-[10px] font-bold bg-warning/10 text-warning px-1.5 py-0.5 rounded animate-pulse">
                  يحتاج اعتماد
                </span>
              </div>
              <p class="font-bold text-brand text-sm truncate">{{ c.company_name || '—' }}</p>
              <div class="flex items-center gap-3 mt-1 text-xs text-text-light flex-wrap">
                <span>المنتج: <span class="font-mono text-brand">{{ c.offer_code || '—' }}</span></span>
                <span v-if="c.assigned_to">معيّن</span>
                <span v-else class="text-warning font-medium">غير معيّن</span>
              </div>
            </div>

            <div class="flex flex-col items-end gap-1.5 flex-shrink-0">
              <span class="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium"
                :class="[stageConf(c.stage).bgColor, stageConf(c.stage).color]">
                {{ stageConf(c.stage).label }}
              </span>
              <span class="text-[10px]" :class="hoursSince(c) > 48 ? 'text-danger font-bold' : 'text-text-light'">
                {{ hoursSince(c) }}h
              </span>
            </div>
          </div>

          <!-- Progress bar -->
          <div class="mt-2.5">
            <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all"
                :class="c.stage === 'rejected' ? 'bg-danger' : 'bg-blue'"
                :style="{ width: getStageProgress(c.stage as RequestStage) + '%' }">
              </div>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="mt-3 flex items-center gap-2 flex-wrap">
            <button
              @click="openCase(c.id)"
              class="text-xs font-bold text-blue bg-blue/10 px-3 py-1.5 rounded-lg hover:bg-blue/20 transition-colors cursor-pointer"
            >تفاصيل</button>

            <!-- Assign button if unassigned -->
            <button
              v-if="!c.assigned_to"
              @click="showAssignModal(c.id)"
              class="text-xs font-bold text-brand bg-brand/10 px-3 py-1.5 rounded-lg hover:bg-brand/20 transition-colors cursor-pointer"
            >تعيين موظف</button>

            <!-- Approve pending -->
            <template v-if="(c.approvals || []).some((a: any) => a.status === 'pending')">
              <button
                @click="handleApproval(c, true)"
                class="text-xs font-bold text-success bg-success/10 px-3 py-1.5 rounded-lg hover:bg-success/20 transition-colors cursor-pointer"
              >✓ اعتماد</button>
              <button
                @click="handleApproval(c, false)"
                class="text-xs font-bold text-danger bg-danger/10 px-3 py-1.5 rounded-lg hover:bg-danger/20 transition-colors cursor-pointer"
              >✗ رفض الاعتماد</button>
            </template>

            <!-- Reject -->
            <button
              v-if="c.stage !== 'rejected' && c.stage !== 'fees_received' && c.stage !== 'analyzing'"
              @click="showRejectModal(c.id)"
              class="text-xs font-bold text-danger bg-danger/10 px-3 py-1.5 rounded-lg hover:bg-danger/20 transition-colors cursor-pointer"
            >رفض</button>
          </div>
        </div>
      </div>
    </main>

    <!-- Assign Modal -->
    <Teleport to="body">
      <div v-if="assignModalCaseId" class="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center" @click.self="assignModalCaseId = null">
        <div class="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-5">
          <h3 class="text-base font-bold text-brand mb-4">تعيين موظف</h3>
          <div class="space-y-2">
            <button
              v-for="emp in employees"
              :key="emp.id"
              @click="doAssign(emp)"
              class="w-full p-3 rounded-xl border border-border text-right hover:border-blue hover:bg-blue/5 transition-all cursor-pointer"
            >
              <p class="text-sm font-bold text-brand">{{ emp.name }}</p>
              <p class="text-xs text-text-light">{{ emp.id }}</p>
            </button>
          </div>
          <button @click="assignModalCaseId = null" class="w-full mt-3 py-2.5 rounded-xl border-2 border-border text-sm font-bold text-text-light hover:border-blue transition-colors cursor-pointer">إلغاء</button>
        </div>
      </div>
    </Teleport>

    <!-- Reject Modal -->
    <Teleport to="body">
      <div v-if="rejectModalCaseId" class="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center" @click.self="rejectModalCaseId = null">
        <div class="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-5">
          <h3 class="text-base font-bold text-danger mb-3">رفض الطلب</h3>
          <textarea v-model="rejectReason" rows="3" placeholder="سبب الرفض (مطلوب)..." class="w-full border-2 border-border rounded-xl p-3 text-sm focus:outline-none focus:border-danger resize-none"></textarea>
          <div class="flex gap-2 mt-4">
            <button @click="rejectModalCaseId = null" class="flex-1 py-2.5 rounded-xl border-2 border-border text-sm font-bold text-text-light hover:border-blue cursor-pointer">إلغاء</button>
            <button @click="doReject" :disabled="!rejectReason.trim()" class="flex-1 py-2.5 rounded-xl bg-danger text-white text-sm font-bold hover:bg-danger/90 disabled:opacity-50 cursor-pointer">تأكيد الرفض</button>
          </div>
        </div>
      </div>
    </Teleport>

    <ChangePasswordModal v-model="showChangePass" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { currentUser, logout } from '../../stores/authStore'
import { casesApi, usersApi } from '../../api/client'
import type { CaseResponse } from '../../api/client'
import { STAGE_MAP, getStageProgress } from '../../types/stages'
import type { RequestStage } from '../../types/stages'
import NotificationBell from '../../components/NotificationBell.vue'
import ChangePasswordModal from '../../components/ChangePasswordModal.vue'

const router = useRouter()
const showChangePass = ref(false)
const userId = computed(() => currentUser.value?.id ?? '')
const userName = computed(() => currentUser.value?.name ?? '')

// Data
const cases = ref<CaseResponse[]>([])
const employees = ref<{ id: string; name: string; phone: string }[]>([])
const kpi = ref<any>({})
const loading = ref(true)

async function loadData() {
  loading.value = true
  try {
    const [casesResp, kpiResp, empsResp] = await Promise.all([
      casesApi.list({ size: 500 }),
      casesApi.getKpis(),
      usersApi.listEmployees(),
    ])
    cases.value = casesResp.items
    kpi.value = kpiResp
    employees.value = empsResp
  } catch { /* silent */ }
  loading.value = false
}

onMounted(loadData)

// KPIs — backend returns total_cases / completed_cases / rejected_cases
const kpiTotal = computed(() => kpi.value.total_cases ?? kpi.value.total ?? cases.value.length)
const kpiCompleted = computed(() => kpi.value.completed_cases ?? kpi.value.completed ?? 0)
const kpiRejected = computed(() => kpi.value.rejected_cases ?? kpi.value.rejected ?? 0)
const kpiAvgHours = computed(() => kpi.value.avg_transition_hours ?? 0)

// Stage distribution
const stageDistribution = computed(() => {
  const dist: Record<string, number> = {}
  for (const c of cases.value) {
    dist[c.stage] = (dist[c.stage] || 0) + 1
  }
  return dist
})

type TabKey = 'all' | 'overdue' | 'pending' | 'unassigned'
const activeTab = ref<TabKey>('all')
const stageFilter = ref('')
const searchQuery = ref('')

function hoursSince(c: CaseResponse): number {
  const ms = Date.now() - new Date(c.last_stage_change_at || c.updated_at).getTime()
  return Math.floor(ms / 3600000)
}

const overdueCases = computed(() => cases.value.filter(c => hoursSince(c) > 48 && c.stage !== 'rejected' && c.stage !== 'fees_received'))
const pendingApproval = computed(() => cases.value.filter(c => (c.approvals || []).some((a: any) => a.status === 'pending')))
const unassignedCases = computed(() => cases.value.filter(c => !c.assigned_to && c.stage !== 'rejected' && c.stage !== 'fees_received'))

const tabs = computed(() => [
  { key: 'all' as TabKey, label: 'الكل', count: cases.value.length },
  { key: 'overdue' as TabKey, label: 'متأخرة', count: overdueCases.value.length },
  { key: 'pending' as TabKey, label: 'بانتظار اعتماد', count: pendingApproval.value.length },
  { key: 'unassigned' as TabKey, label: 'غير معيّنة', count: unassignedCases.value.length },
])

const filteredCases = computed(() => {
  let base: CaseResponse[]
  switch (activeTab.value) {
    case 'all': base = cases.value; break
    case 'overdue': base = overdueCases.value; break
    case 'pending': base = pendingApproval.value; break
    case 'unassigned': base = unassignedCases.value; break
    default: base = cases.value
  }
  if (stageFilter.value) {
    base = base.filter(c => c.stage === stageFilter.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    base = base.filter(c =>
      (c.company_name || '').toLowerCase().includes(q) ||
      (c.registration_number || '').toLowerCase().includes(q) ||
      (c.display_id || '').toLowerCase().includes(q)
    )
  }
  return base
})

// Assign modal
const assignModalCaseId = ref<string | null>(null)
function showAssignModal(caseId: string) { assignModalCaseId.value = caseId }
async function doAssign(emp: { id: string; name: string }) {
  if (!assignModalCaseId.value) return
  try {
    await casesApi.assign(assignModalCaseId.value, emp.id)
    assignModalCaseId.value = null
    await loadData()
  } catch { /* silent */ }
}

// Reject modal
const rejectModalCaseId = ref<string | null>(null)
const rejectReason = ref('')
function showRejectModal(caseId: string) { rejectModalCaseId.value = caseId; rejectReason.value = '' }
async function doReject() {
  if (!rejectModalCaseId.value || !rejectReason.value.trim()) return
  try {
    await casesApi.reject(rejectModalCaseId.value, rejectReason.value.trim())
    rejectModalCaseId.value = null
    rejectReason.value = ''
    await loadData()
  } catch { /* silent */ }
}

// Approve / reject pending approval
async function handleApproval(c: CaseResponse, approved: boolean) {
  const pending = (c.approvals || []).find((a: any) => a.status === 'pending')
  if (pending) {
    try {
      await casesApi.decideApproval(c.id, pending.id, approved)
      await loadData()
    } catch { /* silent */ }
  }
}

function stageConf(stage: string) { return STAGE_MAP[stage as RequestStage] ?? STAGE_MAP['analyzing'] }

function openCase(id: string) { router.push(`/case/${id}`) }
function handleLogout() { logout(); router.push('/') }
</script>
