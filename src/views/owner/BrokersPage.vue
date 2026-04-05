<template>
  <div class="min-h-screen bg-bg" dir="rtl">
    <!-- Header -->
    <header class="bg-white border-b border-border px-6 py-4 flex items-center justify-between sticky top-0 z-10">
      <div class="flex items-center gap-3">
        <router-link to="/owner/users" class="text-text-light hover:text-brand transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        </router-link>
        <div>
          <h1 class="text-lg font-bold text-brand">سجل الوسطاء</h1>
          <p class="text-xs text-text-light">قاعدة بيانات الوسطاء والوكلاء</p>
        </div>
      </div>
      <button v-if="canManage" @click="openCreate"
        class="flex items-center gap-2 bg-blue text-white text-sm font-semibold px-4 py-2 rounded-xl hover:bg-blue/90 cursor-pointer transition-colors">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        إضافة وسيط
      </button>
    </header>

    <main class="p-6 max-w-5xl mx-auto">
      <!-- Search -->
      <div class="mb-5">
        <input v-model="search" placeholder="بحث بالاسم أو الشركة أو السجل التجاري..."
          class="w-full px-4 py-2.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue bg-white" />
      </div>

      <!-- Loading -->
      <div v-if="loading" class="text-center text-text-light py-20">جاري التحميل...</div>

      <!-- Empty -->
      <div v-else-if="filtered.length === 0" class="text-center text-text-light py-20">
        <svg class="w-12 h-12 mx-auto mb-4 text-border" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
        <p>لا يوجد وسطاء مضافون</p>
      </div>

      <!-- Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="b in filtered" :key="b.id"
          class="bg-white rounded-2xl border border-border p-5 space-y-3 hover:shadow-sm transition-shadow">
          <div class="flex justify-between items-start">
            <div>
              <p class="font-semibold text-brand">{{ b.name }}</p>
              <p v-if="b.company_name" class="text-xs text-text-light">{{ b.company_name }}</p>
            </div>
            <span v-if="b.city" class="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded-lg">{{ b.city }}</span>
          </div>
          <div class="grid grid-cols-2 gap-2 text-sm">
            <a v-if="b.phone" :href="`tel:${b.phone}`" class="flex items-center gap-1 text-text-light hover:text-blue transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/></svg>
              {{ b.phone }}
            </a>
            <span v-if="b.cr_number" class="text-xs text-text-light flex items-center gap-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
              س.ت: {{ b.cr_number }}
            </span>
          </div>
          <p v-if="b.notes" class="text-xs text-text-light bg-bg rounded-lg px-3 py-2">{{ b.notes }}</p>
          <div v-if="canManage" class="flex gap-2 pt-1">
            <button @click="openEdit(b)" class="text-xs text-blue border border-blue/30 px-3 py-1.5 rounded-lg hover:bg-blue/5 cursor-pointer transition-colors">تعديل</button>
            <button @click="deleteBroker(b)" class="text-xs text-danger border border-danger/30 px-3 py-1.5 rounded-lg hover:bg-danger/5 cursor-pointer transition-colors">حذف</button>
          </div>
        </div>
      </div>
    </main>

    <!-- Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" @click.self="showModal = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 overflow-y-auto max-h-[90vh]" @click.stop>
          <h3 class="text-lg font-bold text-brand mb-5">{{ editing ? 'تعديل الوسيط' : 'إضافة وسيط جديد' }}</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">الاسم <span class="text-danger">*</span></label>
              <input v-model="form.name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="الاسم الكامل" />
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">الجوال</label>
                <input v-model="form.phone" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">البريد الإلكتروني</label>
                <input v-model="form.email" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">اسم الشركة</label>
              <input v-model="form.company_name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">السجل التجاري</label>
                <input v-model="form.cr_number" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">المدينة</label>
                <input v-model="form.city" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
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
import { brokersApi } from '../../api/client'
import { userPermissions } from '../../stores/authStore'

const canManage = computed(() => userPermissions.value.includes('manage_brokers'))

const items = ref<any[]>([])
const loading = ref(false)
const search = ref('')
const toast = ref('')
const showModal = ref(false)
const editing = ref<any>(null)
const formError = ref('')
const saving = ref(false)

const emptyForm = () => ({ name: '', phone: '', email: '', company_name: '', cr_number: '', city: '', notes: '' })
const form = ref(emptyForm())

const filtered = computed(() => {
  if (!search.value) return items.value
  const q = search.value.toLowerCase()
  return items.value.filter(b =>
    b.name?.toLowerCase().includes(q) ||
    b.company_name?.toLowerCase().includes(q) ||
    b.cr_number?.includes(q)
  )
})

async function load() {
  loading.value = true
  try {
    const d: any = await brokersApi.list()
    items.value = d.items || []
  } catch { /**/ } finally { loading.value = false }
}

function openCreate() { editing.value = null; form.value = emptyForm(); formError.value = ''; showModal.value = true }
function openEdit(b: any) { editing.value = b; form.value = { name: b.name, phone: b.phone, email: b.email, company_name: b.company_name, cr_number: b.cr_number, city: b.city, notes: b.notes }; formError.value = ''; showModal.value = true }

async function save() {
  if (!form.value.name) { formError.value = 'الاسم مطلوب'; return }
  saving.value = true; formError.value = ''
  try {
    if (editing.value) {
      await brokersApi.update(editing.value.id, form.value)
    } else {
      await brokersApi.create(form.value)
    }
    showModal.value = false
    showToast(editing.value ? 'تم التعديل' : 'تمت الإضافة')
    await load()
  } catch (e: any) { formError.value = e?.message || 'حدث خطأ' } finally { saving.value = false }
}

async function deleteBroker(b: any) {
  if (!confirm(`حذف الوسيط ${b.name}؟`)) return
  try { await brokersApi.remove(b.id); showToast('تم الحذف'); await load() } catch { /**/ }
}

function showToast(msg: string) { toast.value = msg; setTimeout(() => { toast.value = '' }, 2500) }
onMounted(load)
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 10px); }
</style>
