<template>
  <div class="min-h-screen min-h-dvh bg-bg">
    <!-- Top bar -->
    <header class="bg-white border-b border-border sticky top-0 z-30">
      <div class="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <img src="/logo.svg" alt="Jenan BIZ" class="h-8" />
          <span class="text-xs font-bold bg-brand/10 text-brand px-2 py-0.5 rounded-lg">موظف</span>
        </div>
        <div class="flex items-center gap-3">
          <NotificationBell />
          <span class="text-sm text-text-light hidden sm:inline">{{ userName }}</span>
          <button @click="showChangePass = true" class="text-text-light hover:text-blue transition-colors cursor-pointer p-1" title="تغيير كلمة المرور">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
            </svg>
          </button>
          <button @click="handleLogout" class="text-text-light hover:text-danger transition-colors cursor-pointer p-1" title="تسجيل خروج">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 pb-8">
      <!-- Quick Access — shown only if employee has elevated permissions -->
      <div v-if="hasElevatedPerms"
           class="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2">

        <!-- Approve Partners -->
        <button v-if="canApprovePartners"
          @click="showPendingPartners = !showPendingPartners"
          class="bg-white rounded-2xl border p-3 text-center hover:border-blue/40 transition-all cursor-pointer"
          :class="showPendingPartners ? 'border-blue' : 'border-border'">
          <div class="relative inline-block">
            <svg class="w-6 h-6 mx-auto text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0"/>
            </svg>
            <span v-if="pendingPartners.length > 0"
              class="absolute -top-1 -right-1 w-4 h-4 text-[10px] font-bold bg-danger text-white rounded-full flex items-center justify-center">
              {{ pendingPartners.length }}
            </span>
          </div>
          <p class="text-xs font-bold text-brand mt-1">موافقة الشركاء</p>
        </button>

        <!-- View Analytics -->
        <router-link v-if="canViewAnalytics" to="/supervisor"
          class="bg-white rounded-2xl border border-border p-3 text-center hover:border-blue/40 transition-all">
          <svg class="w-6 h-6 mx-auto text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
          <p class="text-xs font-bold text-brand mt-1">التقارير</p>
        </router-link>

        <!-- Add Users -->
        <router-link v-if="canAddUsers" to="/owner/users"
          class="bg-white rounded-2xl border border-border p-3 text-center hover:border-blue/40 transition-all">
          <svg class="w-6 h-6 mx-auto text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z"/>
          </svg>
          <p class="text-xs font-bold text-brand mt-1">إدارة المستخدمين</p>
        </router-link>

        <!-- Entities Settings -->
        <router-link v-if="canAddEntities || canEditEntities" to="/owner/entities"
          class="bg-white rounded-2xl border border-border p-3 text-center hover:border-blue/40 transition-all">
          <svg class="w-6 h-6 mx-auto text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
          </svg>
          <p class="text-xs font-bold text-brand mt-1">الجهات التمويلية</p>
        </router-link>

        <!-- Entity Contacts -->
        <router-link v-if="canViewEntityContacts" to="/owner/entity-contacts"
          class="bg-white rounded-2xl border border-border p-3 text-center hover:border-blue/40 transition-all">
          <svg class="w-6 h-6 mx-auto text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/>
          </svg>
          <p class="text-xs font-bold text-brand mt-1">موظفو الجهات</p>
        </router-link>

        <!-- Brokers -->
        <router-link v-if="canViewBrokers" to="/owner/brokers"
          class="bg-white rounded-2xl border border-border p-3 text-center hover:border-blue/40 transition-all">
          <svg class="w-6 h-6 mx-auto text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
          </svg>
          <p class="text-xs font-bold text-brand mt-1">سجل الوسطاء</p>
        </router-link>

        <!-- Business Registry -->
        <router-link v-if="canViewBusinessRegistry" to="/owner/businesses"
          class="bg-white rounded-2xl border border-border p-3 text-center hover:border-blue/40 transition-all">
          <svg class="w-6 h-6 mx-auto text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
          </svg>
          <p class="text-xs font-bold text-brand mt-1">سجل المنشآت</p>
        </router-link>

        <!-- Employee Stats -->
        <router-link v-if="canViewEmployeeStats" to="/owner/employee-stats"
          class="bg-white rounded-2xl border border-border p-3 text-center hover:border-blue/40 transition-all">
          <svg class="w-6 h-6 mx-auto text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
          <p class="text-xs font-bold text-brand mt-1">إحصائيات الموظفين</p>
        </router-link>

        <!-- رفع طلب جديد (when employee has create_cases permission) -->
        <router-link v-if="canCreateCases" to="/partner/request/new"
          class="bg-white rounded-2xl border border-border p-3 text-center hover:border-brand/40 transition-all">
          <svg class="w-6 h-6 mx-auto text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          <p class="text-xs font-bold text-brand mt-1">رفع طلب جديد</p>
        </router-link>

        <!-- Send Campaigns -->
        <router-link v-if="canSendCampaigns" to="/owner/campaigns"
          class="bg-white rounded-2xl border border-border p-3 text-center hover:border-blue/40 transition-all">
          <svg class="w-6 h-6 mx-auto text-brand" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
          </svg>
          <p class="text-xs font-bold text-brand mt-1">الحملات</p>
        </router-link>
      </div>

      <!-- Pending Partners Section -->
      <div v-if="canApprovePartners && showPendingPartners" class="mt-4 bg-white rounded-2xl border border-blue/30 p-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-bold text-brand">طلبات تسجيل الشركاء</h3>
          <span class="text-xs font-bold bg-blue/10 text-blue px-2 py-0.5 rounded-full">{{ pendingPartners.length }}</span>
        </div>
        <div v-if="loadingPartners" class="text-center py-4">
          <svg class="animate-spin w-5 h-5 mx-auto text-blue" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
          </svg>
        </div>
        <div v-else-if="pendingPartners.length === 0" class="text-center py-4 text-sm text-text-light">
          لا توجد طلبات معلّقة
        </div>
        <div v-else class="space-y-2">
          <div v-for="p in pendingPartners" :key="p.id"
               class="flex items-center justify-between p-3 bg-bg rounded-xl border border-border">
            <div>
              <p class="text-sm font-bold text-brand">{{ p.name }}</p>
              <p class="text-xs text-text-light">{{ p.phone }}</p>
            </div>
            <div class="flex gap-2">
              <button @click="approvePartner(p.id)" :disabled="processingPartnerId === p.id"
                class="text-xs font-bold bg-success/10 text-success px-3 py-1.5 rounded-lg hover:bg-success/20 transition-colors cursor-pointer disabled:opacity-50">
                قبول
              </button>
              <button @click="rejectPartner(p.id)" :disabled="processingPartnerId === p.id"
                class="text-xs font-bold bg-danger/10 text-danger px-3 py-1.5 rounded-lg hover:bg-danger/20 transition-colors cursor-pointer disabled:opacity-50">
                رفض
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Tab navigation -->
      <div class="mt-4 flex gap-1 bg-white rounded-xl border border-border p-1 overflow-x-auto">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          class="flex-1 min-w-[100px] py-2.5 px-3 rounded-lg text-xs font-bold text-center transition-all cursor-pointer whitespace-nowrap"
          :class="activeTab === tab.key ? 'bg-blue text-white shadow-sm' : 'text-text-light hover:bg-bg'"
        >
          {{ tab.label }}
          <span class="inline-block mr-1 min-w-[18px] h-[18px] leading-[18px] rounded-full text-[10px] text-center"
            :class="activeTab === tab.key ? 'bg-white/20' : 'bg-gray-200'">
            {{ tab.count }}
          </span>
        </button>
      </div>

      <!-- Search bar -->
      <div class="mt-4">
        <div class="relative">
          <svg class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-light" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="بحث بالمنشأة أو السجل أو رقم الطلب..."
            class="w-full bg-white border border-border rounded-xl py-2.5 pr-9 pl-3 text-sm focus:outline-none focus:border-blue transition-colors"
          />
          <button v-if="searchQuery" @click="searchQuery = ''" class="absolute left-3 top-1/2 -translate-y-1/2 text-text-light hover:text-danger cursor-pointer">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="mt-8 text-center">
        <svg class="animate-spin w-8 h-8 mx-auto text-blue" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
        </svg>
        <p class="text-sm text-text-light mt-2">جاري تحميل الطلبات...</p>
      </div>

      <!-- Cases list -->
      <div v-else class="mt-4 space-y-3">
        <div v-if="filteredCases.length === 0" class="bg-white rounded-2xl border border-border p-8 text-center">
          <svg class="w-12 h-12 mx-auto text-text-light/30 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
          </svg>
          <p class="text-sm text-text-light">لا توجد طلبات في هذا التصنيف</p>
        </div>

        <div
          v-for="c in filteredCases"
          :key="c.id"
          class="bg-white rounded-2xl border border-border p-4 hover:border-blue/30 hover:shadow-sm transition-all"
        >
          <div class="flex items-start justify-between gap-3" @click="openCase(c.id)" style="cursor:pointer">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-xs font-mono text-text-light">{{ c.display_id }}</span>
                <span v-if="!c.assigned_to" class="text-[10px] font-bold bg-warning/10 text-warning px-1.5 py-0.5 rounded">غير معيّن</span>
                <span v-else-if="c.assigned_to === userId" class="text-[10px] font-bold bg-blue/10 text-blue px-1.5 py-0.5 rounded">معيّن لي</span>
              </div>
              <p class="font-bold text-brand text-sm truncate">{{ c.company_name || '—' }}</p>

              <!-- Offer code instead of entity name -->
              <p class="text-xs text-text-light mt-0.5">المنتج: <span class="font-mono text-brand">{{ c.offer_code || '—' }}</span></p>
            </div>

            <div class="flex flex-col items-end gap-2 flex-shrink-0">
              <!-- Stage badge -->
              <span class="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium"
                :class="[stageConfig(c.stage).bgColor, stageConfig(c.stage).color]">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="stageConfig(c.stage).icon"/>
                </svg>
                {{ stageConfig(c.stage).label }}
              </span>
              <!-- SLA indicator -->
              <span class="text-[10px]" :class="hoursSince(c) > 48 ? 'text-danger font-bold' : hoursSince(c) > 24 ? 'text-warning' : 'text-text-light'">
                {{ hoursSince(c) > 0 ? `${hoursSince(c)} ساعة` : 'الآن' }}
              </span>
            </div>
          </div>

          <!-- Progress bar -->
          <div class="mt-3">
            <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full rounded-full transition-all duration-500"
                :class="c.stage === 'rejected' ? 'bg-danger' : 'bg-blue'"
                :style="{ width: stageProgress(c.stage) + '%' }">
              </div>
            </div>
          </div>

          <!-- Last update + claim button -->
          <div class="mt-1.5 flex items-center justify-between">
            <p class="text-[10px] text-text-light">آخر تحديث: {{ formatDate(c.updated_at) }}</p>
            <button
              v-if="!c.assigned_to && c.stage !== 'rejected' && c.stage !== 'fees_received'"
              @click.stop="doClaim(c.id)"
              :disabled="claimingId === c.id"
              class="text-xs font-bold text-blue bg-blue/10 px-3 py-1 rounded-lg hover:bg-blue/20 transition-colors cursor-pointer disabled:opacity-50"
            >استلام الطلب</button>
          </div>
        </div>
      </div>
    </main>

    <ChangePasswordModal v-model="showChangePass" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { currentUser, logout, refreshProfile } from '../../stores/authStore'
import { casesApi, usersApi } from '../../api/client'
import type { CaseResponse } from '../../api/client'
import { STAGE_MAP, getStageProgress } from '../../types/stages'
import type { RequestStage } from '../../types/stages'
import type { UserRole } from '../../types/roles'
import { ROLE_DEFAULT_PERMISSIONS } from '../../types/roles'
import NotificationBell from '../../components/NotificationBell.vue'
import ChangePasswordModal from '../../components/ChangePasswordModal.vue'

const router = useRouter()
const showChangePass = ref(false)
const userId = computed(() => currentUser.value?.id ?? '')
const userName = computed(() => currentUser.value?.name ?? '')

// ─── Local Permissions (computed from currentUser — fully reactive) ────────
const myPerms = computed<string[]>(() => {
  const u = currentUser.value
  if (!u) return []
  const role = u.role as UserRole
  const rolePerms = ROLE_DEFAULT_PERMISSIONS[role] || []
  const extra = u.extra_permissions || []
  return [...new Set([...rolePerms, ...extra])]
})

const canApprovePartners = computed(() => myPerms.value.includes('approve_partners'))
const canViewAnalytics   = computed(() => myPerms.value.includes('view_analytics'))
const canAddUsers        = computed(() => myPerms.value.includes('add_users'))
const canSendCampaigns   = computed(() => myPerms.value.includes('send_campaigns'))
const canAssignCases     = computed(() => myPerms.value.includes('assign_cases'))
const canCreateCases     = computed(() => myPerms.value.includes('create_cases'))
const canAddEntities          = computed(() => myPerms.value.includes('add_entities'))
const canEditEntities         = computed(() => myPerms.value.includes('edit_entities'))
const canViewEntityContacts   = computed(() => myPerms.value.includes('view_entity_contacts') || myPerms.value.includes('manage_entity_contacts'))
const canViewBrokers          = computed(() => myPerms.value.includes('view_brokers') || myPerms.value.includes('manage_brokers'))
const canViewBusinessRegistry = computed(() => myPerms.value.includes('view_business_registry') || myPerms.value.includes('manage_business_registry'))
const canViewEmployeeStats    = computed(() => myPerms.value.includes('view_employee_stats'))
const hasElevatedPerms   = computed(() =>
  canApprovePartners.value || canViewAnalytics.value ||
  canAddUsers.value || canSendCampaigns.value || canAssignCases.value ||
  canAddEntities.value || canEditEntities.value ||
  canViewEntityContacts.value || canViewBrokers.value ||
  canViewBusinessRegistry.value || canViewEmployeeStats.value ||
  canCreateCases.value
)

type TabKey = 'assigned' | 'unassigned' | 'need_info' | 'all'
const activeTab = ref<TabKey>('all')
const loading = ref(true)
const cases = ref<CaseResponse[]>([])

async function loadCases() {
  loading.value = true
  try {
    const resp = await casesApi.list({ size: 200 })
    cases.value = resp.items
  } catch { /* silent */ }
  loading.value = false
}

onMounted(async () => {
  // Get fresh user data (includes extra_permissions) then load cases
  await refreshProfile()
  await loadCases()
  await loadPendingPartners()
})

const myCases = computed(() => cases.value.filter(c => c.assigned_to === userId.value))
const unassigned = computed(() => cases.value.filter(c => !c.assigned_to && c.stage !== 'rejected' && c.stage !== 'fees_received'))
const needInfo = computed(() => cases.value.filter(c => c.stage === 'completing_request'))

const tabs = computed(() => [
  { key: 'assigned' as TabKey, label: 'طلباتي', count: myCases.value.length },
  { key: 'unassigned' as TabKey, label: 'جديدة', count: unassigned.value.length },
  { key: 'need_info' as TabKey, label: 'استكمال', count: needInfo.value.length },
  { key: 'all' as TabKey, label: 'الكل', count: cases.value.length },
])

const searchQuery = ref('')

const filteredCases = computed(() => {
  let base: CaseResponse[]
  switch (activeTab.value) {
    case 'assigned': base = myCases.value; break
    case 'unassigned': base = unassigned.value; break
    case 'need_info': base = needInfo.value; break
    case 'all': default: base = cases.value; break
  }
  if (!searchQuery.value.trim()) return base
  const q = searchQuery.value.trim().toLowerCase()
  return base.filter(c =>
    (c.company_name || '').toLowerCase().includes(q) ||
    (c.registration_number || '').toLowerCase().includes(q) ||
    (c.display_id || '').toLowerCase().includes(q)
  )
})

function stageConfig(stage: string) { return STAGE_MAP[stage as RequestStage] ?? STAGE_MAP['analyzing'] }
function stageProgress(stage: string) { return getStageProgress(stage as RequestStage) }

const claimingId = ref<string | null>(null)
async function doClaim(caseId: string) {
  claimingId.value = caseId
  try {
    await casesApi.claim(caseId)
    await loadCases()
  } catch { /* silent */ }
  claimingId.value = null
}

function hoursSince(c: CaseResponse): number {
  const ms = Date.now() - new Date(c.last_stage_change_at || c.updated_at).getTime()
  return Math.floor(ms / 3600000)
}

function formatDate(iso: string): string {
  const s = /[Zz]|[+\-]\d{2}:?\d{2}$/.test(iso) ? iso : iso + 'Z'
  return new Date(s).toLocaleDateString('ar-SA', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function openCase(id: string) { router.push(`/case/${id}`) }
function handleLogout() { logout(); router.push('/') }

// ─── Approve Partners (permission-gated) ──────────────

const pendingPartners = ref<any[]>([])
const loadingPartners = ref(false)
const showPendingPartners = ref(false)
const processingPartnerId = ref<string | null>(null)

async function loadPendingPartners() {
  if (!canApprovePartners.value) return
  loadingPartners.value = true
  try {
    const resp = await usersApi.listPending()
    pendingPartners.value = resp.items
  } catch { /* silent */ }
  loadingPartners.value = false
}

async function approvePartner(id: string) {
  processingPartnerId.value = id
  try {
    await usersApi.approveUser(id)
    pendingPartners.value = pendingPartners.value.filter(p => p.id !== id)
  } catch { /* silent */ }
  processingPartnerId.value = null
}

async function rejectPartner(id: string) {
  processingPartnerId.value = id
  try {
    await usersApi.rejectUser(id)
    pendingPartners.value = pendingPartners.value.filter(p => p.id !== id)
  } catch { /* silent */ }
  processingPartnerId.value = null
}
</script>
