<template>
  <div class="min-h-screen min-h-dvh bg-bg flex items-center justify-center p-4">
    <div class="text-center max-w-md">
      <div class="w-20 h-20 mx-auto mb-5 rounded-2xl bg-danger/10 flex items-center justify-center">
        <svg class="w-10 h-10 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.832c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/>
        </svg>
      </div>
      <h1 class="text-3xl font-bold text-brand mb-2">404</h1>
      <p class="text-text-light mb-6">الصفحة المطلوبة غير موجودة</p>
      <router-link
        to="/"
        class="inline-flex items-center gap-2 bg-blue text-white text-sm font-semibold px-6 py-3 rounded-xl hover:bg-blue/90 transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
        </svg>
        العودة للرئيسية
      </router-link>
    </div>
  </div>
</template>
