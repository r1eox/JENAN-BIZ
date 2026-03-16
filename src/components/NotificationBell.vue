<template>
  <div class="relative">
    <!-- Bell button -->
    <button
      @click="toggleDropdown"
      class="relative p-1.5 text-text-light hover:text-blue transition-colors cursor-pointer"
      title="الإشعارات"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
      </svg>
      <!-- Badge -->
      <span
        v-if="unreadCount > 0"
        class="absolute -top-0.5 -right-0.5 flex items-center justify-center min-w-[18px] h-[18px] bg-danger text-white text-[10px] font-bold rounded-full px-1"
      >
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </button>

    <!-- Dropdown -->
    <Teleport to="body">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50"
        @click="isOpen = false"
      >
        <div
          class="absolute bg-white rounded-2xl shadow-xl border border-border w-80 max-h-[400px] overflow-hidden"
          :style="dropdownStyle"
          @click.stop
        >
          <!-- Header -->
          <div class="flex items-center justify-between px-4 py-3 border-b border-border bg-gray-50/50">
            <h3 class="text-sm font-bold text-brand">الإشعارات</h3>
            <button
              v-if="unreadCount > 0"
              @click="markAllRead"
              class="text-xs text-blue hover:text-blue-dark cursor-pointer"
            >
              تحديد الكل كمقروء
            </button>
          </div>

          <!-- List -->
          <div class="overflow-y-auto max-h-[320px]">
            <div v-if="loading" class="p-6 text-center text-text-light text-sm">
              جاري التحميل...
            </div>
            <div v-else-if="notifications.length === 0" class="p-6 text-center text-text-light text-sm">
              لا توجد إشعارات
            </div>
            <button
              v-for="n in notifications"
              :key="n.id"
              @click="handleClick(n)"
              class="w-full text-right px-4 py-3 border-b border-border/50 hover:bg-gray-50 transition-colors cursor-pointer"
              :class="{ 'bg-blue/5': !n.is_read }"
            >
              <div class="flex items-start gap-2">
                <span
                  v-if="!n.is_read"
                  class="flex-shrink-0 mt-1.5 w-2 h-2 bg-blue rounded-full"
                ></span>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-brand truncate">{{ n.title }}</p>
                  <p class="text-xs text-text-light mt-0.5 line-clamp-2">{{ n.message }}</p>
                  <p class="text-[10px] text-text-light/60 mt-1">{{ formatTime(n.created_at) }}</p>
                </div>
              </div>
            </button>
          </div>

          <!-- Footer: view all -->
          <div class="px-4 py-2.5 border-t border-border bg-gray-50/50">
            <button
              @click="goToAll"
              class="w-full text-center text-xs font-bold text-blue hover:underline cursor-pointer py-0.5"
            >
              عرض جميع الإشعارات
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { notificationsApi, type NotificationItem } from '../api/client'

const router = useRouter()

const isOpen = ref(false)
const loading = ref(false)
const notifications = ref<NotificationItem[]>([])
const unreadCount = ref(0)

// Position dropdown
const dropdownStyle = computed(() => ({
  top: '56px',
  left: '16px',
}))

let pollTimer: ReturnType<typeof setInterval> | null = null

onMounted(async () => {
  await fetchUnreadCount()
  // Poll every 30 seconds
  pollTimer = setInterval(fetchUnreadCount, 30000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function fetchUnreadCount() {
  try {
    const data = await notificationsApi.unreadCount()
    unreadCount.value = data.unread
  } catch {
    // silent
  }
}

async function fetchNotifications() {
  loading.value = true
  try {
    const data = await notificationsApi.list(1, 20)
    notifications.value = data.items
    unreadCount.value = data.unread
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

function toggleDropdown() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    fetchNotifications()
  }
}

async function markAllRead() {
  try {
    await notificationsApi.markAllRead()
    notifications.value.forEach((n: NotificationItem) => n.is_read = true)
    unreadCount.value = 0
  } catch {
    // silent
  }
}

async function handleClick(n: NotificationItem) {
  if (!n.is_read) {
    try {
      await notificationsApi.markRead(n.id)
      n.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch { /* silent */ }
  }
  isOpen.value = false
  if (n.notification_type === 'new_partner') {
    router.push('/owner/users')
  } else if (n.notification_type === 'approval_result') {
    // Partner approved/rejected — go to partner dashboard
    router.push('/partner')
  } else if (n.case_id) {
    router.push(`/case/${n.case_id}`)
  }
}

function goToAll() {
  isOpen.value = false
  router.push('/notifications')
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
</script>
