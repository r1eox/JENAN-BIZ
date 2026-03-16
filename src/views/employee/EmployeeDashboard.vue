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

        <button
          v-for="c in filteredCases"
          :key="c.id"
          @click="openCase(c.id)"
          class="w-full bg-white rounded-2xl border border-border p-4 text-right hover:border-blue/30 hover:shadow-sm transition-all cursor-pointer"
        >
          <div class="flex items-start justify-between gap-3">
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

          <!-- Last update -->
          <p class="text-[10px] text-text-light mt-1.5">آخر تحديث: {{ formatDate(c.updated_at) }}</p>
        </button>
      </div>
    </main>

    <ChangePasswordModal v-model="showChangePass" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { currentUser, logout } from '../../stores/authStore'
import { casesApi } from '../../api/client'
import type { CaseResponse } from '../../api/client'
import { STAGE_MAP, getStageProgress } from '../../types/stages'
import type { RequestStage } from '../../types/stages'
import NotificationBell from '../../components/NotificationBell.vue'
import ChangePasswordModal from '../../components/ChangePasswordModal.vue'

const router = useRouter()
const showChangePass = ref(false)
const userId = computed(() => currentUser.value?.id ?? '')
const userName = computed(() => currentUser.value?.name ?? '')

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

onMounted(loadCases)

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

function hoursSince(c: CaseResponse): number {
  const ms = Date.now() - new Date(c.last_stage_change_at || c.updated_at).getTime()
  return Math.floor(ms / 3600000)
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('ar-SA', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function openCase(id: string) { router.push(`/case/${id}`) }
function handleLogout() { logout(); router.push('/') }
</script>
