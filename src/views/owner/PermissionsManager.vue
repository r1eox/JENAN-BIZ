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
          <router-link to="/owner/entities" class="text-sm text-text-light hover:text-blue transition-colors">الجهات</router-link>
          <button @click="handleLogout" class="text-text-light hover:text-danger transition-colors cursor-pointer p-1">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-5xl mx-auto px-4 pb-8">
      <div class="mt-6 mb-4">
        <h1 class="text-xl font-bold text-brand">إدارة الصلاحيات</h1>
        <p class="text-sm text-text-light mt-1">
          تحكم في صلاحيات كل مستخدم — يمكنك منح صلاحيات إضافية تتجاوز دوره الأساسي
        </p>
      </div>

      <!-- Info banner -->
      <div class="bg-blue/5 border border-blue/20 rounded-2xl p-4 mb-5">
        <div class="flex gap-3">
          <svg class="w-5 h-5 text-blue flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <div class="text-sm text-brand">
            <p class="font-semibold mb-2">كيف تعمل الصلاحيات؟</p>
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-text-light">
              <div v-for="role in roleInfos" :key="role.key" class="bg-white rounded-xl p-2 border border-border">
                <span class="font-bold" :class="role.color">{{ role.label }}:</span>
                <div class="mt-1 space-y-0.5">
                  <div v-if="definitions.role_defaults[role.key]?.length">
                    <span v-for="p in definitions.role_defaults[role.key]" :key="p"
                      class="inline-block ml-1 mb-0.5 bg-blue/10 text-blue px-1.5 py-0.5 rounded text-[10px]">
                      {{ getPermLabel(p) }}
                    </span>
                  </div>
                  <span v-else class="text-text-light/60 italic">لا صلاحيات افتراضية</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap gap-2 mb-4">
        <button
          v-for="r in roleFilters"
          :key="r.value"
          @click="filterRole = r.value; currentPage = 1; fetchUsers()"
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer"
          :class="filterRole === r.value ? 'bg-blue text-white' : 'bg-white text-text-light border border-border hover:border-blue/30'"
        >
          {{ r.label }}
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-16">
        <div class="w-8 h-8 border-3 border-blue/30 border-t-blue rounded-full animate-spin"></div>
      </div>

      <!-- Users list -->
      <div v-else class="space-y-3">
        <div
          v-for="user in users"
          :key="user.id"
          class="bg-white rounded-2xl border border-border overflow-hidden"
        >
          <div class="p-4">
            <div class="flex items-center justify-between gap-4 flex-wrap">
              <div class="flex items-center gap-3">
                <!-- Avatar letter -->
                <div class="w-10 h-10 rounded-xl flex items-center justify-center text-base font-bold flex-shrink-0"
                  :class="roleStyle(user.role).bg + ' ' + roleStyle(user.role).text">
                  {{ user.name?.charAt(0) || '?' }}
                </div>
                <div>
                  <p class="font-bold text-brand text-sm">{{ user.name }}</p>
                  <p class="text-xs text-text-light" dir="ltr">{{ user.phone }}</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-medium px-2.5 py-1 rounded-lg" :class="roleStyle(user.role).bg + ' ' + roleStyle(user.role).text">
                  {{ roleLabel(user.role) }}
                </span>
                <button
                  @click="openPermissions(user)"
                  class="text-sm px-3 py-1.5 rounded-lg border border-blue/30 text-blue hover:bg-blue/5 transition-colors cursor-pointer flex items-center gap-1.5"
                >
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
                  </svg>
                  تعديل الصلاحيات
                </button>
              </div>
            </div>

            <!-- Current effective permissions preview -->
            <div class="mt-3">
              <div v-if="user.role === 'owner'" class="flex flex-wrap gap-1">
                <span class="text-[11px] bg-success/10 text-success px-2 py-0.5 rounded-lg font-medium">جميع الصلاحيات (مالك)</span>
              </div>
              <div v-else class="flex flex-wrap gap-1">
                <template v-for="perm in getEffectivePerms(user)" :key="perm">
                  <span
                    class="text-[11px] px-2 py-0.5 rounded-lg"
                    :class="isExtraPerm(user, perm) ? 'bg-warning/15 text-warning font-semibold border border-warning/20' : 'bg-blue/10 text-blue'"
                    :title="isExtraPerm(user, perm) ? 'صلاحية مضافة يدوياً' : 'من الدور الأساسي'"
                  >
                    {{ getPermLabel(perm) }}
                    <span v-if="isExtraPerm(user, perm)" class="mr-0.5">★</span>
                  </span>
                </template>
                <span v-if="!getEffectivePerms(user).length" class="text-[11px] text-text-light/60 italic">لا صلاحيات</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="users.length === 0" class="bg-white rounded-2xl border border-border p-10 text-center text-sm text-text-light">
          لا يوجد مستخدمون
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 mt-4">
        <button
          v-for="p in totalPages"
          :key="p"
          @click="currentPage = p; fetchUsers()"
          class="w-8 h-8 rounded-lg text-xs font-medium cursor-pointer"
          :class="currentPage === p ? 'bg-blue text-white' : 'bg-white text-text-light border border-border'"
        >{{ p }}</button>
      </div>

      <!-- Legend -->
      <div class="mt-6 flex items-center gap-4 text-xs text-text-light">
        <div class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-3 bg-blue/20 rounded"></span>
          صلاحية من الدور
        </div>
        <div class="flex items-center gap-1.5">
          <span class="inline-block w-3 h-3 bg-warning/20 rounded"></span>
          صلاحية مضافة يدوياً ★
        </div>
      </div>
    </main>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toastMsg" class="fixed bottom-6 left-1/2 -translate-x-1/2 bg-brand text-white text-sm font-semibold px-6 py-3 rounded-2xl shadow-xl z-50 flex items-center gap-2">
        <svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
        </svg>
        {{ toastMsg }}
      </div>
    </Transition>
  </div>

  <!-- Permissions Modal -->
  <Teleport to="body">
    <div v-if="editUser" class="fixed inset-0 z-50 flex items-start justify-center p-4 bg-black/40 overflow-y-auto" @click.self="editUser = null">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg my-6 p-6" @click.stop>
        <!-- Header -->
        <div class="flex items-center justify-between mb-4">
          <div>
            <h3 class="text-lg font-bold text-brand">صلاحيات: {{ editUser.name }}</h3>
            <p class="text-xs text-text-light mt-0.5">
              الدور الحالي:
              <span class="font-medium" :class="roleStyle(editUser.role).text">{{ roleLabel(editUser.role) }}</span>
            </p>
          </div>
          <button @click="editUser = null" class="text-text-light hover:text-danger cursor-pointer">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <!-- All permissions list -->
        <div class="space-y-2">
          <div
            v-for="perm in definitions.all_permissions"
            :key="perm.key"
            class="flex items-center justify-between p-3 rounded-xl border transition-colors"
            :class="isRolePerm(perm.key) ? 'border-blue/20 bg-blue/5' : (editForm.includes(perm.key) ? 'border-warning/30 bg-warning/5' : 'border-border bg-white')"
          >
            <div class="flex-1">
              <p class="text-sm font-medium text-brand">{{ perm.label }}</p>
              <p class="text-[11px] text-text-light mt-0.5 font-mono">{{ perm.key }}</p>
              <span v-if="isRolePerm(perm.key)" class="text-[10px] text-blue font-semibold">من الدور الأساسي</span>
              <span v-else-if="editForm.includes(perm.key)" class="text-[10px] text-warning font-semibold">مضافة يدوياً ★</span>
            </div>
            <div class="flex items-center gap-2 mr-3 flex-shrink-0">
              <button
                v-if="!isRolePerm(perm.key)"
                @click="togglePerm(perm.key)"
                class="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg border transition-all cursor-pointer"
                :class="editForm.includes(perm.key)
                  ? 'border-danger/30 text-danger bg-danger/5 hover:bg-danger/10'
                  : 'border-success/30 text-success bg-success/5 hover:bg-success/10'"
              >
                <svg v-if="editForm.includes(perm.key)" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
                <svg v-else class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
                {{ editForm.includes(perm.key) ? 'سحب' : 'منح' }}
              </button>
              <span v-else class="text-xs text-blue/60 italic px-2">ثابتة</span>
            </div>
          </div>
        </div>

        <!-- Error -->
        <p v-if="editError" class="text-sm text-danger mt-3 bg-danger/5 rounded-xl px-3 py-2">{{ editError }}</p>

        <!-- Actions -->
        <div class="flex gap-2 mt-5">
          <button
            @click="savePermissions"
            :disabled="editSaving"
            class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-semibold hover:bg-blue/90 disabled:opacity-50 cursor-pointer"
          >
            {{ editSaving ? 'جاري الحفظ...' : 'حفظ الصلاحيات' }}
          </button>
          <button @click="editUser = null" class="px-5 py-2.5 rounded-xl bg-gray-100 text-text-light text-sm hover:bg-gray-200 cursor-pointer">
            إلغاء
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usersApi, permissionsApi, type UserResponse } from '../../api/client'
import { logout } from '../../stores/authStore'
import NotificationBell from '../../components/NotificationBell.vue'

const router = useRouter()
function handleLogout() { logout(); router.push('/login') }

// ─── State ──────────────────────────────────────────
const users = ref<UserResponse[]>([])
const loading = ref(false)
const filterRole = ref('employee')
const currentPage = ref(1)
const totalItems = ref(0)
const pageSize = 20
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize))
const toastMsg = ref('')

const definitions = ref<{
  all_permissions: { key: string; label: string }[]
  role_defaults: Record<string, string[]>
}>({ all_permissions: [], role_defaults: {} })

// ─── Role config ────────────────────────────────────
const roleFilters = [
  { value: 'employee', label: 'موظفين' },
  { value: 'supervisor', label: 'مشرفين' },
  { value: 'owner', label: 'ملاك' },
  { value: '', label: 'الكل' },
]

const roleInfos = [
  { key: 'employee', label: 'موظف', color: 'text-purple-600' },
  { key: 'supervisor', label: 'مشرف', color: 'text-warning' },
  { key: 'owner', label: 'مالك', color: 'text-success' },
]

function roleLabel(role: string): string {
  const map: Record<string, string> = { partner: 'شريك', employee: 'موظف', supervisor: 'مشرف', owner: 'مالك' }
  return map[role] || role
}

function roleStyle(role: string): { text: string; bg: string } {
  const map: Record<string, { text: string; bg: string }> = {
    partner:    { text: 'text-blue',        bg: 'bg-blue/10' },
    employee:   { text: 'text-purple-700',  bg: 'bg-purple-100' },
    supervisor: { text: 'text-amber-700',   bg: 'bg-amber-100' },
    owner:      { text: 'text-success',     bg: 'bg-success/10' },
  }
  return map[role] || { text: 'text-text-light', bg: 'bg-bg' }
}

function getPermLabel(key: string): string {
  const perm = definitions.value.all_permissions.find(p => p.key === key)
  return perm?.label || key
}

function getEffectivePerms(user: UserResponse): string[] {
  const rolePerms = definitions.value.role_defaults[user.role] || []
  const extra = (user as any).extra_permissions || []
  return [...new Set([...rolePerms, ...extra])]
}

function isExtraPerm(user: UserResponse, perm: string): boolean {
  const extra = (user as any).extra_permissions || []
  return extra.includes(perm)
}

// Supplemental permissions known to frontend (fallback if backend hasn't deployed yet)
const SUPPLEMENTAL_PERMISSIONS = [
  { key: 'delete_cases',  label: 'حذف الطلبات نهائياً' },
  { key: 'create_cases',  label: 'رفع طلبات تحليل جديدة (للموظفين)' },
]

// ─── Load data ──────────────────────────────────────
onMounted(async () => {
  await fetchDefinitions()
  await fetchUsers()
})

async function fetchDefinitions() {
  try {
    const data = await permissionsApi.getDefinitions()
    // Merge: add any supplemental permissions not already returned by the backend
    const existingKeys = new Set(data.all_permissions.map((p: any) => p.key))
    for (const perm of SUPPLEMENTAL_PERMISSIONS) {
      if (!existingKeys.has(perm.key)) data.all_permissions.push(perm)
    }
    definitions.value = data
  } catch { /* silent */ }
}

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
  } catch { /* silent */ } finally {
    loading.value = false
  }
}

// ─── Permissions Modal ──────────────────────────────
const editUser = ref<UserResponse | null>(null)
const editForm = ref<string[]>([])
const editSaving = ref(false)
const editError = ref('')
const editRolePerms = ref<string[]>([])

function openPermissions(user: UserResponse) {
  editUser.value = user
  editError.value = ''
  editRolePerms.value = definitions.value.role_defaults[user.role] || []
  editForm.value = [...((user as any).extra_permissions || [])]
}

function isRolePerm(key: string): boolean {
  return editRolePerms.value.includes(key)
}

function togglePerm(key: string) {
  const idx = editForm.value.indexOf(key)
  if (idx === -1) editForm.value.push(key)
  else editForm.value.splice(idx, 1)
}

async function savePermissions() {
  if (!editUser.value) return
  editError.value = ''
  editSaving.value = true
  try {
    const res = await permissionsApi.update(editUser.value.id, editForm.value)
    // Update local user
    const idx = users.value.findIndex(u => u.id === editUser.value!.id)
    if (idx !== -1) (users.value[idx] as any).extra_permissions = res.extra_permissions
    editUser.value = null
    showToast('تم حفظ الصلاحيات بنجاح')
  } catch (e: any) {
    editError.value = e.message || 'فشل في حفظ الصلاحيات'
  } finally {
    editSaving.value = false
  }
}

function showToast(msg: string) {
  toastMsg.value = msg
  setTimeout(() => { toastMsg.value = '' }, 3000)
}
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 10px); }
</style>
