<template>
  <div class="min-h-screen bg-bg" dir="rtl">
    <!-- Header -->
    <header class="bg-white border-b border-border px-6 py-4 flex items-center justify-between sticky top-0 z-10">
      <div class="flex items-center gap-3">
        <router-link to="/owner/users" class="text-text-light hover:text-brand transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        </router-link>
        <div>
          <h1 class="text-lg font-bold text-brand">سجل المنشآت</h1>
          <p class="text-xs text-text-light">قاعدة بيانات المنشآت التجارية</p>
        </div>
      </div>
      <button v-if="canManage" @click="openCreate"
        class="flex items-center gap-2 bg-blue text-white text-sm font-semibold px-4 py-2 rounded-xl hover:bg-blue/90 cursor-pointer transition-colors">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        إضافة منشأة
      </button>
    </header>

    <main class="p-6 max-w-5xl mx-auto">
      <!-- Search -->
      <div class="mb-5">
        <input v-model="search" placeholder="بحث باسم المنشأة أو رقم السجل التجاري..."
          class="w-full px-4 py-2.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue bg-white" />
      </div>

      <!-- Loading -->
      <div v-if="loading" class="text-center text-text-light py-20">جاري التحميل...</div>

      <!-- Empty -->
      <div v-else-if="filtered.length === 0" class="text-center text-text-light py-20">
        <svg class="w-12 h-12 mx-auto mb-4 text-border" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
        <p>لا توجد منشآت مضافة</p>
      </div>

      <!-- Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="biz in filtered" :key="biz.id"
          class="bg-white rounded-2xl border border-border p-5 space-y-3 hover:shadow-sm transition-shadow">
          <div class="flex justify-between items-start">
            <div>
              <p class="font-semibold text-brand">{{ biz.company_name }}</p>
              <p v-if="biz.activity" class="text-xs text-text-light">{{ biz.activity }}</p>
            </div>
            <span v-if="biz.city" class="text-xs bg-success/10 text-success px-2 py-1 rounded-lg">{{ biz.city }}</span>
          </div>
          <div class="grid grid-cols-2 gap-2 text-sm">
            <span v-if="biz.cr_number" class="text-xs text-text-light flex items-center gap-1">
              <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
              س.ت: {{ biz.cr_number }}
            </span>
            <span v-if="biz.owner_name" class="text-xs text-text-light">المالك: {{ biz.owner_name }}</span>
            <a v-if="biz.phone" :href="`tel:${biz.phone}`" class="text-xs text-text-light hover:text-blue flex items-center gap-1 transition-colors">
              <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/></svg>
              {{ biz.phone }}
            </a>
            <span v-if="biz.establishment_year" class="text-xs text-text-light">تأسيس: {{ biz.establishment_year }}</span>
          </div>
          <p v-if="biz.notes" class="text-xs text-text-light bg-bg rounded-lg px-3 py-2">{{ biz.notes }}</p>
          <div v-if="canManage" class="flex gap-2 pt-1">
            <button @click="openEdit(biz)" class="text-xs text-blue border border-blue/30 px-3 py-1.5 rounded-lg hover:bg-blue/5 cursor-pointer transition-colors">تعديل</button>
            <button @click="deleteBiz(biz)" class="text-xs text-danger border border-danger/30 px-3 py-1.5 rounded-lg hover:bg-danger/5 cursor-pointer transition-colors">حذف</button>
          </div>
        </div>
      </div>
    </main>

    <!-- Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" @click.self="showModal = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 overflow-y-auto max-h-[90vh]" @click.stop>
          <h3 class="text-lg font-bold text-brand mb-5">{{ editing ? 'تعديل المنشأة' : 'إضافة منشأة جديدة' }}</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">اسم المنشأة <span class="text-danger">*</span></label>
              <input v-model="form.company_name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">السجل التجاري</label>
                <input v-model="form.cr_number" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">النشاط التجاري</label>
                <input v-model="form.activity" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">اسم المالك</label>
                <input v-model="form.owner_name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">الجوال</label>
                <input v-model="form.phone" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">المدينة</label>
                <input v-model="form.city" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">سنة التأسيس</label>
                <input v-model="form.establishment_year" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="مثال: 2015" />
              </div>
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">ملاحظات</label>
              <textarea v-model="form.notes" rows="2" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue resize-none"></textarea>
            </div>
          </div>
          <p v-if="formError" class="text-xs text-danger mt-3 bg-danger/5 rounded-xl px-3 py-2">{{ formError }}</p>
          <div class="flex gap-2 mt-5">
            <button @click="save" :disabled="saving" class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-semibold hover:bg-blue/90 disabled:opacity-50 cursor-pointer">
              {{ saving ? 'جاري الحفظ...' : 'حفظ' }}
            </button>
            <button @click="showModal = false" class="px-4 py-2.5 rounded-xl bg-gray-100 text-text-light text-sm hover:bg-gray-200 cursor-pointer">إلغاء</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast" class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-brand text-white text-sm font-medium px-5 py-3 rounded-2xl shadow-xl">{{ toast }}</div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { businessesApi } from '../../api/client'
import { userPermissions } from '../../stores/authStore'

const canManage = computed(() => userPermissions.value.includes('manage_business_registry'))

const items = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const toast = ref('')
const showModal = ref(false)
const editing = ref<any>(null)
const formError = ref('')
const saving = ref(false)

const emptyForm = () => ({ company_name: '', cr_number: '', activity: '', owner_name: '', phone: '', city: '', establishment_year: '', notes: '' })
const form = ref(emptyForm())

const filtered = computed(() => {
  if (!search.value) return items.value
  const q = search.value.toLowerCase()
  return items.value.filter(b =>
    b.company_name?.toLowerCase().includes(q) ||
    b.cr_number?.includes(q) ||
    b.owner_name?.toLowerCase().includes(q)
  )
})

async function load() {
  loading.value = true
  try {
    const d: any = await businessesApi.list()
    items.value = d.items || []
  } catch { /**/ } finally { loading.value = false }
}

function openCreate() { editing.value = null; form.value = emptyForm(); formError.value = ''; showModal.value = true }
function openEdit(b: any) {
  editing.value = b
  form.value = { company_name: b.company_name, cr_number: b.cr_number, activity: b.activity, owner_name: b.owner_name, phone: b.phone, city: b.city, establishment_year: b.establishment_year, notes: b.notes }
  formError.value = ''; showModal.value = true
}

async function save() {
  if (!form.value.company_name) { formError.value = 'اسم المنشأة مطلوب'; return }
  saving.value = true; formError.value = ''
  try {
    if (editing.value) {
      await businessesApi.update(editing.value.id, form.value)
    } else {
      await businessesApi.create(form.value)
    }
    showModal.value = false
    showToast(editing.value ? 'تم التعديل' : 'تمت الإضافة')
    await load()
  } catch (e: any) { formError.value = e?.message || 'حدث خطأ' } finally { saving.value = false }
}

async function deleteBiz(b: any) {
  if (!confirm(`حذف المنشأة ${b.company_name}؟`)) return
  try { await businessesApi.remove(b.id); showToast('تم الحذف'); await load() } catch { /**/ }
}

function showToast(msg: string) { toast.value = msg; setTimeout(() => { toast.value = '' }, 2500) }
onMounted(load)
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 10px); }
</style>
