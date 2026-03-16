<template>
  <div class="min-h-screen min-h-dvh bg-gradient-to-b from-white to-blue/5 flex flex-col">
    <!-- Header -->
    <header class="w-full px-4 pt-6 pb-2 flex justify-center">
      <div class="w-10 h-10 rounded-full bg-blue/10 flex items-center justify-center">
        <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
        </svg>
      </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col items-center justify-center px-6 pb-8">
      <!-- Logo -->
      <div class="mb-6 animate-fade-in">
        <img src="/logo.svg" alt="Jenan BIZ" class="h-24 sm:h-28 md:h-32 mx-auto drop-shadow-sm" />
      </div>

      <!-- Title & Description -->
      <div class="text-center max-w-sm mx-auto mb-10">
        <h1 class="text-2xl sm:text-3xl font-bold text-brand mb-3 leading-tight">
          نظام إدارة الأعمال المتكامل
        </h1>
        <p class="text-text-light text-sm sm:text-base leading-relaxed">
          أدِر أعمالك بكفاءة واحترافية. تتبّع المهام، الموظفين، الشركاء والعملاء من مكان واحد.
        </p>
      </div>

      <!-- CTA Buttons -->
      <div class="w-full max-w-xs space-y-3">
        <router-link
          to="/login"
          class="block w-full py-3.5 rounded-xl bg-blue text-white font-bold text-base text-center shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all duration-200"
        >
          تسجيل الدخول
        </router-link>

        <router-link
          to="/signup"
          class="block w-full py-3.5 rounded-xl bg-white text-brand font-bold text-base text-center border-2 border-border hover:border-blue hover:text-blue active:scale-[0.98] transition-all duration-200"
        >
          إنشاء حساب جديد
        </router-link>
      </div>

      <!-- Features hints -->
      <div class="mt-10 grid grid-cols-3 gap-4 max-w-sm w-full">
        <div class="text-center">
          <div class="w-11 h-11 mx-auto mb-2 rounded-xl bg-blue/10 flex items-center justify-center">
            <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
          </div>
          <p class="text-xs text-text-light font-medium">آمن وموثوق</p>
        </div>
        <div class="text-center">
          <div class="w-11 h-11 mx-auto mb-2 rounded-xl bg-blue/10 flex items-center justify-center">
            <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"/>
            </svg>
          </div>
          <p class="text-xs text-text-light font-medium">متوافق مع الجوال</p>
        </div>
        <div class="text-center">
          <div class="w-11 h-11 mx-auto mb-2 rounded-xl bg-blue/10 flex items-center justify-center">
            <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
            </svg>
          </div>
          <p class="text-xs text-text-light font-medium">تقارير وتحليلات</p>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="px-6 py-4 text-center">
      <p class="text-xs text-text-light/60">© {{ currentYear }} Jenan BIZ — جميع الحقوق محفوظة</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
const currentYear = new Date().getFullYear()
</script>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.6s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
