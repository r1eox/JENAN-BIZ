<template>
  <div class="min-h-screen min-h-dvh bg-bg">
    <!-- Top bar -->
    <header class="bg-white border-b border-border sticky top-0 z-30">
      <div class="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <img src="/logo.svg" alt="Jenan BIZ" class="h-8" />
          <span class="text-xs font-bold bg-blue/10 text-blue px-2 py-0.5 rounded-lg">المالك</span>
        </div>
        <div class="flex items-center gap-3">
          <NotificationBell />
          <router-link to="/owner/users" class="text-sm text-text-light hover:text-blue transition-colors">المستخدمون</router-link>
          <router-link to="/owner/campaigns" class="text-sm text-text-light hover:text-blue transition-colors">الحملات</router-link>
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
          <h1 class="text-xl font-bold text-brand">جهات الاتصال الخارجية</h1>
          <p class="text-sm text-text-light mt-1">إدارة جهات الاتصال للحملات التسويقية عبر واتساب</p>
        </div>
        <div class="flex gap-2">
          <button
            @click="exportCSV"
            class="bg-white border border-border text-text-light text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-success/50 hover:text-success transition-colors cursor-pointer flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
            تصدير CSV
          </button>
          <button
            @click="showBulkModal = true"
            class="bg-white border border-border text-text-light text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-blue/30 transition-colors cursor-pointer flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
            </svg>
            استيراد جماعي
          </button>
          <button
            @click="openCreateModal"
            class="bg-blue text-white text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-blue/90 transition-colors cursor-pointer flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            جهة اتصال جديدة
          </button>
        </div>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap gap-2 mb-4">
        <div class="flex-1 min-w-[200px]">
          <input
            v-model="searchQuery"
            class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue bg-white"
            placeholder="بحث بالاسم أو الجوال أو اسم الشركة..."
            @input="debouncedFetch"
          />
        </div>
        <select
          v-model="filterGroup"
          class="px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue bg-white"
          @change="fetchContacts"
        >
          <option value="">كل المجموعات</option>
          <option v-for="g in groups" :key="g" :value="g">{{ g }}</option>
        </select>
      </div>

      <!-- Stats -->
      <div class="flex gap-3 mb-4">
        <div class="bg-white rounded-xl border border-border px-4 py-2.5 flex items-center gap-2">
          <span class="text-xl font-bold text-blue">{{ totalItems }}</span>
          <span class="text-xs text-text-light">جهة اتصال</span>
        </div>
        <div class="bg-white rounded-xl border border-border px-4 py-2.5 flex items-center gap-2">
          <span class="text-xl font-bold text-brand">{{ groups.length }}</span>
          <span class="text-xs text-text-light">مجموعة</span>
        </div>
      </div>

      <!-- Bulk action bar -->
      <div v-if="contacts.length > 0" class="flex items-center gap-3 mb-4">
        <button
          @click="toggleSelectAll"
          class="flex items-center gap-2 text-sm px-3 py-2 rounded-xl border border-border bg-white hover:border-blue/40 transition-colors cursor-pointer"
        >
          <span class="w-4 h-4 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors"
            :class="allSelected ? 'bg-blue border-blue' : 'border-gray-300'">
            <svg v-if="allSelected" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
            </svg>
          </span>
          {{ allSelected ? 'إلغاء التحديد' : 'تحديد الكل' }}
        </button>
        <Transition name="fade">
          <button
            v-if="selected.size > 0"
            @click="deleteSelected"
            class="flex items-center gap-2 text-sm px-4 py-2 rounded-xl bg-danger text-white hover:bg-red-700 transition-colors cursor-pointer font-semibold"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
            حذف المحدد ({{ selected.size }})
          </button>
        </Transition>
      </div>

      <!-- Contacts Table -->
      <div class="bg-white rounded-2xl border border-border overflow-hidden">
        <div v-if="loading" class="p-8 text-center text-text-light text-sm">جاري التحميل...</div>
        <div v-else-if="contacts.length === 0" class="p-8 text-center text-text-light text-sm">لا توجد جهات اتصال</div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-border bg-gray-50/50">
                <th class="px-4 py-3 w-8"></th>
                <th class="text-right px-4 py-3 text-xs font-bold text-text-light">الاسم</th>
                <th class="text-right px-4 py-3 text-xs font-bold text-text-light">الجوال</th>
                <th class="text-right px-4 py-3 text-xs font-bold text-text-light">الشركة</th>
                <th class="text-right px-4 py-3 text-xs font-bold text-text-light">المجموعة</th>
                <th class="text-right px-4 py-3 text-xs font-bold text-text-light">المصدر</th>
                <th class="text-center px-4 py-3 text-xs font-bold text-text-light">إجراءات</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="c in contacts"
                :key="c.id"
                class="border-b border-border/50 hover:bg-gray-50 transition-colors cursor-pointer"
                :class="{ 'bg-blue/5': selected.has(c.id) }"
                @click="toggleSelect(c.id)"
              >
                <td class="px-4 py-3" @click.stop>
                  <span class="w-4 h-4 rounded border-2 flex items-center justify-center transition-colors"
                    :class="selected.has(c.id) ? 'bg-blue border-blue' : 'border-gray-300'">
                    <svg v-if="selected.has(c.id)" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
                    </svg>
                  </span>
                </td>
                <td class="px-4 py-3 font-medium text-brand">{{ c.name || '—' }}</td>
                <td class="px-4 py-3 text-text-light" dir="ltr">{{ c.phone }}</td>
                <td class="px-4 py-3 text-text-light">{{ c.company_name || '—' }}</td>
                <td class="px-4 py-3">
                  <span class="inline-flex px-2 py-0.5 rounded-lg text-xs font-medium bg-blue/10 text-blue">{{ c.group_name }}</span>
                </td>
                <td class="px-4 py-3 text-text-light text-xs">{{ sourceLabel(c.source) }}</td>
                <td class="px-4 py-3 text-center" @click.stop>
                  <div class="flex items-center justify-center gap-1">
                    <!-- WhatsApp direct button -->
                    <a
                      :href="`https://wa.me/${formatWhatsApp(c.phone)}`"
                      target="_blank"
                      class="text-success hover:text-green-700 p-1 cursor-pointer"
                      title="واتساب"
                    >
                      <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                      </svg>
                    </a>
                    <button @click="openEditModal(c)" class="text-blue hover:text-blue-dark p-1 cursor-pointer" title="تعديل">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                      </svg>
                    </button>
                    <button @click="removeContact(c.id)" class="text-danger hover:text-red-700 p-1 cursor-pointer" title="حذف">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-4">
        <button
          v-for="p in totalPages"
          :key="p"
          @click="currentPage = p; fetchContacts()"
          class="w-8 h-8 rounded-lg text-xs font-medium cursor-pointer transition-colors"
          :class="currentPage === p ? 'bg-blue text-white' : 'bg-white text-text-light border border-border hover:border-blue/30'"
        >
          {{ p }}
        </button>
      </div>
    </main>

    <!-- Create/Edit Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" @click.self="showModal = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6" @click.stop>
          <h3 class="text-lg font-bold text-brand mb-4">{{ editingContact ? 'تعديل جهة اتصال' : 'جهة اتصال جديدة' }}</h3>

          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">الاسم</label>
              <input v-model="form.name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="الاسم" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">رقم الجوال *</label>
              <input v-model="form.phone" dir="ltr" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="05xxxxxxxx" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">اسم الشركة</label>
              <input v-model="form.company_name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="اسم الشركة" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">المجموعة</label>
              <input v-model="form.group_name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="عام" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">ملاحظات</label>
              <textarea v-model="form.notes" rows="2" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue resize-none" placeholder="ملاحظات"></textarea>
            </div>
          </div>

          <p v-if="formError" class="text-xs text-danger mt-3">{{ formError }}</p>

          <div class="flex gap-2 mt-5">
            <button
              @click="submitForm"
              :disabled="formSaving"
              class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-semibold hover:bg-blue/90 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {{ formSaving ? 'جاري الحفظ...' : (editingContact ? 'حفظ' : 'إضافة') }}
            </button>
            <button @click="showModal = false" class="px-4 py-2.5 rounded-xl bg-gray-100 text-text-light text-sm font-medium hover:bg-gray-200 transition-colors cursor-pointer">
              إلغاء
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Bulk Import Modal -->
    <Teleport to="body">
      <div v-if="showBulkModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" @click.self="closeBulkModal">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6" @click.stop>
          <h3 class="text-lg font-bold text-brand mb-1">استيراد جهات الاتصال</h3>
          <p class="text-xs text-text-light mb-4">ارفع ملف CSV — الأعمدة: الاسم، الجوال (إجباري)، الشركة، المجموعة</p>

          <!-- Template download -->
          <button @click="downloadTemplate"
            class="flex items-center gap-1.5 text-xs text-blue hover:underline mb-4 cursor-pointer">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
            تحميل نموذج CSV فارغ
          </button>

          <!-- File picker -->
          <label class="flex flex-col items-center justify-center w-full h-28 border-2 border-dashed border-border rounded-xl cursor-pointer hover:border-blue/50 hover:bg-blue/5 transition-colors bg-gray-50">
            <svg class="w-8 h-8 text-text-light mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
            <span v-if="!bulkFileName" class="text-xs text-text-light">اضغط لاختيار ملف CSV</span>
            <span v-else class="text-xs font-medium text-blue">{{ bulkFileName }}</span>
            <span v-if="bulkParsed.length" class="text-[10px] text-success mt-0.5">{{ bulkParsed.length }} جهة جاهزة للاستيراد</span>
            <input ref="fileInput" type="file" accept=".csv" class="hidden" @change="onFileChange" />
          </label>

          <p v-if="bulkError" class="text-xs text-danger mt-2">{{ bulkError }}</p>
          <p v-if="bulkResult" class="text-xs text-success mt-2">{{ bulkResult }}</p>

          <div class="flex gap-2 mt-4">
            <button
              @click="submitBulk"
              :disabled="bulkSaving || bulkParsed.length === 0"
              class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-semibold hover:bg-blue/90 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {{ bulkSaving ? 'جاري الاستيراد...' : `استيراد ${bulkParsed.length ? bulkParsed.length + ' جهة' : ''}` }}
            </button>
            <button @click="closeBulkModal" class="px-4 py-2.5 rounded-xl bg-gray-100 text-text-light text-sm font-medium hover:bg-gray-200 transition-colors cursor-pointer">
              إغلاق
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { contactsApi, type ContactItem } from '../../api/client'
import { logout } from '../../stores/authStore'
import { useRouter } from 'vue-router'
import NotificationBell from '../../components/NotificationBell.vue'
const router = useRouter()
function handleLogout() { logout(); router.push('/login') }

const contacts = ref<ContactItem[]>([])
const groups = ref<string[]>([])
const loading = ref(false)
const searchQuery = ref('')
const filterGroup = ref('')
const currentPage = ref(1)
const totalItems = ref(0)
const pageSize = 20
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize))

// Bulk select
const selected = ref<Set<string>>(new Set())
const allSelected = computed(() => contacts.value.length > 0 && contacts.value.every(c => selected.value.has(c.id)))
function toggleSelect(id: string) {
  const s = new Set(selected.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selected.value = s
}
function toggleSelectAll() {
  if (allSelected.value) {
    selected.value = new Set()
  } else {
    selected.value = new Set(contacts.value.map(c => c.id))
  }
}
async function deleteSelected() {
  if (!confirm(`هل أنت متأكد من حذف ${selected.value.size} جهة اتصال؟`)) return
  try {
    await Promise.all([...selected.value].map(id => contactsApi.remove(id)))
    selected.value = new Set()
    await fetchContacts()
  } catch {
    // silent
  }
}

// Contact modal
const showModal = ref(false)
const editingContact = ref<ContactItem | null>(null)
const form = ref({ name: '', phone: '', company_name: '', group_name: 'عام', notes: '' })
const formError = ref('')
const formSaving = ref(false)

// Bulk import modal
const showBulkModal = ref(false)
const bulkFileName = ref('')
const bulkParsed = ref<{ phone: string; name?: string; company_name?: string; group_name?: string }[]>([])
const bulkError = ref('')
const bulkResult = ref('')
const bulkSaving = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

function closeBulkModal() {
  showBulkModal.value = false
  bulkFileName.value = ''
  bulkParsed.value = []
  bulkError.value = ''
  bulkResult.value = ''
}

function downloadTemplate() {
  const bom = '\uFEFF'
  const csv = bom + 'الاسم,الجوال,الشركة,المجموعة\nأحمد محمد,0501234567,شركة نموذجية,عام'
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'نموذج-جهات-الاتصال.csv'
  a.click()
  URL.revokeObjectURL(url)
}

function onFileChange(e: Event) {
  bulkError.value = ''
  bulkResult.value = ''
  bulkParsed.value = []
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  bulkFileName.value = file.name
  const reader = new FileReader()
  reader.onload = (ev) => {
    try {
      const text = (ev.target?.result as string).replace(/^\uFEFF/, '')
      const lines = text.split(/\r?\n/).filter(l => l.trim())
      if (lines.length < 2) { bulkError.value = 'الملف فارغ أو لا يحتوي على بيانات'; return }

      const header = lines[0].split(',')
      const idx = (names: string[]) => header.findIndex(h => names.some(n => h.trim().replace(/"/g, '').includes(n)))
      const phoneIdx = idx(['الجوال', 'phone', 'جوال', 'رقم'])
      const nameIdx  = idx(['الاسم', 'name', 'اسم'])
      const compIdx  = idx(['الشركة', 'company', 'شركة', 'منشأة'])
      const groupIdx = idx(['المجموعة', 'group', 'مجموعة'])

      if (phoneIdx === -1) { bulkError.value = 'لم يتم العثور على عمود الجوال — تأكد من وجود عمود باسم "الجوال"'; return }

      const parsed: typeof bulkParsed.value = []
      for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(',')
        const phone = cols[phoneIdx]?.replace(/"/g, '').trim()
        if (!phone) continue
        parsed.push({
          phone,
          name:         nameIdx  >= 0 ? cols[nameIdx]?.replace(/"/g, '').trim()  || undefined : undefined,
          company_name: compIdx  >= 0 ? cols[compIdx]?.replace(/"/g, '').trim()  || undefined : undefined,
          group_name:   groupIdx >= 0 ? cols[groupIdx]?.replace(/"/g, '').trim() || undefined : undefined,
        })
      }
      bulkParsed.value = parsed
      if (parsed.length === 0) bulkError.value = 'لم يتم العثور على صفوف صالحة'
    } catch { bulkError.value = 'حدث خطأ أثناء قراءة الملف' }
  }
  reader.readAsText(file, 'UTF-8')
}

let debounceTimer: ReturnType<typeof setTimeout> | null = null

function debouncedFetch() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    fetchContacts()
  }, 400)
}

onMounted(async () => {
  await Promise.all([fetchContacts(), fetchGroups()])
})

async function fetchContacts() {
  loading.value = true
  try {
    const data = await contactsApi.list({
      group: filterGroup.value || undefined,
      search: searchQuery.value || undefined,
      page: currentPage.value,
      size: pageSize,
    })
    contacts.value = data.items
    totalItems.value = data.total
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

async function fetchGroups() {
  try {
    const data = await contactsApi.groups()
    groups.value = data.groups
  } catch {
    // silent
  }
}

function sourceLabel(s: string): string {
  const map: Record<string, string> = { manual: 'يدوي', import: 'استيراد', signup: 'تسجيل' }
  return map[s] || s
}

function openCreateModal() {
  editingContact.value = null
  form.value = { name: '', phone: '', company_name: '', group_name: 'عام', notes: '' }
  formError.value = ''
  showModal.value = true
}

function openEditModal(c: ContactItem) {
  editingContact.value = c
  form.value = {
    name: c.name,
    phone: c.phone,
    company_name: c.company_name,
    group_name: c.group_name,
    notes: c.notes,
  }
  formError.value = ''
  showModal.value = true
}

async function submitForm() {
  formError.value = ''
  if (!form.value.phone) {
    formError.value = 'رقم الجوال مطلوب'
    return
  }
  formSaving.value = true
  try {
    if (editingContact.value) {
      await contactsApi.update(editingContact.value.id, form.value)
    } else {
      await contactsApi.create(form.value)
    }
    showModal.value = false
    await Promise.all([fetchContacts(), fetchGroups()])
  } catch (err: any) {
    formError.value = err?.message || 'حدث خطأ'
  } finally {
    formSaving.value = false
  }
}

async function removeContact(id: string) {
  if (!confirm('هل أنت متأكد من حذف جهة الاتصال؟')) return
  try {
    await contactsApi.remove(id)
    fetchContacts()
  } catch {
    // silent
  }
}

// Format phone for WhatsApp link (966 prefix)
function formatWhatsApp(phone: string): string {
  const cleaned = phone.replace(/\D/g, '')
  if (cleaned.startsWith('0')) return '966' + cleaned.slice(1)
  if (cleaned.startsWith('966')) return cleaned
  return '966' + cleaned
}

// Export all contacts as CSV
async function exportCSV() {
  try {
    // Fetch all contacts in batches (max 500 per request)
    const allRows: typeof contacts.value = []
    let page = 1
    while (true) {
      const data = await contactsApi.list({ size: 500, page })
      allRows.push(...data.items)
      if (allRows.length >= data.total || data.items.length === 0) break
      page++
    }
    const rows = allRows
    const header = ['الاسم', 'الجوال', 'الشركة', 'المجموعة', 'المصدر', 'الملاحظات', 'تاريخ الإضافة']
    const lines = [
      header.join(','),
      ...rows.map(c => [
        `"${(c.name || '').replace(/"/g, '""')}"`,
        `"${c.phone}"`,
        `"${(c.company_name || '').replace(/"/g, '""')}"`,
        `"${(c.group_name || '').replace(/"/g, '""')}"`,
        `"${sourceLabel(c.source)}"`,
        `"${(c.notes || '').replace(/"/g, '""')}"`,
        `"${c.created_at ? new Date(c.created_at).toLocaleDateString('ar-SA') : ''}"`,
      ].join(','))
    ]
    const bom = '\uFEFF' // UTF-8 BOM for Arabic support in Excel
    const blob = new Blob([bom + lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `جهات-الاتصال-${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch {
    // silent
  }
}

async function submitBulk() {
  if (bulkParsed.value.length === 0) return
  bulkError.value = ''
  bulkResult.value = ''
  bulkSaving.value = true
  try {
    const result = await contactsApi.bulkImport(bulkParsed.value)
    bulkResult.value = `✓ تم استيراد ${result.imported} جهة — تم تخطي ${result.skipped} مكرر`
    if (result.errors.length > 0) bulkResult.value += ` — ${result.errors.length} خطأ`
    bulkParsed.value = []
    bulkFileName.value = ''
    if (fileInput.value) fileInput.value.value = ''
    fetchContacts()
    fetchGroups()
  } catch (err: any) {
    bulkError.value = err?.message || 'حدث خطأ أثناء الاستيراد'
  } finally {
    bulkSaving.value = false
  }
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s, transform 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.95); }
</style>
