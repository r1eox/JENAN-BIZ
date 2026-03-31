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
          <NotificationBell />
          <router-link to="/owner/contacts" class="text-sm text-text-light hover:text-blue transition-colors">جهات الاتصال</router-link>
          <router-link to="/owner/users" class="text-sm text-text-light hover:text-blue transition-colors">المستخدمون</router-link>
          <button @click="handleLogout" class="text-text-light hover:text-danger transition-colors cursor-pointer p-1">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-5xl mx-auto px-4 pb-8">
      <!-- Page title -->
      <div class="mt-6 mb-4 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 class="text-xl font-bold text-brand">الحملات التسويقية</h1>
          <p class="text-sm text-text-light mt-1">إنشاء وإرسال حملات واتساب إلى الشركاء وجهات الاتصال</p>
        </div>
        <div class="flex gap-2">
          <button
            @click="autoRemind"
            :disabled="reminding"
            class="bg-amber-50 border border-amber-200 text-amber-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-amber-100 transition-colors cursor-pointer flex items-center gap-2 disabled:opacity-50"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            تذكير تلقائي (مستندات ناقصة)
          </button>
          <button
            @click="openCreateModal"
            class="bg-blue text-white text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-blue/90 transition-colors cursor-pointer flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            حملة جديدة
          </button>
        </div>
      </div>

      <!-- Auto-remind result -->
      <div v-if="remindResult" class="mb-4 p-3 rounded-xl text-sm" :class="remindResult.failed > 0 ? 'bg-amber-50 text-amber-800 border border-amber-200' : 'bg-success/10 text-success border border-success/20'">
        تم إرسال {{ remindResult.sent }} تذكير واتساب من أصل {{ remindResult.total }} طلب معلّق
        <span v-if="remindResult.failed > 0"> — {{ remindResult.failed }} فشل</span>
      </div>

      <!-- Status filters -->
      <div class="flex flex-wrap gap-2 mb-4">
        <button
          v-for="s in statusFilters"
          :key="s.value"
          @click="filterStatus = s.value; fetchCampaigns()"
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer"
          :class="filterStatus === s.value ? 'bg-blue text-white' : 'bg-white text-text-light border border-border hover:border-blue/30'"
        >
          {{ s.label }}
        </button>
      </div>

      <!-- Campaigns list -->
      <div class="space-y-3">
        <div v-if="loading" class="bg-white rounded-2xl border border-border p-8 text-center text-text-light text-sm">جاري التحميل...</div>
        <div v-else-if="campaigns.length === 0" class="bg-white rounded-2xl border border-border p-8 text-center text-text-light text-sm">لا توجد حملات</div>

        <div
          v-for="c in campaigns"
          :key="c.id"
          class="bg-white rounded-2xl border border-border p-4"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <h3 class="text-sm font-bold text-brand">{{ c.title }}</h3>
                <span
                  class="inline-flex px-2 py-0.5 rounded-lg text-[10px] font-medium"
                  :class="statusClass(c.status)"
                >
                  {{ statusLabel(c.status) }}
                </span>
                <span class="inline-flex px-2 py-0.5 rounded-lg text-[10px] font-medium bg-gray-100 text-text-light">
                  {{ contentLabel(c.content_type) }}
                </span>
              </div>

              <p class="text-xs text-text-light mb-2 line-clamp-2">{{ c.content_text || c.media_caption || '(بدون نص)' }}</p>

              <div class="flex items-center gap-4 text-xs text-text-light">
                <span>الجمهور: {{ audienceLabel(c.target_audience) }}</span>
                <span v-if="c.total_recipients > 0">المستلمون: {{ c.total_recipients }}</span>
                <span v-if="c.sent_count > 0" class="text-success">تم إرسال: {{ c.sent_count }}</span>
                <span v-if="c.failed_count > 0" class="text-danger">فشل: {{ c.failed_count }}</span>
              </div>

              <div class="flex items-center gap-2 text-[10px] text-text-light/60 mt-1">
                <span>{{ formatDate(c.created_at) }}</span>
                <span v-if="c.sent_at">• أُرسلت {{ formatDate(c.sent_at) }}</span>
              </div>

              <!-- Error log (collapsed) -->
              <details v-if="c.error_log && c.error_log.length > 0" class="mt-2">
                <summary class="text-[10px] text-danger cursor-pointer select-none">عرض أخطاء الإرسال ({{ c.error_log.length }})</summary>
                <div class="mt-1 bg-danger/5 border border-danger/20 rounded-lg p-2 max-h-28 overflow-y-auto space-y-0.5">
                  <p v-for="(e, i) in c.error_log" :key="i" class="text-[10px] text-danger font-mono break-all">{{ e }}</p>
                </div>
              </details>
            </div>

            <div class="flex items-center gap-1 flex-shrink-0">
              <button
                v-if="c.status === 'draft'"
                @click="sendCampaign(c)"
                class="bg-success/10 text-success text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-success/20 transition-colors cursor-pointer"
              >
                إرسال
              </button>
              <button
                v-if="c.status === 'failed' || c.status === 'sent'"
                @click="sendCampaign(c)"
                class="bg-amber-50 text-amber-700 text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-amber-100 transition-colors cursor-pointer border border-amber-200"
              >
                إعادة إرسال
              </button>
              <button
                v-if="c.status === 'draft'"
                @click="openEditModal(c)"
                class="text-blue hover:text-blue-dark p-1.5 cursor-pointer"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                </svg>
              </button>
              <button
                v-if="c.status !== 'sending'"
                @click="removeCampaign(c.id)"
                class="text-danger hover:text-red-700 p-1.5 cursor-pointer"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Create/Edit Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" @click.self="showModal = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6" @click.stop>
          <h3 class="text-lg font-bold text-brand mb-4">{{ editingCampaign ? 'تعديل الحملة' : 'حملة جديدة' }}</h3>

          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">عنوان الحملة *</label>
              <input v-model="form.title" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="عنوان الحملة" />
            </div>

            <div>
              <label class="block text-xs font-medium text-text-light mb-1">نوع المحتوى</label>
              <select v-model="form.content_type" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue bg-white">
                <option value="text">نص</option>
                <option value="image">صورة</option>
                <option value="video">فيديو</option>
                <option value="document">مستند</option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-medium text-text-light mb-1">النص</label>
              <textarea v-model="form.content_text" rows="4" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue resize-none" placeholder="نص الرسالة..."></textarea>
            </div>

            <div v-if="form.content_type !== 'text'">
              <label class="block text-xs font-medium text-text-light mb-1">رابط الملف (URL)</label>
              <input v-model="form.media_url" dir="ltr" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="https://..." />
            </div>

            <div v-if="form.content_type !== 'text'">
              <label class="block text-xs font-medium text-text-light mb-1">وصف الملف</label>
              <input v-model="form.media_caption" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="وصف اختياري" />
            </div>

            <div>
              <label class="block text-xs font-medium text-text-light mb-1">الجمهور المستهدف</label>
              <select v-model="form.target_audience" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue bg-white">
                <option value="all">الكل (مسجلين + خارجيين)</option>
                <option value="all_users">المسجلين فقط</option>
                <option value="partners">الشركاء فقط</option>
                <option value="employees">الموظفين فقط</option>
                <option value="external">جهات خارجية فقط</option>
                <option value="custom_group">مجموعة مخصصة</option>
              </select>
            </div>

            <div v-if="form.target_audience === 'custom_group'">
              <label class="block text-xs font-medium text-text-light mb-1">اسم المجموعة</label>
              <input v-model="form.target_group" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="مثال: عملاء VIP" />
            </div>
          </div>

          <p v-if="formError" class="text-xs text-danger mt-3">{{ formError }}</p>

          <div class="flex gap-2 mt-5">
            <button
              @click="submitForm"
              :disabled="formSaving"
              class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-semibold hover:bg-blue/90 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {{ formSaving ? 'جاري الحفظ...' : (editingCampaign ? 'حفظ التعديلات' : 'إنشاء مسودة') }}
            </button>
            <button @click="showModal = false" class="px-4 py-2.5 rounded-xl bg-gray-100 text-text-light text-sm font-medium hover:bg-gray-200 transition-colors cursor-pointer">
              إلغاء
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { campaignsApi, notificationsApi, type CampaignItem } from '../../api/client'
import { logout, currentUser } from '../../stores/authStore'
import NotificationBell from '../../components/NotificationBell.vue'
import { useRouter } from 'vue-router'
const router = useRouter()
function handleLogout() { logout(); router.push('/login') }

const campaigns = ref<CampaignItem[]>([])
const loading = ref(false)
const filterStatus = ref('')
const reminding = ref(false)
const remindResult = ref<{ total: number; sent: number; failed: number } | null>(null)

// Modal
const showModal = ref(false)
const editingCampaign = ref<CampaignItem | null>(null)
const form = ref({
  title: '',
  content_type: 'text',
  content_text: '',
  media_url: '',
  media_caption: '',
  target_audience: 'all',
  target_group: '',
})
const formError = ref('')
const formSaving = ref(false)

const statusFilters = [
  { value: '', label: 'الكل' },
  { value: 'draft', label: 'مسودة' },
  { value: 'sending', label: 'قيد الإرسال' },
  { value: 'sent', label: 'مُرسلة' },
  { value: 'failed', label: 'فاشلة' },
]

onMounted(() => fetchCampaigns())

async function fetchCampaigns() {
  loading.value = true
  try {
    const data = await campaignsApi.list({
      status: filterStatus.value || undefined,
      page: 1,
      size: 50,
    })
    campaigns.value = data.items
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

function statusLabel(s: string): string {
  const map: Record<string, string> = { draft: 'مسودة', sending: 'قيد الإرسال', sent: 'مُرسلة', failed: 'فاشلة', cancelled: 'ملغية' }
  return map[s] || s
}

function statusClass(s: string): string {
  const map: Record<string, string> = {
    draft: 'bg-gray-100 text-text-light',
    sending: 'bg-blue/10 text-blue',
    sent: 'bg-success/10 text-success',
    failed: 'bg-danger/10 text-danger',
    cancelled: 'bg-gray-100 text-text-light',
  }
  return map[s] || ''
}

function contentLabel(t: string): string {
  const map: Record<string, string> = { text: 'نص', image: 'صورة', video: 'فيديو', document: 'مستند' }
  return map[t] || t
}

function audienceLabel(a: string): string {
  const map: Record<string, string> = {
    all: 'الكل',
    all_users: 'المسجلين',
    partners: 'الشركاء',
    employees: 'الموظفين',
    external: 'خارجيين',
    custom_group: 'مجموعة مخصصة',
  }
  return map[a] || a
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('ar-SA', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function openCreateModal() {
  editingCampaign.value = null
  form.value = { title: '', content_type: 'text', content_text: '', media_url: '', media_caption: '', target_audience: 'all', target_group: '' }
  formError.value = ''
  showModal.value = true
}

function openEditModal(c: CampaignItem) {
  editingCampaign.value = c
  form.value = {
    title: c.title,
    content_type: c.content_type,
    content_text: c.content_text,
    media_url: c.media_url,
    media_caption: c.media_caption,
    target_audience: c.target_audience,
    target_group: c.target_group,
  }
  formError.value = ''
  showModal.value = true
}

async function submitForm() {
  formError.value = ''
  if (!form.value.title) {
    formError.value = 'عنوان الحملة مطلوب'
    return
  }
  formSaving.value = true
  try {
    if (editingCampaign.value) {
      await campaignsApi.update(editingCampaign.value.id, form.value)
    } else {
      await campaignsApi.create(form.value)
    }
    showModal.value = false
    fetchCampaigns()
  } catch (err: any) {
    formError.value = err?.message || 'حدث خطأ'
  } finally {
    formSaving.value = false
  }
}

async function sendCampaign(c: CampaignItem) {
  if (!confirm(`هل تريد إرسال الحملة "${c.title}" الآن؟`)) return
  try {
    const result = await campaignsApi.send(c.id)
    alert(result.message)
    fetchCampaigns()
  } catch (err: any) {
    alert(err?.message || 'حدث خطأ أثناء الإرسال')
  }
}

async function removeCampaign(id: string) {
  if (!confirm('هل أنت متأكد من حذف الحملة؟')) return
  try {
    await campaignsApi.remove(id)
    fetchCampaigns()
  } catch {
    // silent
  }
}

async function autoRemind() {
  reminding.value = true
  remindResult.value = null
  try {
    remindResult.value = await notificationsApi.autoRemindMissingDocs()
  } catch (err: any) {
    alert(err?.message || 'حدث خطأ')
  } finally {
    reminding.value = false
  }
}
</script>
