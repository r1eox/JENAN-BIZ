<template>
  <div class="min-h-screen bg-bg" dir="rtl">
    <!-- Header -->
    <header class="bg-white border-b border-border px-6 py-4 flex items-center justify-between sticky top-0 z-10">
      <div class="flex items-center gap-3">
        <router-link to="/owner" class="text-text-light hover:text-brand transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
        </router-link>
        <div>
          <h1 class="text-lg font-bold text-brand">موظفو الجهات التمويلية</h1>
          <p class="text-xs text-text-light">جهات الاتصال في كل جهة تمويلية</p>
        </div>
      </div>
      <button v-if="canManage" @click="openCreate"
        class="flex items-center gap-2 bg-blue text-white text-sm font-semibold px-4 py-2 rounded-xl hover:bg-blue/90 cursor-pointer transition-colors">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        إضافة موظف
      </button>
    </header>

    <main class="p-6 max-w-5xl mx-auto">
      <!-- Filter by entity -->
      <div class="flex gap-2 mb-6 flex-wrap">
        <button @click="filterEntity = ''" :class="filterEntity === '' ? 'bg-blue text-white' : 'bg-white text-text-light border border-border'"
          class="px-3 py-1.5 rounded-xl text-sm font-medium cursor-pointer transition-colors">الكل</button>
        <button v-for="e in entityNames" :key="e" @click="filterEntity = e"
          :class="filterEntity === e ? 'bg-blue text-white' : 'bg-white text-text-light border border-border'"
          class="px-3 py-1.5 rounded-xl text-sm font-medium cursor-pointer transition-colors">{{ e }}</button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="text-center text-text-light py-20">جاري التحميل...</div>

      <!-- Empty -->
      <div v-else-if="filtered.length === 0" class="text-center text-text-light py-20">
        <svg class="w-12 h-12 mx-auto mb-4 text-border" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
        <p>لا يوجد موظفون مضافون</p>
      </div>

      <!-- Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="c in filtered" :key="c.id"
          class="bg-white rounded-2xl border border-border p-5 space-y-3 hover:shadow-sm transition-shadow">
          <div class="flex justify-between items-start">
            <div>
              <p class="font-semibold text-brand">{{ c.name }}</p>
              <p class="text-xs text-text-light">{{ c.position }}</p>
            </div>
            <span class="text-xs bg-blue/10 text-blue px-2 py-1 rounded-lg">{{ c.entity_name }}</span>
          </div>
          <div class="grid grid-cols-2 gap-2 text-sm">
            <a v-if="c.phone" :href="`tel:${c.phone}`" class="flex items-center gap-1 text-text-light hover:text-blue transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/></svg>
              {{ c.phone }}
            </a>
            <span v-if="c.email" class="flex items-center gap-1 text-text-light truncate">
              <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
              {{ c.email }}
            </span>
          </div>
          <p v-if="c.notes" class="text-xs text-text-light bg-bg rounded-lg px-3 py-2">{{ c.notes }}</p>
          <div v-if="canManage" class="flex gap-2 pt-1">
            <button @click="openEdit(c)" class="text-xs text-blue border border-blue/30 px-3 py-1.5 rounded-lg hover:bg-blue/5 cursor-pointer transition-colors">تعديل</button>
            <button @click="deleteContact(c)" class="text-xs text-danger border border-danger/30 px-3 py-1.5 rounded-lg hover:bg-danger/5 cursor-pointer transition-colors">حذف</button>
          </div>
        </div>
      </div>
    </main>

    <!-- Modal -->
    <Teleport to="body">
      <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" @click.self="showModal = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-md p-6" @click.stop>
          <h3 class="text-lg font-bold text-brand mb-5">{{ editing ? 'تعديل الموظف' : 'إضافة موظف جديد' }}</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">الجهة التمويلية <span class="text-danger">*</span></label>
              <input v-model="form.entity_name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="مثال: البنك الراجحي" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">الاسم <span class="text-danger">*</span></label>
              <input v-model="form.name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="اسم الموظف" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">المسمى الوظيفي <span class="text-text-light/60 font-normal">(اختياري)</span></label>
              <input v-model="form.position" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="مثال: مدير العلاقات" />
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">الجوال <span class="text-danger">*</span></label>
                <input v-model="form.phone" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="05xxxxxxxx" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">البريد الإلكتروني <span class="text-text-light/60 font-normal">(اختياري)</span></label>
                <input v-model="form.email" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">ملاحظات <span class="text-text-light/60 font-normal">(اختياري)</span></label>
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
import { entityContactsApi } from '../../api/client'
import { userPermissions } from '../../stores/authStore'

const canManage = computed(() => userPermissions.value.includes('manage_entity_contacts'))

const items = ref<any[]>([])
const loading = ref(false)
const filterEntity = ref('')
const toast = ref('')
const showModal = ref(false)
const editing = ref<any>(null)
const formError = ref('')
const saving = ref(false)

const emptyForm = () => ({ entity_name: '', name: '', position: '', phone: '', email: '', notes: '' })
const form = ref(emptyForm())

const entityNames = computed(() => [...new Set(items.value.map(c => c.entity_name))].filter(Boolean).sort())
const filtered = computed(() => filterEntity.value ? items.value.filter(c => c.entity_name === filterEntity.value) : items.value)

async function load() {
  loading.value = true
  try {
    const d: any = await entityContactsApi.list()
    items.value = d.items || []
  } catch { /**/ } finally { loading.value = false }
}

function openCreate() { editing.value = null; form.value = emptyForm(); formError.value = ''; showModal.value = true }
function openEdit(c: any) { editing.value = c; form.value = { entity_name: c.entity_name, name: c.name, position: c.position, phone: c.phone, email: c.email, notes: c.notes }; formError.value = ''; showModal.value = true }

async function save() {
  if (!form.value.name || !form.value.entity_name || !form.value.phone) { formError.value = 'الاسم والجهة التمويلية ورقم الجوال مطلوبة'; return }
  saving.value = true; formError.value = ''
  try {
    if (editing.value) {
      await entityContactsApi.update(editing.value.id, form.value)
    } else {
      await entityContactsApi.create(form.value)
    }
    showModal.value = false
    showToast(editing.value ? 'تم التعديل' : 'تمت الإضافة')
    await load()
  } catch (e: any) { formError.value = e?.message || 'حدث خطأ' } finally { saving.value = false }
}

async function deleteContact(c: any) {
  if (!confirm(`حذف ${c.name}؟`)) return
  try { await entityContactsApi.remove(c.id); showToast('تم الحذف'); await load() } catch { /**/ }
}

function showToast(msg: string) { toast.value = msg; setTimeout(() => { toast.value = '' }, 2500) }
onMounted(load)
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 10px); }
</style>
