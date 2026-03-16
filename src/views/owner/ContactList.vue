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
          <button @click="$router.push('/')" class="text-text-light hover:text-danger transition-colors cursor-pointer p-1">
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

      <!-- Contacts Table -->
      <div class="bg-white rounded-2xl border border-border overflow-hidden">
        <div v-if="loading" class="p-8 text-center text-text-light text-sm">جاري التحميل...</div>
        <div v-else-if="contacts.length === 0" class="p-8 text-center text-text-light text-sm">لا توجد جهات اتصال</div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-border bg-gray-50/50">
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
                class="border-b border-border/50 hover:bg-gray-50 transition-colors"
              >
                <td class="px-4 py-3 font-medium text-brand">{{ c.name || '—' }}</td>
                <td class="px-4 py-3 text-text-light" dir="ltr">{{ c.phone }}</td>
                <td class="px-4 py-3 text-text-light">{{ c.company_name || '—' }}</td>
                <td class="px-4 py-3">
                  <span class="inline-flex px-2 py-0.5 rounded-lg text-xs font-medium bg-blue/10 text-blue">{{ c.group_name }}</span>
                </td>
                <td class="px-4 py-3 text-text-light text-xs">{{ sourceLabel(c.source) }}</td>
                <td class="px-4 py-3 text-center">
                  <div class="flex items-center justify-center gap-1">
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
      <div v-if="showBulkModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" @click.self="showBulkModal = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6" @click.stop>
          <h3 class="text-lg font-bold text-brand mb-2">استيراد جماعي</h3>
          <p class="text-xs text-text-light mb-4">الصق البيانات بصيغة JSON — كل سطر يحتوي على phone (إجباري) و name, company_name, group_name (اختياري)</p>

          <textarea
            v-model="bulkJson"
            rows="8"
            dir="ltr"
            class="w-full px-3 py-2 text-xs font-mono border border-border rounded-xl focus:outline-none focus:border-blue resize-none bg-gray-50"
            placeholder='[{"phone":"0501234567","name":"أحمد","group_name":"عملاء VIP"}]'
          ></textarea>

          <p v-if="bulkError" class="text-xs text-danger mt-2">{{ bulkError }}</p>
          <p v-if="bulkResult" class="text-xs text-success mt-2">{{ bulkResult }}</p>

          <div class="flex gap-2 mt-4">
            <button
              @click="submitBulk"
              :disabled="bulkSaving"
              class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-semibold hover:bg-blue/90 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {{ bulkSaving ? 'جاري الاستيراد...' : 'استيراد' }}
            </button>
            <button @click="showBulkModal = false" class="px-4 py-2.5 rounded-xl bg-gray-100 text-text-light text-sm font-medium hover:bg-gray-200 transition-colors cursor-pointer">
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
import NotificationBell from '../../components/NotificationBell.vue'

const contacts = ref<ContactItem[]>([])
const groups = ref<string[]>([])
const loading = ref(false)
const searchQuery = ref('')
const filterGroup = ref('')
const currentPage = ref(1)
const totalItems = ref(0)
const pageSize = 20
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize))

// Contact modal
const showModal = ref(false)
const editingContact = ref<ContactItem | null>(null)
const form = ref({ name: '', phone: '', company_name: '', group_name: 'عام', notes: '' })
const formError = ref('')
const formSaving = ref(false)

// Bulk modal
const showBulkModal = ref(false)
const bulkJson = ref('')
const bulkError = ref('')
const bulkResult = ref('')
const bulkSaving = ref(false)

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

async function submitBulk() {
  bulkError.value = ''
  bulkResult.value = ''
  let items: any[]
  try {
    items = JSON.parse(bulkJson.value)
    if (!Array.isArray(items)) throw new Error()
  } catch {
    bulkError.value = 'صيغة JSON غير صحيحة — يجب أن تكون مصفوفة []'
    return
  }
  bulkSaving.value = true
  try {
    const result = await contactsApi.bulkImport(items)
    bulkResult.value = `تم استيراد ${result.imported} جهة — تم تخطي ${result.skipped} مكرر`
    if (result.errors.length > 0) {
      bulkResult.value += ` — ${result.errors.length} خطأ`
    }
    fetchContacts()
    fetchGroups()
  } catch (err: any) {
    bulkError.value = err?.message || 'حدث خطأ أثناء الاستيراد'
  } finally {
    bulkSaving.value = false
  }
}
</script>
