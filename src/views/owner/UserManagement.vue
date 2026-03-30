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
          <router-link to="/owner/permissions" class="text-sm text-text-light hover:text-blue transition-colors">الصلاحيات</router-link>
          <router-link to="/owner/entities" class="text-sm text-text-light hover:text-blue transition-colors">الجهات</router-link>
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
          <h1 class="text-xl font-bold text-brand">إدارة المستخدمين</h1>
          <p class="text-sm text-text-light mt-1">إنشاء وتعديل وإدارة حسابات المستخدمين</p>
        </div>
        <button
          @click="openCreateModal"
          class="bg-blue text-white text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-blue/90 transition-colors cursor-pointer flex items-center gap-2"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          مستخدم جديد
        </button>
      </div>

      <!-- Pending Partners Section -->
      <div v-if="pendingPartners.length > 0" class="mb-6">
        <h2 class="text-base font-bold text-brand mb-2 flex items-center gap-2">
          طلبات تسجيل شركاء جدد
          <span class="text-xs font-bold bg-warning/15 text-warning px-2 py-0.5 rounded-lg">{{ pendingPartners.length }}</span>
        </h2>
        <div class="space-y-2">
          <div v-for="p in pendingPartners" :key="p.id"
            class="bg-white rounded-xl border border-warning/30 p-3 flex items-center justify-between gap-4">
            <div class="flex-1 min-w-0">
              <p class="font-bold text-brand text-sm">{{ p.name }}</p>
              <p class="text-xs text-text-light mt-0.5" dir="ltr">{{ p.phone }}</p>
            </div>
            <div class="flex gap-2 flex-shrink-0">
              <button @click="approvePending(p)"
                class="text-xs font-bold text-success bg-success/10 px-3 py-1.5 rounded-lg hover:bg-success/20 transition-colors cursor-pointer">
                قبول
              </button>
              <button @click="rejectPending(p)"
                class="text-xs font-bold text-danger bg-danger/10 px-3 py-1.5 rounded-lg hover:bg-danger/20 transition-colors cursor-pointer">
                رفض
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap gap-2 mb-4">
        <button
          v-for="r in roleFilters"
          :key="r.value"
          @click="filterRole = r.value"
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer"
          :class="filterRole === r.value ? 'bg-blue text-white' : 'bg-white text-text-light border border-border hover:border-blue/30'"
        >
          {{ r.label }}
        </button>
      </div>

      <!-- Users Table -->
      <div class="bg-white rounded-2xl border border-border overflow-hidden">
        <div v-if="loading" class="p-8 text-center text-text-light text-sm">جاري التحميل...</div>
        <div v-else-if="users.length === 0" class="p-8 text-center text-text-light text-sm">لا يوجد مستخدمون</div>
        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-border bg-gray-50/50">
                <th class="text-right px-4 py-3 text-xs font-bold text-text-light">الاسم</th>
                <th class="text-right px-4 py-3 text-xs font-bold text-text-light">الجوال</th>
                <th class="text-right px-4 py-3 text-xs font-bold text-text-light">الدور</th>
                <th class="text-right px-4 py-3 text-xs font-bold text-text-light">الحالة</th>
                <th class="text-right px-4 py-3 text-xs font-bold text-text-light">تاريخ الإنشاء</th>
                <th class="text-center px-4 py-3 text-xs font-bold text-text-light">إجراءات</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="user in users"
                :key="user.id"
                class="border-b border-border/50 hover:bg-gray-50 transition-colors"
              >
                <td class="px-4 py-3 font-medium text-brand">{{ user.name }}</td>
                <td class="px-4 py-3 text-text-light" dir="ltr">{{ user.phone }}</td>
                <td class="px-4 py-3">
                  <span class="inline-flex px-2 py-0.5 rounded-lg text-xs font-medium" :class="roleClass(user.role)">
                    {{ roleLabel(user.role) }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <span
                    class="inline-flex items-center gap-1 text-xs font-medium"
                    :class="user.is_active ? 'text-success' : 'text-danger'"
                  >
                    <span class="w-1.5 h-1.5 rounded-full" :class="user.is_active ? 'bg-success' : 'bg-danger'"></span>
                    {{ user.is_active ? 'نشط' : 'معطّل' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-text-light text-xs">{{ formatDate(user.created_at) }}</td>
                <td class="px-4 py-3 text-center">
                  <div class="flex items-center justify-center gap-1">
                    <button @click="openEditModal(user)" class="text-blue hover:text-blue-dark p-1 cursor-pointer" title="تعديل">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                      </svg>
                    </button>
                    <button @click="toggleActive(user)" class="p-1 cursor-pointer" :class="user.is_active ? 'text-warning hover:text-danger' : 'text-success hover:text-success'" :title="user.is_active ? 'تعطيل' : 'تفعيل'">
                      <svg v-if="user.is_active" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"/>
                      </svg>
                      <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
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
          @click="currentPage = p; fetchUsers()"
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
          <h3 class="text-lg font-bold text-brand mb-4">{{ editingUser ? 'تعديل مستخدم' : 'مستخدم جديد' }}</h3>

          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">الاسم</label>
              <input v-model="form.name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="الاسم الكامل" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">رقم الجوال</label>
              <input v-model="form.phone" dir="ltr" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="05xxxxxxxx" />
            </div>
            <div v-if="!editingUser">
              <label class="block text-xs font-medium text-text-light mb-1">كلمة المرور</label>
              <input v-model="form.password" type="password" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="كلمة المرور" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">الدور</label>
              <select v-model="form.role" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue bg-white">
                <option value="partner">شريك</option>
                <option value="employee">موظف</option>
                <option value="supervisor">مشرف</option>
                <option value="owner">مالك</option>
              </select>
            </div>
          </div>

          <p v-if="formError" class="text-xs text-danger mt-3">{{ formError }}</p>

          <div class="flex gap-2 mt-5">
            <button
              @click="submitForm"
              :disabled="formSaving"
              class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-semibold hover:bg-blue/90 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {{ formSaving ? 'جاري الحفظ...' : (editingUser ? 'حفظ التعديلات' : 'إنشاء') }}
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
import { ref, watch, onMounted, computed } from 'vue'
import { usersApi, type UserResponse } from '../../api/client'
import { logout } from '../../stores/authStore'
import NotificationBell from '../../components/NotificationBell.vue'
import { useRouter } from 'vue-router'
const router = useRouter()
function handleLogout() { logout(); router.push('/login') }

const users = ref<UserResponse[]>([])
const loading = ref(false)
const filterRole = ref('')
const currentPage = ref(1)
const totalItems = ref(0)
const pageSize = 20
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize))

// Modal
const showModal = ref(false)
const editingUser = ref<UserResponse | null>(null)
const form = ref({ name: '', phone: '', password: '', role: 'partner' })
const formError = ref('')
const formSaving = ref(false)

const roleFilters = [
  { value: '', label: 'الكل' },
  { value: 'partner', label: 'شركاء' },
  { value: 'employee', label: 'موظفين' },
  { value: 'supervisor', label: 'مشرفين' },
  { value: 'owner', label: 'ملاك' },
]

onMounted(() => {
  fetchUsers()
  fetchPendingPartners()
})

watch(filterRole, () => {
  currentPage.value = 1
  fetchUsers()
})

async function fetchUsers() {
  loading.value = true
  try {
    const data = await usersApi.list({
      role: filterRole.value || undefined,
      page: currentPage.value,
      size: pageSize,
    })
    users.value = data.items
    totalItems.value = data.total
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

function roleLabel(role: string): string {
  const map: Record<string, string> = { partner: 'شريك', employee: 'موظف', supervisor: 'مشرف', owner: 'مالك' }
  return map[role] || role
}

function roleClass(role: string): string {
  const map: Record<string, string> = {
    partner: 'bg-blue/10 text-blue',
    employee: 'bg-purple-100 text-purple-700',
    supervisor: 'bg-amber-100 text-amber-700',
    owner: 'bg-red-100 text-red-700',
  }
  return map[role] || 'bg-gray-100 text-gray-600'
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('ar-SA', { year: 'numeric', month: 'short', day: 'numeric' })
}

function openCreateModal() {
  editingUser.value = null
  form.value = { name: '', phone: '', password: '', role: 'partner' }
  formError.value = ''
  showModal.value = true
}

function openEditModal(user: UserResponse) {
  editingUser.value = user
  form.value = { name: user.name, phone: user.phone, password: '', role: user.role }
  formError.value = ''
  showModal.value = true
}

async function submitForm() {
  formError.value = ''
  formSaving.value = true
  try {
    if (editingUser.value) {
      await usersApi.update(editingUser.value.id, {
        name: form.value.name || undefined,
        phone: form.value.phone || undefined,
        role: form.value.role || undefined,
      })
    } else {
      if (!form.value.name || !form.value.phone || !form.value.password) {
        formError.value = 'جميع الحقول مطلوبة'
        formSaving.value = false
        return
      }
      await usersApi.create({
        name: form.value.name,
        phone: form.value.phone,
        password: form.value.password,
        role: form.value.role,
      })
    }
    showModal.value = false
    fetchUsers()
  } catch (err: any) {
    formError.value = err?.message || 'حدث خطأ'
  } finally {
    formSaving.value = false
  }
}

async function toggleActive(user: UserResponse) {
  try {
    if (user.is_active) {
      await usersApi.deactivate(user.id)
    } else {
      await usersApi.update(user.id, { is_active: true })
    }
    fetchUsers()
  } catch {
    // silent
  }
}

// ─── Pending Partners ──────────────────────────────────────────────────────
const pendingPartners = ref<any[]>([])

async function fetchPendingPartners() {
  try {
    const data = await usersApi.listPending()
    pendingPartners.value = data.items
  } catch { /* silent */ }
}

async function approvePending(user: any) {
  try {
    await usersApi.approveUser(user.id)
    await Promise.all([fetchPendingPartners(), fetchUsers()])
  } catch { /* silent */ }
}

async function rejectPending(user: any) {
  if (!confirm(`هل تريد رفض طلب تسجيل ${user.name}؟`)) return
  try {
    await usersApi.rejectUser(user.id)
    await fetchPendingPartners()
  } catch { /* silent */ }
}
</script>
