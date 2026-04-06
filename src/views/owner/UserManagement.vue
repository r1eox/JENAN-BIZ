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
            {{ currentUser?.role === 'employee' ? 'موظف' : currentUser?.role === 'supervisor' ? 'مشرف' : 'المالك' }}
          </span>
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

      <!-- Bulk action bar -->
      <div v-if="users.length > 0" class="flex items-center gap-3 mb-4">
        <button @click="toggleSelectAll"
          class="flex items-center gap-2 text-sm px-3 py-2 rounded-xl border border-border bg-white hover:border-blue/40 transition-colors cursor-pointer">
          <span class="w-4 h-4 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors"
            :class="allSelected ? 'bg-blue border-blue' : 'border-gray-300'">
            <svg v-if="allSelected" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
            </svg>
          </span>
          {{ allSelected ? 'إلغاء التحديد' : 'تحديد الكل' }}
        </button>
        <Transition name="fade">
          <button v-if="selected.size > 0" @click="deleteSelected"
            class="flex items-center gap-2 text-sm px-4 py-2 rounded-xl bg-danger text-white hover:bg-red-700 transition-colors cursor-pointer font-semibold">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
            حذف المحدد ({{ selected.size }})
          </button>
        </Transition>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-16">
        <div class="w-8 h-8 border-3 border-blue/30 border-t-blue rounded-full animate-spin"></div>
      </div>

      <!-- Users List (card-based) -->
      <div v-else class="space-y-3">
        <div v-for="user in users" :key="user.id"
          class="bg-white rounded-2xl border border-border overflow-hidden transition-all cursor-pointer"
          :class="{ 'opacity-60': !user.is_active, 'ring-2 ring-blue/30 bg-blue/5': selected.has(user.id) }"
          @click="toggleSelect(user.id)">

          <!-- User header -->
          <div class="p-4 flex items-center gap-3 flex-wrap" @click.stop>
            <!-- Checkbox -->
            <span class="w-4 h-4 rounded border-2 flex-shrink-0 flex items-center justify-center transition-colors"
              :class="selected.has(user.id) ? 'bg-blue border-blue' : 'border-gray-300'">
              <svg v-if="selected.has(user.id)" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
              </svg>
            </span>

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
              <button @click="deleteUser(user)" title="حذف المستخدم"
                class="text-xs px-2.5 py-1.5 rounded-lg border border-danger/30 text-danger hover:bg-danger/5 cursor-pointer transition-colors">
                حذف
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
import { logout, currentUser } from '../../stores/authStore'
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
  { label: 'الجهات التمويلية', keys: ['add_entities', 'edit_entities', 'view_entity_contacts', 'manage_entity_contacts'] },
  { label: 'السجلات', keys: ['view_brokers', 'manage_brokers', 'view_business_registry', 'manage_business_registry'] },
  { label: 'التسويق والتقارير', keys: ['send_campaigns', 'view_analytics', 'view_employee_stats'] },
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

// ─── Bulk select ─────────────────────────────────────
const selected = ref<Set<string>>(new Set())
const allSelected = computed(() => users.value.length > 0 && users.value.every(u => selected.value.has(u.id)))
function toggleSelect(id: string) {
  const s = new Set(selected.value); s.has(id) ? s.delete(id) : s.add(id); selected.value = s
}
function toggleSelectAll() {
  allSelected.value ? selected.value = new Set() : selected.value = new Set(users.value.map(u => u.id))
}
async function deleteUser(user: UserResponse) {
  if (!confirm(`حذف المستخدم ${user.name}؟`)) return
  try { await usersApi.deactivate(user.id); showToast('تم حذف المستخدم'); fetchUsers() } catch { /* silent */ }
}
async function deleteSelected() {
  if (!confirm(`حذف ${selected.value.size} مستخدم؟`)) return
  try {
    await Promise.all([...selected.value].map(id => usersApi.deactivate(id)))
    selected.value = new Set()
    showToast('تم حذف المستخدمين المحددين')
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
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s, transform 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.95); }
</style>

