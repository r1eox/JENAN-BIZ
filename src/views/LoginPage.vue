<template>
  <div class="min-h-screen min-h-dvh bg-white flex flex-col">
    <!-- Back button -->
    <header class="px-4 pt-4">
      <button @click="$router.push('/')" class="flex items-center gap-1.5 text-text-light hover:text-brand transition-colors cursor-pointer p-1">
        <svg class="w-5 h-5 rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        <span class="text-sm">رجوع</span>
      </button>
    </header>

    <main class="flex-1 flex flex-col justify-center px-6 pb-8 max-w-sm mx-auto w-full">
      <!-- Logo -->
      <div class="text-center mb-8">
        <img src="/logo.svg" alt="Jenan BIZ" class="h-16 mx-auto mb-4" />
        <h1 class="text-xl font-bold text-brand">تسجيل الدخول</h1>
        <p class="text-sm text-text-light mt-1">أدخل بياناتك للوصول إلى حسابك</p>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="space-y-4" novalidate>
        <!-- Phone / Username -->
        <div>
          <label class="block text-sm font-medium text-brand mb-1.5">رقم الجوال أو اسم المستخدم</label>
          <div class="relative">
            <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
            </div>
            <input
              v-model="form.identifier"
              type="text"
              inputmode="text"
              autocomplete="username"
              placeholder="05xxxxxxxx أو اسم المستخدم"
              class="w-full pr-10 pl-4 py-3 border-2 rounded-xl text-brand placeholder-gray-400 transition-colors focus:outline-none"
              :class="errors.identifier ? 'border-danger' : 'border-border focus:border-blue'"
              @input="errors.identifier = ''"
            />
          </div>
          <p v-if="errors.identifier" class="mt-1 text-xs text-danger font-medium">{{ errors.identifier }}</p>
        </div>

        <!-- Password -->
        <div>
          <label class="block text-sm font-medium text-brand mb-1.5">كلمة المرور</label>
          <div class="relative">
            <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
              </svg>
            </div>
            <input
              v-model="form.password"
              :type="showPass ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="أدخل كلمة المرور"
              class="w-full pr-10 pl-12 py-3 border-2 rounded-xl text-brand placeholder-gray-400 transition-colors focus:outline-none"
              :class="errors.password ? 'border-danger' : 'border-border focus:border-blue'"
              @input="errors.password = ''"
            />
            <button type="button" @click="showPass = !showPass" class="absolute inset-y-0 left-0 pl-3 flex items-center cursor-pointer" tabindex="-1">
              <svg v-if="!showPass" class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
              </svg>
              <svg v-else class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
              </svg>
            </button>
          </div>
          <p v-if="errors.password" class="mt-1 text-xs text-danger font-medium">{{ errors.password }}</p>
        </div>

        <!-- Error banner -->
        <div v-if="loginError" class="flex items-start gap-2 bg-danger/5 border border-danger/20 rounded-xl p-3">
          <svg class="w-5 h-5 text-danger flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <p class="text-sm text-danger">{{ loginError }}</p>
        </div>

        <!-- Rate limit warning -->
        <div v-if="isLocked" class="flex items-start gap-2 bg-warning/5 border border-warning/20 rounded-xl p-3">
          <svg class="w-5 h-5 text-warning flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <p class="text-sm text-warning">تم تجاوز عدد المحاولات المسموحة. يرجى الانتظار {{ lockCountdown }} ثانية.</p>
        </div>

        <!-- Submit -->
        <button
          type="submit"
          :disabled="isLoading || isLocked"
          class="w-full py-3.5 rounded-xl bg-blue text-white font-bold text-base shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          <span v-if="!isLoading">تسجيل الدخول</span>
          <span v-else class="flex items-center justify-center gap-2">
            <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
            جاري الدخول...
          </span>
        </button>
      </form>

      <!-- Forgot password -->
      <div class="text-center mt-4">
        <router-link to="/forgot-password" class="text-sm text-blue font-medium hover:underline">
          نسيت كلمة المرور؟
        </router-link>
      </div>

      <!-- Divider -->
      <div class="flex items-center gap-3 my-6">
        <div class="flex-1 h-px bg-border"></div>
        <span class="text-xs text-text-light">أو</span>
        <div class="flex-1 h-px bg-border"></div>
      </div>

      <!-- Sign up link -->
      <router-link
        to="/signup"
        class="block w-full py-3 rounded-xl bg-white text-brand font-bold text-base text-center border-2 border-border hover:border-blue hover:text-blue active:scale-[0.98] transition-all duration-200"
      >
        إنشاء حساب جديد
      </router-link>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { rateLimiter } from '../utils/security'
import { login, getRoleLanding } from '../stores/authStore'
import { ApiException } from '../api/client'

const router = useRouter()
const route = useRoute()
const showPass = ref(false)
const isLoading = ref(false)
const loginError = ref('')
const isLocked = ref(false)
const lockCountdown = ref(0)

let countdownTimer: ReturnType<typeof setInterval> | null = null

const form = reactive({
  identifier: '',
  password: '',
})

const errors = reactive({
  identifier: '',
  password: '',
})

function validate(): boolean {
  let valid = true
  errors.identifier = ''
  errors.password = ''

  if (!form.identifier.trim()) {
    errors.identifier = 'يرجى إدخال رقم الجوال أو اسم المستخدم'
    valid = false
  }
  if (!form.password) {
    errors.password = 'يرجى إدخال كلمة المرور'
    valid = false
  } else if (form.password.length < 6) {
    errors.password = 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'
    valid = false
  }
  return valid
}

function startLockCountdown(seconds: number) {
  isLocked.value = true
  lockCountdown.value = seconds
  countdownTimer = setInterval(() => {
    lockCountdown.value--
    if (lockCountdown.value <= 0) {
      isLocked.value = false
      if (countdownTimer) clearInterval(countdownTimer)
    }
  }, 1000)
}

async function handleLogin() {
  loginError.value = ''
  if (!validate()) return

  // Check rate limit
  const limiterResult = rateLimiter.check('login')
  if (!limiterResult.allowed) {
    startLockCountdown(limiterResult.retryAfter)
    return
  }

  isLoading.value = true
  try {
    const user = await login(form.identifier.trim(), form.password)
    // Redirect to the intended page or role landing
    const redirect = route.query.redirect as string | undefined
    router.push(redirect || getRoleLanding(user.role))
  } catch (err) {
    if (err instanceof ApiException) {
      if (err.status === 401) {
        loginError.value = 'رقم الجوال أو كلمة المرور غير صحيحة'
      } else if (err.status === 403) {
        loginError.value = 'الحساب معطّل. تواصل مع الإدارة'
      } else {
        loginError.value = err.message || 'حدث خطأ في الخادم'
      }
    } else {
      loginError.value = 'تعذر الاتصال بالخادم. تأكد من اتصال الإنترنت'
    }
  } finally {
    isLoading.value = false
  }
}

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>
