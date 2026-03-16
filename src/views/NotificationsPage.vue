<template>
  <div class="min-h-screen min-h-dvh bg-bg">
    <!-- Top bar -->
    <header class="bg-white border-b border-border sticky top-0 z-30">
      <div class="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
        <button @click="router.back()" class="flex items-center gap-1.5 text-text-light hover:text-brand transition-colors cursor-pointer p-1">
          <svg class="w-5 h-5 rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
          <span class="text-sm">رجوع</span>
        </button>
        <span class="text-sm font-bold text-brand">الإشعارات</span>
        <button
          v-if="unreadCount > 0"
          @click="doMarkAllRead"
          class="text-xs text-blue hover:underline cursor-pointer font-medium"
        >
          تحديد الكل كمقروء
        </button>
        <span v-else class="w-16"></span>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="loading && notifications.length === 0" class="max-w-2xl mx-auto px-4 py-16 text-center">
      <svg class="animate-spin w-8 h-8 mx-auto text-blue" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
      </svg>
      <p class="text-sm text-text-light mt-3">جاري تحميل الإشعارات...</p>
    </div>

    <!-- Empty state -->
    <div v-else-if="notifications.length === 0" class="max-w-2xl mx-auto px-4 py-20 text-center">
      <svg class="w-16 h-16 mx-auto text-text-light/20 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
      </svg>
      <p class="text-sm text-text-light font-medium">لا توجد إشعارات</p>
    </div>

    <!-- Notifications list -->
    <main v-else class="max-w-2xl mx-auto px-4 pb-8">
      <!-- Filter tabs -->
      <div class="mt-4 flex gap-1 bg-white rounded-xl border border-border p-1">
        <button
          @click="filter = 'all'"
          class="flex-1 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer"
          :class="filter === 'all' ? 'bg-blue text-white' : 'text-text-light hover:bg-bg'"
        >
          الكل ({{ notifications.length }})
        </button>
        <button
          @click="filter = 'unread'"
          class="flex-1 py-2 rounded-lg text-xs font-bold transition-all cursor-pointer"
          :class="filter === 'unread' ? 'bg-blue text-white' : 'text-text-light hover:bg-bg'"
        >
          غير مقروء ({{ unreadCount }})
        </button>
      </div>

      <div class="mt-3 space-y-2">
        <button
          v-for="n in filteredNotifications"
          :key="n.id"
          @click="handleClick(n)"
          class="w-full text-right bg-white rounded-2xl border p-4 hover:shadow-sm transition-all cursor-pointer"
          :class="n.is_read ? 'border-border' : 'border-blue/20 bg-blue/[0.02]'"
        >
          <div class="flex items-start gap-3">
            <!-- Icon -->
            <div class="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
              :class="iconClass(n.notification_type)">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="iconPath(n.notification_type)"/>
              </svg>
            </div>

            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2">
                <p class="text-sm font-bold text-brand leading-snug">{{ n.title }}</p>
                <div class="flex items-center gap-1.5 flex-shrink-0">
                  <span
                    v-if="!n.is_read"
                    class="w-2 h-2 bg-blue rounded-full flex-shrink-0"
                  ></span>
                  <span class="text-[10px] text-text-light whitespace-nowrap">{{ formatTime(n.created_at) }}</span>
                </div>
              </div>
              <p class="text-xs text-text-light mt-0.5 leading-relaxed">{{ n.message }}</p>
              <p v-if="n.case_id" class="text-[10px] text-blue mt-1">اضغط للعرض ←</p>
            </div>
          </div>
        </button>
      </div>

      <!-- Load more -->
      <div v-if="hasMore" class="mt-4 text-center">
        <button
          @click="loadMore"
          :disabled="loading"
          class="text-sm text-blue font-bold hover:underline cursor-pointer disabled:opacity-50"
        >
          {{ loading ? 'جاري التحميل...' : 'تحميل المزيد' }}
        </button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { notificationsApi, type NotificationItem } from '../api/client'

const router = useRouter()
const loading = ref(false)
const notifications = ref<NotificationItem[]>([])
const unreadCount = ref(0)
const filter = ref<'all' | 'unread'>('all')
const page = ref(1)
const hasMore = ref(false)

const filteredNotifications = computed(() =>
  filter.value === 'unread'
    ? notifications.value.filter(n => !n.is_read)
    : notifications.value
)

async function loadNotifications(reset = false) {
  loading.value = true
  try {
    if (reset) {
      page.value = 1
      notifications.value = []
    }
    const data = await notificationsApi.list(page.value, 30)
    if (reset) {
      notifications.value = data.items
    } else {
      notifications.value.push(...data.items)
    }
    unreadCount.value = data.unread
    hasMore.value = data.items.length === 30 && notifications.value.length < data.total
  } catch { /* silent */ }
  loading.value = false
}

async function loadMore() {
  page.value++
  await loadNotifications(false)
}

async function doMarkAllRead() {
  try {
    await notificationsApi.markAllRead()
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  } catch { /* silent */ }
}

async function handleClick(n: NotificationItem) {
  if (!n.is_read) {
    try {
      await notificationsApi.markRead(n.id)
      n.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch { /* silent */ }
  }
  if (n.notification_type === 'new_partner') {
    router.push('/owner/users')
  } else if (n.notification_type === 'approval_result') {
    router.push('/partner')
  } else if (n.case_id) {
    router.push(`/case/${n.case_id}`)
  }
}

function iconClass(type: string): string {
  switch (type) {
    case 'new_case': return 'bg-blue/10 text-blue'
    case 'stage_change': return 'bg-success/10 text-success'
    case 'rejection': return 'bg-danger/10 text-danger'
    case 'completion_request': return 'bg-warning/10 text-warning'
    case 'approval_request': return 'bg-warning/10 text-warning'
    case 'approval_result': return 'bg-success/10 text-success'
    case 'new_partner': return 'bg-brand/10 text-brand'
    case 'docs_required': return 'bg-warning/10 text-warning'
    default: return 'bg-gray-100 text-text-light'
  }
}

function iconPath(type: string): string {
  switch (type) {
    case 'new_case': return 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'
    case 'stage_change': return 'M9 5l7 7-7 7'
    case 'rejection': return 'M6 18L18 6M6 6l12 12'
    case 'completion_request': case 'docs_required': return 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12'
    case 'approval_request': case 'approval_result': return 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
    case 'new_partner': return 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z'
    default: return 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9'
  }
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'الآن'
  if (mins < 60) return `منذ ${mins} دقيقة`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `منذ ${hours} ساعة`
  const days = Math.floor(hours / 24)
  if (days < 7) return `منذ ${days} يوم`
  return d.toLocaleDateString('ar-SA', { month: 'short', day: 'numeric' })
}

onMounted(() => loadNotifications(true))
</script>
