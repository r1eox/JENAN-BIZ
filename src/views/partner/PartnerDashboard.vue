<template>
  <div class="min-h-screen min-h-dvh bg-bg">
    <!-- Top bar -->
    <header class="bg-white border-b border-border sticky top-0 z-30">
      <div class="max-w-lg mx-auto px-4 h-14 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <img src="/logo.svg" alt="Jenan BIZ" class="h-8" />
        </div>
        <div class="flex items-center gap-3">
          <NotificationBell />
          <span class="text-sm text-text-light hidden sm:inline">مرحباً، {{ currentUser?.name || 'شريك' }}</span>
          <button
            @click="showChangePass = true"
            class="text-text-light hover:text-blue transition-colors cursor-pointer p-1"
            title="تغيير كلمة المرور"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
            </svg>
          </button>
          <button
            @click="handleLogout"
            class="text-text-light hover:text-danger transition-colors cursor-pointer p-1"
            title="تسجيل خروج"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-lg mx-auto px-4 pb-8">
      <!-- Welcome banner for newly approved partner (first login, no cases) -->
      <div v-if="!loading && allRequests.length === 0 && isNewlyApproved"
        class="mt-5 mb-4 bg-success/5 border border-success/25 rounded-2xl p-4 flex items-start gap-3">
        <div class="w-10 h-10 rounded-xl bg-success/15 flex items-center justify-center flex-shrink-0">
          <svg class="w-6 h-6 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <div class="flex-1">
          <p class="font-bold text-success text-sm">مرحباً {{ currentUser?.name }}، تم قبول حسابك!</p>
          <p class="text-xs text-success/80 mt-0.5 leading-relaxed">يمكنك الآن رفع طلبات التمويل بالضغط على "رفع طلب جديد" أعلاه.</p>
        </div>
        <button @click="isNewlyApproved = false" class="text-success/60 hover:text-success cursor-pointer p-0.5">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
      </div>

      <!-- New Request CTA -->
      <div class="mt-6 mb-6">
        <button
          @click="startNewRequest"
          :disabled="hasProcessing"
          class="w-full py-4 rounded-2xl bg-blue text-white font-bold text-lg shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center gap-2"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          رفع طلب جديد
        </button>
        <p v-if="hasProcessing" class="text-xs text-warning text-center mt-2 font-medium">
          يوجد طلب قيد التحليل حالياً. يرجى الانتظار حتى يكتمل.
        </p>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="mt-8 text-center">
        <svg class="animate-spin w-8 h-8 mx-auto text-blue" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
        </svg>
      </div>

      <!-- Requests List -->
      <div v-else>
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-base font-bold text-brand">طلباتي</h2>
          <span class="text-xs text-text-light bg-gray-100 px-2 py-0.5 rounded-full">
            {{ allRequests.length }} طلب
          </span>
        </div>

        <!-- Empty state -->
        <div v-if="allRequests.length === 0" class="bg-white rounded-2xl border border-border p-8 text-center">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-blue/10 flex items-center justify-center">
            <svg class="w-8 h-8 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
          </div>
          <p class="text-text-light text-sm">لا توجد طلبات سابقة</p>
          <p class="text-text-light/60 text-xs mt-1">اضغط "رفع طلب جديد" للبدء</p>
        </div>

        <!-- Request cards -->
        <div v-else class="space-y-3">
          <button
            v-for="req in allRequests"
            :key="req.id"
            @click="openRequest(req.id)"
            class="w-full bg-white rounded-2xl border border-border p-4 text-right hover:border-blue/30 hover:shadow-sm transition-all cursor-pointer"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <!-- Company name or ID -->
                <p class="font-bold text-brand text-sm truncate">
                  {{ req.company_name || req.display_id }}
                </p>
                <!-- Date -->
                <p class="text-xs text-text-light mt-1">
                  {{ formatDate(req.created_at) }}
                </p>
                <!-- CR number if available -->
                <p v-if="req.registration_number" class="text-xs text-text-light mt-0.5">
                  سجل تجاري: {{ req.registration_number }}
                </p>
              </div>

              <!-- Status badge -->
              <div class="flex-shrink-0">
                <span
                  class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium"
                  :class="[statusConfig(getStatus(req)).bgColor, statusConfig(getStatus(req)).color]"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="statusConfig(getStatus(req)).icon"/>
                  </svg>
                  {{ statusConfig(getStatus(req)).label }}
                </span>
              </div>
            </div>

            <!-- Upload docs CTA for completing_request (eligible OR manual review) -->
            <div v-if="req.stage === 'completing_request'" class="mt-3">
              <router-link
                :to="`/partner/documents/${req.id}`"
                @click.stop
                class="inline-flex items-center gap-1.5 text-xs font-bold text-white bg-warning px-3 py-1.5 rounded-lg hover:bg-yellow-500 transition-colors"
              >
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                </svg>
                ارفع المستندات المطلوبة
              </router-link>
            </div>

            <!-- Progress bar for actively analyzing cases (BS uploaded) -->
            <div v-if="req.stage === 'analyzing' && req.bs_file_name" class="mt-3">
              <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full bg-blue rounded-full transition-all duration-500"
                  :style="{ width: (req.analysis_progress || 0) + '%' }"
                ></div>
              </div>
              <p class="text-xs text-blue mt-1">جاري التحليل... {{ req.analysis_progress || 0 }}%</p>
            </div>

            <!-- Incomplete wizard – BS not uploaded yet -->
            <div v-else-if="req.stage === 'analyzing' && !req.bs_file_name" class="mt-3 flex items-center gap-2">
              <p class="text-xs text-text-light flex-1">لم يتم رفع كشف الحساب. أكمل الطلب أو اسحبه.</p>
              <button
                @click.stop="cancelCase(req.id)"
                :disabled="cancelingId === req.id"
                class="inline-flex items-center gap-1 text-xs font-medium text-danger border border-danger/30 bg-danger/5 px-2.5 py-1 rounded-lg hover:bg-danger/10 transition-colors disabled:opacity-50 cursor-pointer"
              >
                <svg v-if="cancelingId !== req.id" class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
                <svg v-else class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
                سحب
              </button>
            </div>

            <!-- Result summary -->
            <p v-if="req.result_summary" class="text-xs text-text-light mt-2 leading-relaxed">
              {{ req.result_summary }}
            </p>
          </button>
        </div>
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
import NotificationBell from '../../components/NotificationBell.vue'
import ChangePasswordModal from '../../components/ChangePasswordModal.vue'

const router = useRouter()

const showChangePass = ref(false)
const loading = ref(true)
const cases = ref<CaseResponse[]>([])
const cancelingId = ref<string | null>(null)

// Show welcome banner if partner just got approved (no cases + notif check via localStorage)
const isNewlyApproved = ref(false)

async function loadCases() {
  loading.value = true
  try {
    const resp = await casesApi.list({ size: 100 })
    cases.value = resp.items
    // Show welcome banner once for newly approved partner who hasn't submitted yet
    const key = `partner_welcomed_${currentUser.value?.id}`
    if (cases.value.length === 0 && !localStorage.getItem(key)) {
      isNewlyApproved.value = true
      localStorage.setItem(key, '1')
    }
  } catch { /* silent */ }
  loading.value = false
}

onMounted(loadCases)

const allRequests = computed(() => cases.value)
// Only block new requests when a case is actively being AI-analyzed (BS uploaded).
// Cases where the wizard was abandoned (no BS) should not block the partner.
const hasProcessing = computed(() =>
  cases.value.some(c => c.stage === 'analyzing' && !!c.bs_file_name)
)

type ReqStatus = 'analyzing' | 'incomplete' | 'eligible' | 'rejected' | 'processing' | 'completed' | 'needs_completion'

function getStatus(c: CaseResponse): ReqStatus {
  if (c.stage === 'analyzing') return c.bs_file_name ? 'analyzing' : 'incomplete'
  if (c.stage === 'rejected') return 'rejected'
  if (c.stage === 'fees_received') return 'completed'
  if (c.stage === 'completing_request') return 'needs_completion'
  if (c.is_eligible) return 'eligible'
  return 'processing'
}

const STATUS_MAP: Record<ReqStatus, { label: string; bgColor: string; color: string; icon: string }> = {
  analyzing: { label: 'جاري التحليل', bgColor: 'bg-blue/10', color: 'text-blue', icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' },
  incomplete: { label: 'غير مكتمل', bgColor: 'bg-gray-100', color: 'text-text-light', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' },
  eligible: { label: 'مؤهل', bgColor: 'bg-success/10', color: 'text-success', icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' },
  rejected: { label: 'مرفوض', bgColor: 'bg-danger/10', color: 'text-danger', icon: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z' },
  needs_completion: { label: 'مطلوب استكمال ⚠', bgColor: 'bg-warning/15', color: 'text-warning font-bold', icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' },
  processing: { label: 'قيد المعالجة', bgColor: 'bg-warning/10', color: 'text-warning', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
  completed: { label: 'مكتمل', bgColor: 'bg-success/10', color: 'text-success', icon: 'M5 13l4 4L19 7' },
}

function statusConfig(status: ReqStatus) {
  return STATUS_MAP[status]
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString('ar-SA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function startNewRequest() {
  if (hasProcessing.value) return
  router.push('/partner/request/new')
}

async function cancelCase(id: string) {
  if (cancelingId.value) return
  if (!confirm('هل أنت متأكد من سحب هذا الطلب؟ لا يمكن التراجع.')) return
  cancelingId.value = id
  try {
    await casesApi.cancel(id)
    cases.value = cases.value.filter(c => c.id !== id)
  } catch {
    alert('حدث خطأ أثناء سحب الطلب. حاول مجدداً.')
  } finally {
    cancelingId.value = null
  }
}

function openRequest(id: string) {
  router.push(`/case/${id}`)
}

function handleLogout() { logout(); router.push('/') }
</script>
