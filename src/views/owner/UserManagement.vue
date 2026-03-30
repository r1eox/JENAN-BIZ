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
      <div class="mt-6 mb-5 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 class="text-xl font-bold text-brand">إدارة المستخدمين والصلاحيات</h1>
          <p class="text-sm text-text-light mt-1">إنشاء وتعديل المستخدمين وضبط صلاحيات كل مستخدم</p>
        </div>
        <button @click="openCreateModal"
          class="bg-blue text-white text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-blue/90 transition-colors cursor-pointer flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          مستخدم جديد
        </button>
      </div>

      <!-- Pending Partners -->
      <div v-if="pendingPartners.length > 0" class="mb-5">
        <h2 class="text-sm font-bold text-brand mb-2 flex items-center gap-2">
          <span class="w-2 h-2 bg-warning rounded-full animate-pulse"></span>
          طلبات تسجيل شركاء جدد
          <span class="text-xs font-bold bg-warning/15 text-warning px-2 py-0.5 rounded-lg">{{ pendingPartners.length }} طلبات</span>
        </h2>
        <div class="space-y-2">
          <div v-for="p in pendingPartners" :key="p.id"
            class="bg-white rounded-xl border border-warning/40 p-3 flex items-center justify-between gap-4">
            <div>
              <p class="font-bold text-brand text-sm">{{ p.name }}</p>
              <p class="text-xs text-text-light" dir="ltr">{{ p.phone }}</p>
            </div>
            <div class="flex gap-2">
              <button @click="approvePending(p)" class="text-xs font-bold text-success bg-success/10 px-3 py-1.5 rounded-lg hover:bg-success/20 cursor-pointer">قبول ✓</button>
              <button @click="rejectPending(p)" class="text-xs font-bold text-danger bg-danger/10 px-3 py-1.5 rounded-lg hover:bg-danger/20 cursor-pointer">رفض ✗</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap gap-2 mb-4">
        <button v-for="r in roleFilters" :key="r.value"
          @click="filterRole = r.value; currentPage = 1; fetchUsers()"
          class="px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer transition-colors"
          :class="filterRole === r.value ? 'bg-blue text-white' : 'bg-white text-text-light border border-border hover:border-blue/30'">
          {{ r.label }}
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-16">
        <div class="w-8 h-8 border-3 border-blue/30 border-t-blue rounded-full animate-spin"></div>
      </div>

      <!-- Users List (card-based) -->
      <div v-else class="space-y-3">
        <div v-for="user in users" :key="user.id"
          class="bg-white rounded-2xl border border-border overflow-hidden transition-all"
          :class="{ 'opacity-60': !user.is_active }">

          <!-- User header -->
          <div class="p-4 flex items-center gap-3 flex-wrap">
            <!-- Avatar -->
            <div class="w-10 h-10 rounded-xl font-bold text-base flex items-center justify-center flex-shrink-0"
              :class="roleStyle(user.role).bg + ' ' + roleStyle(user.role).text">
              {{ user.name?.charAt(0) }}
            </div>

            <!-- Info -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-bold text-brand text-sm">{{ user.name }}</span>
                <span class="text-xs font-medium px-2 py-0.5 rounded-lg" :class="roleStyle(user.role).bg + ' ' + roleStyle(user.role).text">
                  {{ roleLabel(user.role) }}
                </span>
                <span class="text-xs" :class="user.is_active ? 'text-success' : 'text-danger'">
                  {{ user.is_active ? '● نشط' : '● معطّل' }}
                </span>
              </div>
              <p class="text-xs text-text-light mt-0.5" dir="ltr">{{ user.phone }}</p>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-1.5 flex-shrink-0">
              <button @click="openEditModal(user)" title="تعديل البيانات"
                class="text-xs px-2.5 py-1.5 rounded-lg border border-border text-text-light hover:border-blue/40 hover:text-blue cursor-pointer transition-colors">
                تعديل
              </button>
              <button @click="openPermModal(user)" title="إدارة الصلاحيات"
                class="text-xs px-2.5 py-1.5 rounded-lg border border-blue/30 text-blue hover:bg-blue/5 cursor-pointer transition-colors flex items-center gap-1">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
                </svg>
                الصلاحيات
              </button>
              <button @click="toggleActive(user)"
                :title="user.is_active ? 'تعطيل الحساب' : 'تفعيل الحساب'"
                class="text-xs px-2.5 py-1.5 rounded-lg border cursor-pointer transition-colors"
                :class="user.is_active ? 'border-danger/30 text-danger hover:bg-danger/5' : 'border-success/30 text-success hover:bg-success/5'">
                {{ user.is_active ? 'تعطيل' : 'تفعيل' }}
              </button>
            </div>
          </div>

          <!-- Permissions row -->
          <div class="px-4 pb-3 border-t border-border/40 pt-2.5">
            <div v-if="user.role === 'owner'" class="flex items-center gap-2">
              <span class="text-[11px] text-text-light">الصلاحيات:</span>
              <span class="text-[11px] bg-success/10 text-success px-2 py-0.5 rounded-lg font-semibold">كل الصلاحيات (مالك)</span>
            </div>
            <div v-else class="flex items-start gap-2 flex-wrap">
              <span class="text-[11px] text-text-light mt-0.5 flex-shrink-0">الصلاحيات:</span>
              <div class="flex flex-wrap gap-1">
                <template v-for="perm in getEffective(user)" :key="perm">
                  <span class="text-[11px] px-2 py-0.5 rounded-lg"
                    :class="isExtra(user, perm) ? 'bg-warning/15 text-warning border border-warning/20 font-semibold' : 'bg-blue/10 text-blue'">
                    {{ permLabel(perm) }}{{ isExtra(user, perm) ? ' ★' : '' }}
                  </span>
                </template>
                <span v-if="!getEffective(user).length" class="text-[11px] text-text-light/50 italic">لا صلاحيات</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="users.length === 0" class="bg-white rounded-2xl border border-border p-10 text-center text-sm text-text-light">
          لا يوجد مستخدمون
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex justify-center gap-2 mt-4">
        <button v-for="p in totalPages" :key="p"
          @click="currentPage = p; fetchUsers()"
          class="w-8 h-8 rounded-lg text-xs font-medium cursor-pointer"
          :class="currentPage === p ? 'bg-blue text-white' : 'bg-white border border-border text-text-light'">
          {{ p }}
        </button>
      </div>

      <!-- Legend -->
      <div class="mt-5 flex gap-4 text-xs text-text-light flex-wrap">
        <div class="flex items-center gap-1.5"><span class="w-3 h-3 bg-blue/20 rounded"></span> صلاحية من الدور</div>
        <div class="flex items-center gap-1.5"><span class="w-3 h-3 bg-warning/20 rounded"></span> صلاحية مضافة يدوياً ★</div>
      </div>
    </main>

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast" class="fixed bottom-6 left-1/2 -translate-x-1/2 bg-brand text-white text-sm font-semibold px-6 py-3 rounded-2xl shadow-xl z-50 flex items-center gap-2">
        <svg class="w-4 h-4 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
        </svg>
        {{ toast }}
      </div>
    </Transition>
  </div>

  <!-- ── Create / Edit User Modal ────────────────────── -->
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
            <input v-model="form.password" type="password" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
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
        <p v-if="formError" class="text-xs text-danger mt-3 bg-danger/5 rounded-xl px-3 py-2">{{ formError }}</p>
        <div class="flex gap-2 mt-5">
          <button @click="submitForm" :disabled="formSaving"
            class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-semibold hover:bg-blue/90 disabled:opacity-50 cursor-pointer">
            {{ formSaving ? 'جاري الحفظ...' : (editingUser ? 'حفظ التعديلات' : 'إنشاء') }}
          </button>
          <button @click="showModal = false" class="px-4 py-2.5 rounded-xl bg-gray-100 text-text-light text-sm hover:bg-gray-200 cursor-pointer">إلغاء</button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- ── Permissions Modal ──────────────────────────── -->
  <Teleport to="body">
    <div v-if="permUser" class="fixed inset-0 z-50 flex items-start justify-center p-4 bg-black/40 overflow-y-auto" @click.self="permUser = null">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg my-6 p-6" @click.stop>
        <!-- Header -->
        <div class="flex items-center justify-between mb-1">
          <h3 class="text-lg font-bold text-brand">صلاحيات: {{ permUser.name }}</h3>
          <button @click="permUser = null" class="text-text-light hover:text-danger cursor-pointer">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <p class="text-xs text-text-light mb-4">
          الدور: <span class="font-semibold" :class="roleStyle(permUser.role).text">{{ roleLabel(permUser.role) }}</span>
          — الصلاحيات الزرقاء من الدور، البرتقالية ★ مضافة يدوياً
        </p>

        <!-- Permission groups -->
        <div class="space-y-4">
          <div v-for="group in permGroups" :key="group.label">
            <p class="text-xs font-bold text-text-light mb-2 uppercase tracking-wide">{{ group.label }}</p>
            <div class="space-y-1.5">
              <div v-for="perm in group.keys" :key="perm"
                class="flex items-center justify-between p-3 rounded-xl border transition-colors"
                :class="isRoleDefault(perm) ? 'border-blue/20 bg-blue/5' : (permForm.includes(perm) ? 'border-warning/30 bg-warning/5' : 'border-border')">
                <div>
                  <p class="text-sm font-medium text-brand">{{ allPerms[perm] }}</p>
                  <span v-if="isRoleDefault(perm)" class="text-[10px] text-blue">من الدور الأساسي — لا يمكن سحبها</span>
                  <span v-else-if="permForm.includes(perm)" class="text-[10px] text-warning font-semibold">مضافة يدوياً ★</span>
                </div>
                <button v-if="!isRoleDefault(perm)"
                  @click="togglePerm(perm)"
                  class="text-xs font-semibold px-3 py-1.5 rounded-lg border cursor-pointer transition-colors flex-shrink-0 mr-2"
                  :class="permForm.includes(perm)
                    ? 'border-danger/30 text-danger bg-danger/5 hover:bg-danger/10'
                    : 'border-success/30 text-success bg-success/5 hover:bg-success/10'">
                  {{ permForm.includes(perm) ? 'سحب' : 'منح' }}
                </button>
                <span v-else class="text-[11px] text-blue/50 px-2 flex-shrink-0">ثابتة</span>
              </div>
            </div>
          </div>
        </div>

        <p v-if="permError" class="text-sm text-danger mt-3 bg-danger/5 rounded-xl px-3 py-2">{{ permError }}</p>

        <div class="flex gap-2 mt-5">
          <button @click="savePerms" :disabled="permSaving"
            class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-semibold hover:bg-blue/90 disabled:opacity-50 cursor-pointer">
            {{ permSaving ? 'جاري الحفظ...' : 'حفظ الصلاحيات' }}
          </button>
          <button @click="permUser = null" class="px-5 py-2.5 rounded-xl bg-gray-100 text-text-light text-sm hover:bg-gray-200 cursor-pointer">إلغاء</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { usersApi, permissionsApi, type UserResponse } from '../../api/client'
import { logout } from '../../stores/authStore'
import NotificationBell from '../../components/NotificationBell.vue'
import { useRouter } from 'vue-router'

const router = useRouter()
function handleLogout() { logout(); router.push('/login') }

// ─── Permissions definitions ──────────────────────────
const allPerms = ref<Record<string, string>>({})
const roleDefaults = ref<Record<string, string[]>>({})

const permGroups = [
  { label: 'المستخدمون', keys: ['add_users', 'edit_users', 'promote_roles', 'approve_partners', 'manage_permissions'] },
  { label: 'الملفات والطلبات', keys: ['view_partner_files', 'view_employee_files', 'view_all_cases', 'update_case_stages', 'assign_cases'] },
  { label: 'الجهات التمويلية', keys: ['add_entities', 'edit_entities'] },
  { label: 'التسويق والتقارير', keys: ['send_campaigns', 'view_analytics'] },
]

async function fetchDefinitions() {
  try {
    const data = await permissionsApi.getDefinitions()
    const map: Record<string, string> = {}
    data.all_permissions.forEach((p: any) => { map[p.key] = p.label })
    allPerms.value = map
    roleDefaults.value = data.role_defaults
  } catch { /* silent */ }
}

// ─── Users ────────────────────────────────────────────
const users = ref<UserResponse[]>([])
const loading = ref(false)
const filterRole = ref('')
const currentPage = ref(1)
const totalItems = ref(0)
const pageSize = 20
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize))
const toast = ref('')

const roleFilters = [
  { value: '', label: 'الكل' },
  { value: 'partner', label: 'شركاء' },
  { value: 'employee', label: 'موظفين' },
  { value: 'supervisor', label: 'مشرفين' },
  { value: 'owner', label: 'ملاك' },
]

onMounted(() => { fetchDefinitions(); fetchUsers(); fetchPendingPartners() })
watch(filterRole, () => { currentPage.value = 1; fetchUsers() })

async function fetchUsers() {
  loading.value = true
  try {
    const data = await usersApi.list({ role: filterRole.value || undefined, page: currentPage.value, size: pageSize })
    users.value = data.items
    totalItems.value = data.total
  } catch { /* silent */ } finally { loading.value = false }
}

function roleLabel(role: string) {
  return ({ partner: 'شريك', employee: 'موظف', supervisor: 'مشرف', owner: 'مالك' } as any)[role] || role
}
function roleStyle(role: string) {
  return ({
    partner:    { text: 'text-blue',       bg: 'bg-blue/10' },
    employee:   { text: 'text-purple-700', bg: 'bg-purple-100' },
    supervisor: { text: 'text-amber-700',  bg: 'bg-amber-100' },
    owner:      { text: 'text-success',    bg: 'bg-success/10' },
  } as any)[role] || { text: 'text-text-light', bg: 'bg-bg' }
}

function permLabel(key: string) { return allPerms.value[key] || key }
function getEffective(u: UserResponse): string[] {
  const rp = roleDefaults.value[u.role] || []
  const ep = (u as any).extra_permissions || []
  return [...new Set([...rp, ...ep])]
}
function isExtra(u: UserResponse, key: string) {
  return ((u as any).extra_permissions || []).includes(key)
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('ar-SA', { year: 'numeric', month: 'short', day: 'numeric' })
}

// ─── Create / Edit Modal ──────────────────────────────
const showModal = ref(false)
const editingUser = ref<UserResponse | null>(null)
const form = ref({ name: '', phone: '', password: '', role: 'partner' })
const formError = ref('')
const formSaving = ref(false)

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
      await usersApi.update(editingUser.value.id, { name: form.value.name || undefined, phone: form.value.phone || undefined, role: form.value.role || undefined })
    } else {
      if (!form.value.name || !form.value.phone || !form.value.password) { formError.value = 'جميع الحقول مطلوبة'; formSaving.value = false; return }
      await usersApi.create({ name: form.value.name, phone: form.value.phone, password: form.value.password, role: form.value.role })
    }
    showModal.value = false
    showToast(editingUser.value ? 'تم حفظ بيانات المستخدم' : 'تم إنشاء المستخدم')
    fetchUsers()
  } catch (e: any) { formError.value = e?.message || 'حدث خطأ' } finally { formSaving.value = false }
}

async function toggleActive(user: UserResponse) {
  try {
    user.is_active ? await usersApi.deactivate(user.id) : await usersApi.update(user.id, { is_active: true })
    fetchUsers()
  } catch { /* silent */ }
}

// ─── Pending Partners ─────────────────────────────────
const pendingPartners = ref<any[]>([])
async function fetchPendingPartners() {
  try { const d = await usersApi.listPending(); pendingPartners.value = d.items } catch { /* silent */ }
}
async function approvePending(user: any) {
  try { await usersApi.approveUser(user.id); await Promise.all([fetchPendingPartners(), fetchUsers()]); showToast(`تمت الموافقة على ${user.name}`) } catch { /* silent */ }
}
async function rejectPending(user: any) {
  if (!confirm(`هل تريد رفض طلب تسجيل ${user.name}؟`)) return
  try { await usersApi.rejectUser(user.id); await fetchPendingPartners(); showToast(`تم رفض طلب ${user.name}`) } catch { /* silent */ }
}

// ─── Permissions Modal ────────────────────────────────
const permUser = ref<UserResponse | null>(null)
const permForm = ref<string[]>([])
const permRoleDefaults = ref<string[]>([])
const permSaving = ref(false)
const permError = ref('')

function openPermModal(user: UserResponse) {
  permUser.value = user
  permError.value = ''
  permRoleDefaults.value = roleDefaults.value[user.role] || []
  permForm.value = [...((user as any).extra_permissions || [])]
}
function isRoleDefault(key: string) { return permRoleDefaults.value.includes(key) }
function togglePerm(key: string) {
  const i = permForm.value.indexOf(key)
  i === -1 ? permForm.value.push(key) : permForm.value.splice(i, 1)
}
async function savePerms() {
  if (!permUser.value) return
  permError.value = ''
  permSaving.value = true
  try {
    const res = await permissionsApi.update(permUser.value.id, permForm.value)
    const idx = users.value.findIndex(u => u.id === permUser.value!.id)
    if (idx !== -1) (users.value[idx] as any).extra_permissions = res.extra_permissions
    permUser.value = null
    showToast('تم حفظ الصلاحيات بنجاح')
  } catch (e: any) { permError.value = e?.message || 'فشل في حفظ الصلاحيات' } finally { permSaving.value = false }
}

function showToast(msg: string) { toast.value = msg; setTimeout(() => { toast.value = '' }, 3000) }
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 10px); }
</style>

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
