<template>
  <div class="min-h-screen min-h-dvh bg-white flex flex-col">
    <!-- Back button -->
    <header class="px-4 pt-4">
      <button @click="goBack" class="flex items-center gap-1.5 text-text-light hover:text-brand transition-colors cursor-pointer p-1">
        <svg class="w-5 h-5 rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        <span class="text-sm">رجوع</span>
      </button>
    </header>

    <main class="flex-1 flex flex-col justify-center px-6 pb-8 max-w-sm mx-auto w-full">

      <!-- ============ Step 1: Enter Phone ============ -->
      <div v-if="step === 'phone'">
        <div class="text-center mb-8">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-blue/10 flex items-center justify-center">
            <svg class="w-8 h-8 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
            </svg>
          </div>
          <h1 class="text-xl font-bold text-brand">استعادة كلمة المرور</h1>
          <p class="text-sm text-text-light mt-2 leading-relaxed">أدخل رقم الجوال المسجّل وسنرسل لك رمز تحقق</p>
        </div>

        <form @submit.prevent="sendOTP" class="space-y-4" novalidate>
          <div>
            <label class="block text-sm font-medium text-brand mb-1.5">رقم الجوال</label>
            <div class="relative">
              <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
                </svg>
              </div>
              <input
                v-model="phone"
                type="tel"
                inputmode="numeric"
                dir="ltr"
                placeholder="05xxxxxxxx"
                class="w-full pr-10 pl-4 py-3 border-2 rounded-xl text-brand placeholder-gray-400 transition-colors focus:outline-none text-left"
                :class="phoneError ? 'border-danger' : 'border-border focus:border-blue'"
                @input="phoneError = ''"
              />
            </div>
            <p v-if="phoneError" class="mt-1 text-xs text-danger font-medium">{{ phoneError }}</p>
          </div>

          <!-- Security: generic message -->
          <p class="text-xs text-text-light leading-relaxed">
            في حال كان الرقم مسجّلاً لدينا، سيتم إرسال رمز تحقق إليه.
          </p>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full py-3.5 rounded-xl bg-blue text-white font-bold shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            <span v-if="!isLoading">إرسال رمز التحقق</span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              جاري الإرسال...
            </span>
          </button>
        </form>
      </div>

      <!-- ============ Step 2: Enter OTP ============ -->
      <div v-else-if="step === 'otp'">
        <div class="text-center mb-8">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-blue/10 flex items-center justify-center">
            <svg class="w-8 h-8 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/>
            </svg>
          </div>
          <h1 class="text-xl font-bold text-brand">أدخل رمز التحقق</h1>
          <p class="text-sm text-text-light mt-2">تم إرسال رمز مكوّن من 4 أرقام إلى</p>
          <p class="text-sm font-bold text-brand mt-1 dir-ltr" dir="ltr">{{ maskedPhone }}</p>
        </div>

        <form @submit.prevent="verifyOTP" class="space-y-5" novalidate>
          <!-- OTP Inputs -->
          <div class="flex justify-center gap-3" dir="ltr">
            <input
              v-for="(_, i) in 4"
              :key="i"
              :ref="el => { if (el) otpRefs[i] = el as HTMLInputElement }"
              v-model="otp[i]"
              type="text"
              inputmode="numeric"
              maxlength="1"
              class="otp-input"
              :class="{ filled: otp[i] }"
              @input="onOtpInput(i)"
              @keydown.delete="onOtpDelete(i)"
              @paste="onOtpPaste"
            />
          </div>

          <p v-if="otpError" class="text-center text-xs text-danger font-medium">{{ otpError }}</p>

          <!-- Timer & Resend -->
          <div class="text-center">
            <p v-if="resendTimer > 0" class="text-sm text-text-light">
              إعادة إرسال الرمز بعد <span class="font-bold text-brand">{{ resendTimer }}</span> ثانية
            </p>
            <button
              v-else
              type="button"
              @click="resendOTP"
              class="text-sm text-blue font-medium hover:underline cursor-pointer"
            >
              إعادة إرسال الرمز
            </button>
          </div>

          <button
            type="submit"
            :disabled="isLoading || otp.join('').length < 4"
            class="w-full py-3.5 rounded-xl bg-blue text-white font-bold shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            <span v-if="!isLoading">تحقق</span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              جاري التحقق...
            </span>
          </button>
        </form>
      </div>

      <!-- ============ Step 3: New Password ============ -->
      <div v-else-if="step === 'reset'">
        <div class="text-center mb-8">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-success/10 flex items-center justify-center">
            <svg class="w-8 h-8 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
            </svg>
          </div>
          <h1 class="text-xl font-bold text-brand">كلمة مرور جديدة</h1>
          <p class="text-sm text-text-light mt-2">أدخل كلمة المرور الجديدة لحسابك</p>
        </div>

        <form @submit.prevent="resetPassword" class="space-y-4" novalidate>
          <div>
            <label class="block text-sm font-medium text-brand mb-1.5">كلمة المرور الجديدة</label>
            <div class="relative">
              <input
                v-model="newPassword"
                :type="showNewPass ? 'text' : 'password'"
                placeholder="6 أحرف على الأقل"
                class="w-full pr-4 pl-12 py-3 border-2 rounded-xl text-brand placeholder-gray-400 transition-colors focus:outline-none"
                :class="resetErrors.password ? 'border-danger' : 'border-border focus:border-blue'"
              />
              <button type="button" @click="showNewPass = !showNewPass" class="absolute inset-y-0 left-0 pl-3 flex items-center cursor-pointer" tabindex="-1">
                <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path v-if="!showNewPass" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                  <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M3 3l18 18"/>
                </svg>
              </button>
            </div>
            <p v-if="resetErrors.password" class="mt-1 text-xs text-danger font-medium">{{ resetErrors.password }}</p>
            <!-- Password strength -->
            <div v-if="newPassword" class="mt-2 flex gap-1">
              <div v-for="i in 4" :key="i" class="flex-1 h-1 rounded-full transition-colors"
                   :class="i <= passwordStrength ? strengthColor : 'bg-gray-200'"></div>
            </div>
            <p v-if="newPassword" class="text-xs mt-1" :class="strengthTextColor">{{ strengthLabel }}</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-brand mb-1.5">تأكيد كلمة المرور</label>
            <input
              v-model="confirmPassword"
              type="password"
              placeholder="أعد كتابة كلمة المرور"
              class="w-full px-4 py-3 border-2 rounded-xl text-brand placeholder-gray-400 transition-colors focus:outline-none"
              :class="resetErrors.confirm ? 'border-danger' : 'border-border focus:border-blue'"
            />
            <p v-if="resetErrors.confirm" class="mt-1 text-xs text-danger font-medium">{{ resetErrors.confirm }}</p>
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full py-3.5 rounded-xl bg-blue text-white font-bold shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            <span v-if="!isLoading">تعيين كلمة المرور</span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              جاري الحفظ...
            </span>
          </button>
        </form>
      </div>

      <!-- ============ Step 4: Success ============ -->
      <div v-else-if="step === 'success'" class="text-center">
        <div class="w-20 h-20 mx-auto mb-6 rounded-full bg-success/10 flex items-center justify-center">
          <svg class="w-10 h-10 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <h1 class="text-xl font-bold text-brand mb-2">تم التغيير بنجاح!</h1>
        <p class="text-sm text-text-light mb-8">تم تعيين كلمة المرور الجديدة. يمكنك الآن تسجيل الدخول.</p>
        <router-link
          to="/login"
          class="block w-full py-3.5 rounded-xl bg-blue text-white font-bold shadow-lg shadow-blue/25 hover:bg-blue-dark transition-all text-center"
        >
          تسجيل الدخول
        </router-link>
      </div>

    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { authApi, ApiException } from '../api/client'

const router = useRouter()

type Step = 'phone' | 'otp' | 'reset' | 'success'
const step = ref<Step>('phone')
const isLoading = ref(false)

// Step 1 — Phone
const phone = ref('')
const phoneError = ref('')

// Step 2 — OTP
const otp = reactive(['', '', '', ''])
const otpRefs: HTMLInputElement[] = []
const otpError = ref('')
const resendTimer = ref(0)
let timerInterval: ReturnType<typeof setInterval> | null = null

// Step 3 — Reset
const newPassword = ref('')
const confirmPassword = ref('')
const showNewPass = ref(false)
const resetErrors = reactive({ password: '', confirm: '' })
const resetToken = ref('')

const maskedPhone = computed(() => {
  if (phone.value.length >= 4) {
    return phone.value.slice(0, 4) + '****' + phone.value.slice(-2)
  }
  return phone.value
})

// Password strength
const passwordStrength = computed(() => {
  const p = newPassword.value
  let score = 0
  if (p.length >= 6) score++
  if (p.length >= 8) score++
  if (/[A-Z]/.test(p) && /[a-z]/.test(p)) score++
  if (/[0-9]/.test(p) && /[^A-Za-z0-9]/.test(p)) score++
  return score
})

const strengthColor = computed(() => {
  const colors = ['bg-danger', 'bg-warning', 'bg-blue', 'bg-success']
  return colors[passwordStrength.value - 1] || 'bg-gray-200'
})

const strengthTextColor = computed(() => {
  const colors = ['text-danger', 'text-warning', 'text-blue', 'text-success']
  return colors[passwordStrength.value - 1] || 'text-text-light'
})

const strengthLabel = computed(() => {
  const labels = ['ضعيفة', 'مقبولة', 'جيدة', 'قوية']
  return labels[passwordStrength.value - 1] || ''
})

function startResendTimer() {
  resendTimer.value = 60
  timerInterval = setInterval(() => {
    resendTimer.value--
    if (resendTimer.value <= 0 && timerInterval) {
      clearInterval(timerInterval)
    }
  }, 1000)
}

async function sendOTP() {
  phoneError.value = ''
  const cleaned = phone.value.replace(/\s/g, '')

  if (!cleaned) {
    phoneError.value = 'يرجى إدخال رقم الجوال'
    return
  }
  if (!/^05\d{8}$/.test(cleaned)) {
    phoneError.value = 'صيغة الرقم غير صحيحة (يجب أن يبدأ بـ 05 ويتكون من 10 أرقام)'
    return
  }

  isLoading.value = true
  try {
    await authApi.forgotPassword(cleaned)
    step.value = 'otp'
    startResendTimer()
    setTimeout(() => otpRefs[0]?.focus(), 100)
  } catch {
    // Always move to OTP step — backend returns 200 even if phone not found
    step.value = 'otp'
    startResendTimer()
    setTimeout(() => otpRefs[0]?.focus(), 100)
  }
  isLoading.value = false
}

function onOtpInput(index: number) {
  otpError.value = ''
  const val = otp[index]
  if (!/^\d$/.test(val)) {
    otp[index] = ''
    return
  }
  if (index < 3) {
    otpRefs[index + 1]?.focus()
  }
}

function onOtpDelete(index: number) {
  if (!otp[index] && index > 0) {
    otpRefs[index - 1]?.focus()
  }
}

function onOtpPaste(e: ClipboardEvent) {
  const data = e.clipboardData?.getData('text')?.replace(/\D/g, '').slice(0, 4)
  if (data && data.length === 4) {
    data.split('').forEach((d, i) => { otp[i] = d })
    otpRefs[3]?.focus()
    e.preventDefault()
  }
}

async function verifyOTP() {
  otpError.value = ''
  const code = otp.join('')

  if (code.length < 4) {
    otpError.value = 'يرجى إدخال الرمز كاملاً'
    return
  }

  isLoading.value = true
  try {
    const res = await authApi.verifyOtp(phone.value.replace(/\s/g, ''), code)
    resetToken.value = res.reset_token
    step.value = 'reset'
  } catch (err: any) {
    if (err instanceof ApiException) {
      if (err.status === 429) {
        otpError.value = 'تم تجاوز عدد المحاولات. أعد طلب رمز جديد.'
      } else {
        otpError.value = err.message || 'الرمز غير صحيح. يرجى المحاولة مرة أخرى.'
      }
    } else {
      otpError.value = 'حدث خطأ في الاتصال'
    }
  }
  isLoading.value = false
}

async function resendOTP() {
  isLoading.value = true
  try {
    await authApi.forgotPassword(phone.value.replace(/\s/g, ''))
  } catch { /* silent — same anti-enumeration */ }
  isLoading.value = false
  otp.fill('')
  otpError.value = ''
  startResendTimer()
  otpRefs[0]?.focus()
}

async function resetPassword() {
  resetErrors.password = ''
  resetErrors.confirm = ''

  if (!newPassword.value) {
    resetErrors.password = 'يرجى إدخال كلمة المرور الجديدة'
    return
  }
  if (newPassword.value.length < 6) {
    resetErrors.password = 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    resetErrors.confirm = 'كلمتا المرور غير متطابقتين'
    return
  }

  isLoading.value = true
  try {
    await authApi.resetPassword(resetToken.value, newPassword.value)
    step.value = 'success'
  } catch (err: any) {
    if (err instanceof ApiException) {
      resetErrors.password = err.message || 'حدث خطأ أثناء تغيير كلمة المرور'
    } else {
      resetErrors.password = 'حدث خطأ في الاتصال'
    }
  }
  isLoading.value = false
}

function goBack() {
  if (step.value === 'otp') {
    step.value = 'phone'
  } else if (step.value === 'reset') {
    step.value = 'otp'
  } else {
    router.push('/login')
  }
}

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
})
</script>
