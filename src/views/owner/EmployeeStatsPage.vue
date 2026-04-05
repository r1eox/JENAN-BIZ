<template>
  <div class="min-h-screen bg-bg" dir="rtl">
    <!-- Header -->
    <header class="bg-white border-b border-border px-6 py-4 flex items-center gap-3 sticky top-0 z-10">
      <router-link to="/owner" class="text-text-light hover:text-brand transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
      </router-link>
      <div>
        <h1 class="text-lg font-bold text-brand">إحصائيات الموظفين</h1>
        <p class="text-xs text-text-light">أداء الموظفين بناءً على الملفات المعالجة</p>
      </div>
    </header>

    <main class="p-6 max-w-4xl mx-auto">
      <!-- Loading -->
      <div v-if="loading" class="text-center text-text-light py-20">جاري التحميل...</div>

      <!-- Empty -->
      <div v-else-if="stats.length === 0" class="text-center text-text-light py-20">
        <svg class="w-12 h-12 mx-auto mb-4 text-border" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
        <p>لا تتوفر بيانات بعد</p>
      </div>

      <!-- Summary cards -->
      <div v-else>
        <div class="grid grid-cols-3 gap-4 mb-8">
          <div class="bg-white rounded-2xl border border-border p-5 text-center">
            <p class="text-3xl font-bold text-brand">{{ totals.total }}</p>
            <p class="text-xs text-text-light mt-1">إجمالي الملفات</p>
          </div>
          <div class="bg-success/5 rounded-2xl border border-success/20 p-5 text-center">
            <p class="text-3xl font-bold text-success">{{ totals.completed }}</p>
            <p class="text-xs text-text-light mt-1">مكتملة (رسوم محصّلة)</p>
          </div>
          <div class="bg-danger/5 rounded-2xl border border-danger/20 p-5 text-center">
            <p class="text-3xl font-bold text-danger">{{ totals.rejected }}</p>
            <p class="text-xs text-text-light mt-1">مرفوضة</p>
          </div>
        </div>

        <!-- Table -->
        <div class="bg-white rounded-2xl border border-border overflow-hidden">
          <div class="px-5 py-4 border-b border-border">
            <p class="font-semibold text-brand">تفاصيل لكل موظف</p>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-border">
                  <th class="text-right text-xs font-semibold text-text-light px-5 py-3">#</th>
                  <th class="text-right text-xs font-semibold text-text-light px-5 py-3">الموظف</th>
                  <th class="text-right text-xs font-semibold text-text-light px-5 py-3">الدور</th>
                  <th class="text-center text-xs font-semibold text-text-light px-5 py-3">الإجمالي</th>
                  <th class="text-center text-xs font-semibold text-text-light px-5 py-3">مكتمل</th>
                  <th class="text-center text-xs font-semibold text-text-light px-5 py-3">جارٍ</th>
                  <th class="text-center text-xs font-semibold text-text-light px-5 py-3">مرفوض</th>
                  <th class="text-right text-xs font-semibold text-text-light px-5 py-3">معدل الإنجاز</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(s, idx) in stats" :key="s.user_id"
                  class="border-b border-border last:border-0 hover:bg-bg/50 transition-colors">
                  <td class="px-5 py-3.5 text-xs text-text-light">{{ idx + 1 }}</td>
                  <td class="px-5 py-3.5 font-medium text-brand">{{ s.name }}</td>
                  <td class="px-5 py-3.5">
                    <span class="text-xs px-2 py-1 rounded-lg"
                      :class="s.role === 'supervisor' ? 'bg-amber-100 text-amber-700' : 'bg-purple-100 text-purple-700'">
                      {{ s.role === 'supervisor' ? 'مشرف' : 'موظف' }}
                    </span>
                  </td>
                  <td class="px-5 py-3.5 text-center font-semibold text-brand">{{ s.total }}</td>
                  <td class="px-5 py-3.5 text-center font-semibold text-success">{{ s.completed }}</td>
                  <td class="px-5 py-3.5 text-center text-blue">{{ s.in_progress }}</td>
                  <td class="px-5 py-3.5 text-center text-danger">{{ s.rejected }}</td>
                  <td class="px-5 py-3.5">
                    <div class="flex items-center gap-2">
                      <div class="flex-1 h-1.5 bg-border rounded-full overflow-hidden max-w-24">
                        <div class="h-full bg-success rounded-full transition-all"
                          :style="{ width: completionRate(s) + '%' }"></div>
                      </div>
                      <span class="text-xs text-text-light whitespace-nowrap">{{ completionRate(s) }}%</span>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { employeeStatsApi } from '../../api/client'

interface Stat {
  user_id: string
  name: string
  role: string
  total: number
  completed: number
  rejected: number
  in_progress: number
}

const stats = ref<Stat[]>([])
const loading = ref(false)

const totals = computed(() => ({
  total: stats.value.reduce((s, r) => s + r.total, 0),
  completed: stats.value.reduce((s, r) => s + r.completed, 0),
  rejected: stats.value.reduce((s, r) => s + r.rejected, 0),
}))

function completionRate(s: Stat) {
  if (!s.total) return 0
  return Math.round((s.completed / s.total) * 100)
}

async function load() {
  loading.value = true
  try {
    const d: any = await employeeStatsApi.get()
    stats.value = d.stats || []
  } catch { /**/ } finally { loading.value = false }
}

onMounted(load)
</script>
