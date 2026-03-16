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
      <!-- Pending approval success card -->
      <div v-if="registered" class="text-center py-4">
        <div class="w-20 h-20 mx-auto mb-5 rounded-full bg-warning/10 flex items-center justify-center">
          <svg class="w-10 h-10 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <h2 class="text-xl font-bold text-brand mb-2">تم استلام طلبك!</h2>
        <p class="text-sm text-text-light leading-relaxed mb-6">
          حسابك في انتظار موافقة الإدارة.<br/>
          سيتم إشعارك عبر التطبيق عند تفعيل حسابك.
        </p>
        <router-link to="/login"
          class="inline-block px-8 py-3 rounded-xl bg-blue text-white font-bold text-sm hover:bg-blue-dark transition-colors">
          العودة لتسجيل الدخول
        </router-link>
      </div>

      <!-- Header -->
      <template v-else>
      <div class="text-center mb-6">
        <img src="/logo.svg" alt="Jenan BIZ" class="h-14 mx-auto mb-3" />
        <h1 class="text-xl font-bold text-brand">إنشاء حساب جديد</h1>
        <p class="text-sm text-text-light mt-1">أدخل بياناتك لإنشاء حسابك</p>
      </div>

      <form @submit.prevent="handleSignup" class="space-y-4" novalidate>
        <!-- Full Name -->
        <div>
          <label class="block text-sm font-medium text-brand mb-1.5">الاسم الكامل</label>
          <div class="relative">
            <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
            </div>
            <input
              v-model="form.name"
              type="text"
              autocomplete="name"
              placeholder="مثال: محمد أحمد"
              class="w-full pr-10 pl-4 py-3 border-2 rounded-xl text-brand placeholder-gray-400 transition-colors focus:outline-none"
              :class="errors.name ? 'border-danger' : 'border-border focus:border-blue'"
              @input="errors.name = ''"
            />
          </div>
          <p v-if="errors.name" class="mt-1 text-xs text-danger font-medium">{{ errors.name }}</p>
        </div>

        <!-- Phone -->
        <div>
          <label class="block text-sm font-medium text-brand mb-1.5">رقم الجوال</label>
          <div class="relative">
            <div class="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
              </svg>
            </div>
            <input
              v-model="form.phone"
              type="tel"
              inputmode="numeric"
              dir="ltr"
              autocomplete="tel"
              placeholder="05xxxxxxxx"
              class="w-full pr-10 pl-4 py-3 border-2 rounded-xl text-brand placeholder-gray-400 transition-colors focus:outline-none text-left"
              :class="errors.phone ? 'border-danger' : 'border-border focus:border-blue'"
              @input="errors.phone = ''"
            />
          </div>
          <p v-if="errors.phone" class="mt-1 text-xs text-danger font-medium">{{ errors.phone }}</p>
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
              autocomplete="new-password"
              placeholder="6 أحرف على الأقل"
              class="w-full pr-10 pl-12 py-3 border-2 rounded-xl text-brand placeholder-gray-400 transition-colors focus:outline-none"
              :class="errors.password ? 'border-danger' : 'border-border focus:border-blue'"
              @input="errors.password = ''"
            />
            <button type="button" @click="showPass = !showPass" class="absolute inset-y-0 left-0 pl-3 flex items-center cursor-pointer" tabindex="-1">
              <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path v-if="!showPass" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M3 3l18 18"/>
              </svg>
            </button>
          </div>
          <p v-if="errors.password" class="mt-1 text-xs text-danger font-medium">{{ errors.password }}</p>
          <!-- Password strength indicator -->
          <div v-if="form.password" class="mt-2">
            <div class="flex gap-1">
              <div v-for="i in 4" :key="i" class="flex-1 h-1 rounded-full transition-colors"
                   :class="i <= passwordStrength ? strengthColor : 'bg-gray-200'"></div>
            </div>
            <p class="text-xs mt-1" :class="strengthTextColor">{{ strengthLabel }}</p>
          </div>
        </div>

        <!-- Confirm Password -->
        <div>
          <label class="block text-sm font-medium text-brand mb-1.5">تأكيد كلمة المرور</label>
          <input
            v-model="form.confirmPassword"
            type="password"
            autocomplete="new-password"
            placeholder="أعد كتابة كلمة المرور"
            class="w-full px-4 py-3 border-2 rounded-xl text-brand placeholder-gray-400 transition-colors focus:outline-none"
            :class="errors.confirmPassword ? 'border-danger' : 'border-border focus:border-blue'"
            @input="errors.confirmPassword = ''"
          />
          <p v-if="errors.confirmPassword" class="mt-1 text-xs text-danger font-medium">{{ errors.confirmPassword }}</p>
        </div>

        <!-- Terms checkbox -->
        <div class="flex items-start gap-2.5">
          <input
            v-model="form.agreeTerms"
            type="checkbox"
            id="terms"
            class="mt-1 w-4.5 h-4.5 rounded border-gray-300 text-blue focus:ring-blue cursor-pointer flex-shrink-0"
          />
          <label for="terms" class="text-sm text-text-light leading-relaxed cursor-pointer">
            أوافق على
            <button type="button" @click="showTerms = true" class="text-blue font-medium hover:underline cursor-pointer">الشروط والأحكام</button>
            و<button type="button" @click="showTerms = true" class="text-blue font-medium hover:underline cursor-pointer">سياسة الخصوصية</button>
          </label>
        </div>
        <p v-if="errors.terms" class="text-xs text-danger font-medium -mt-2">{{ errors.terms }}</p>

        <!-- Error banner -->
        <div v-if="signupError" class="flex items-start gap-2 bg-danger/5 border border-danger/20 rounded-xl p-3">
          <svg class="w-5 h-5 text-danger flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <p class="text-sm text-danger">{{ signupError }}</p>
        </div>

        <!-- Submit -->
        <button
          type="submit"
          :disabled="isLoading"
          class="w-full py-3.5 rounded-xl bg-blue text-white font-bold text-base shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          <span v-if="!isLoading">إنشاء الحساب</span>
          <span v-else class="flex items-center justify-center gap-2">
            <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            جاري إنشاء الحساب...
          </span>
        </button>
      </form>

      <!-- Divider -->
      <div class="flex items-center gap-3 my-5">
        <div class="flex-1 h-px bg-border"></div>
        <span class="text-xs text-text-light">لديك حساب؟</span>
        <div class="flex-1 h-px bg-border"></div>
      </div>

      <router-link
        to="/login"
        class="block w-full py-3 rounded-xl bg-white text-brand font-bold text-base text-center border-2 border-border hover:border-blue hover:text-blue active:scale-[0.98] transition-all duration-200"
      >
        تسجيل الدخول
      </router-link>
      </template>
    </main>

    <!-- Terms Modal -->
    <Teleport to="body">
      <div v-if="showTerms" class="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/40" @click.self="showTerms = false">
        <div class="bg-white rounded-t-2xl sm:rounded-2xl w-full max-w-md max-h-[80vh] flex flex-col shadow-2xl">
          <div class="flex items-center justify-between p-4 border-b border-border">
            <h2 class="text-lg font-bold text-brand">الشروط والأحكام</h2>
            <button @click="showTerms = false" class="text-text-light hover:text-brand cursor-pointer p-1">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <div class="overflow-y-auto p-4 text-sm text-text-light leading-relaxed space-y-3">
            <p>مرحباً بك في نظام Jenan BIZ. باستخدامك لهذا النظام، فإنك توافق على الشروط التالية:</p>
            <h3 class="font-bold text-brand">1. الاستخدام المسؤول</h3>
            <p>يلتزم المستخدم باستخدام النظام بشكل قانوني ومسؤول وعدم إساءة استخدام أي من خدماته.</p>
            <h3 class="font-bold text-brand">2. حماية البيانات</h3>
            <p>نلتزم بحماية بياناتك الشخصية وعدم مشاركتها مع أي طرف ثالث دون إذنك.</p>
            <h3 class="font-bold text-brand">3. كلمة المرور</h3>
            <p>أنت مسؤول عن الحفاظ على سرية كلمة المرور الخاصة بك وعن جميع الأنشطة التي تتم تحت حسابك.</p>
            <h3 class="font-bold text-brand">4. الخصوصية</h3>
            <p>يتم تشفير جميع البيانات الحساسة ولا يتم تخزين كلمات المرور بشكل نصي.</p>
          </div>
          <div class="p-4 border-t border-border">
            <button
              @click="form.agreeTerms = true; showTerms = false"
              class="w-full py-3 rounded-xl bg-blue text-white font-bold hover:bg-blue-dark transition-colors cursor-pointer"
            >
              موافق
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '../stores/authStore'

const router = useRouter()
const showPass = ref(false)
const isLoading = ref(false)
const signupError = ref('')
const showTerms = ref(false)
const registered = ref(false)

const form = reactive({
  name: '',
  phone: '',
  password: '',
  confirmPassword: '',
  agreeTerms: false,
})

const errors = reactive({
  name: '',
  phone: '',
  password: '',
  confirmPassword: '',
  terms: '',
})

// Password strength
const passwordStrength = computed(() => {
  const p = form.password
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

function validate(): boolean {
  let valid = true
  errors.name = ''
  errors.phone = ''
  errors.password = ''
  errors.confirmPassword = ''
  errors.terms = ''

  if (!form.name.trim()) {
    errors.name = 'يرجى إدخال الاسم الكامل'
    valid = false
  } else if (form.name.trim().length < 3) {
    errors.name = 'الاسم يجب أن يكون 3 أحرف على الأقل'
    valid = false
  }

  const cleanPhone = form.phone.replace(/\s/g, '')
  if (!cleanPhone) {
    errors.phone = 'يرجى إدخال رقم الجوال'
    valid = false
  } else if (!/^05\d{8}$/.test(cleanPhone)) {
    errors.phone = 'صيغة الرقم غير صحيحة (يجب أن يبدأ بـ 05 ويتكون من 10 أرقام)'
    valid = false
  }

  if (!form.password) {
    errors.password = 'يرجى إدخال كلمة المرور'
    valid = false
  } else if (form.password.length < 6) {
    errors.password = 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'
    valid = false
  }

  if (!form.confirmPassword) {
    errors.confirmPassword = 'يرجى تأكيد كلمة المرور'
    valid = false
  } else if (form.password !== form.confirmPassword) {
    errors.confirmPassword = 'كلمتا المرور غير متطابقتين'
    valid = false
  }

  if (!form.agreeTerms) {
    errors.terms = 'يجب الموافقة على الشروط والأحكام'
    valid = false
  }

  return valid
}

async function handleSignup() {
  signupError.value = ''
  if (!validate()) return

  isLoading.value = true
  try {
    await register(form.name.trim(), form.phone.replace(/\s/g, ''), form.password)
    // Show pending approval message instead of redirecting
    registered.value = true
  } catch (err: any) {
    if (err?.status === 409) {
      signupError.value = 'رقم الجوال مستخدم بالفعل. جرّب تسجيل الدخول'
    } else if (err?.message) {
      signupError.value = err.message
    } else {
      signupError.value = 'تعذر الاتصال بالخادم. تأكد من اتصال الإنترنت'
    }
  } finally {
    isLoading.value = false
  }
}
</script>
