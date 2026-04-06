<template>
  <div class="min-h-screen min-h-dvh bg-bg">
    <!-- Top bar -->
    <header class="bg-white border-b border-border sticky top-0 z-30">
      <div class="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <img src="/logo.svg" alt="Jenan BIZ" class="h-8" />
          <span class="text-xs font-bold bg-blue/10 text-blue px-2 py-0.5 rounded-lg">المالك</span>
        </div>
        <div class="flex items-center gap-3">
          <NotificationBell />
          <span class="text-sm text-text-light hidden sm:inline">{{ userName }}</span>
          <button @click="showChangePass = true" class="text-text-light hover:text-blue transition-colors cursor-pointer p-1" title="تغيير كلمة المرور">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/>
            </svg>
          </button>
          <button @click="handleLogout" class="text-text-light hover:text-danger transition-colors cursor-pointer p-1">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-6xl mx-auto px-4 pb-8">
      <!-- Welcome -->
      <div class="mt-6 mb-6">
        <h1 class="text-2xl font-bold text-brand">مرحبًا {{ userName }} 👋</h1>
        <p class="text-sm text-text-light mt-1">لوحة التحليلات المتقدمة — إدارة النظام بالكامل</p>
      </div>

      <!-- Primary KPIs -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div class="bg-white rounded-2xl border border-border p-4 text-center">
          <div class="w-10 h-10 mx-auto mb-2 rounded-xl bg-blue/10 flex items-center justify-center">
            <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
          </div>
          <p class="text-2xl font-bold text-brand">{{ analytics.total_requests }}</p>
          <p class="text-xs text-text-light mt-0.5">إجمالي الطلبات</p>
        </div>
        <div class="bg-white rounded-2xl border border-border p-4 text-center">
          <div class="w-10 h-10 mx-auto mb-2 rounded-xl bg-success/10 flex items-center justify-center">
            <svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <p class="text-2xl font-bold text-success">{{ analytics.eligibility_rate }}%</p>
          <p class="text-xs text-text-light mt-0.5">نسبة الأهلية</p>
        </div>
        <div class="bg-white rounded-2xl border border-border p-4 text-center">
          <div class="w-10 h-10 mx-auto mb-2 rounded-xl bg-danger/10 flex items-center justify-center">
            <svg class="w-5 h-5 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"/></svg>
          </div>
          <p class="text-2xl font-bold text-danger">{{ analytics.rejection_rate }}%</p>
          <p class="text-xs text-text-light mt-0.5">نسبة الرفض</p>
        </div>
        <div class="bg-white rounded-2xl border border-border p-4 text-center">
          <div class="w-10 h-10 mx-auto mb-2 rounded-xl bg-warning/10 flex items-center justify-center">
            <svg class="w-5 h-5 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <p class="text-2xl font-bold text-warning">{{ formatHours(analytics.avg_processing_hours) }}</p>
          <p class="text-xs text-text-light mt-0.5">متوسط وقت المعالجة</p>
        </div>
      </div>

      <!-- Financial KPIs -->
      <h2 class="text-lg font-bold text-brand mb-3">المؤشرات المالية</h2>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <div class="bg-gradient-to-br from-blue/5 to-blue/10 rounded-2xl border border-blue/20 p-5">
          <p class="text-xs text-text-light mb-1">إجمالي حجم نقاط البيع</p>
          <p class="text-xl font-bold text-brand">{{ formatCurrency(analytics.total_pos_volume) }}</p>
          <p class="text-[10px] text-text-light mt-1">ريال سعودي</p>
        </div>
        <div class="bg-gradient-to-br from-success/5 to-success/10 rounded-2xl border border-success/20 p-5">
          <p class="text-xs text-text-light mb-1">إجمالي التمويل المتوقع</p>
          <p class="text-xl font-bold text-success">{{ formatCurrency(analytics.expected_total_financing) }}</p>
          <p class="text-[10px] text-text-light mt-1">ريال سعودي</p>
        </div>
        <div class="bg-gradient-to-br from-warning/5 to-warning/10 rounded-2xl border border-warning/20 p-5">
          <p class="text-xs text-text-light mb-1">طلبات هذا الشهر</p>
          <div class="flex items-baseline gap-3 mt-1">
            <span class="text-lg font-bold text-brand">{{ analytics.new_this_month }} <span class="text-xs font-normal text-text-light">جديد</span></span>
            <span class="text-lg font-bold text-success">{{ analytics.completed_this_month }} <span class="text-xs font-normal text-text-light">مكتمل</span></span>
            <span class="text-lg font-bold text-danger">{{ analytics.rejected_this_month }} <span class="text-xs font-normal text-text-light">مرفوض</span></span>
          </div>
        </div>
      </div>

      <!-- Entity Distribution + Decisions -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        <div class="bg-white rounded-2xl border border-border p-5">
          <h3 class="text-sm font-bold text-brand mb-4">توزيع الجهات التمويلية</h3>
          <div v-if="Object.keys(analytics.entity_distribution).length > 0" class="space-y-3">
            <div v-for="(count, entity) in analytics.entity_distribution" :key="entity" class="flex items-center gap-3">
              <span class="text-xs text-text-light w-24 text-left truncate">{{ entity }}</span>
              <div class="flex-1 h-6 bg-bg rounded-full overflow-hidden">
                <div class="h-full bg-blue/60 rounded-full transition-all duration-500 flex items-center justify-end pr-2" :style="{ width: entityPercent(count) + '%' }">
                  <span class="text-[10px] text-white font-bold" v-if="entityPercent(count) > 15">{{ count }}</span>
                </div>
              </div>
              <span class="text-xs font-bold text-brand w-8 text-left">{{ count }}</span>
            </div>
          </div>
          <p v-else class="text-xs text-text-light text-center py-6">لا توجد بيانات بعد</p>
        </div>

        <div class="bg-white rounded-2xl border border-border p-5">
          <h3 class="text-sm font-bold text-brand mb-4">ملخص القرارات</h3>
          <div class="grid grid-cols-2 gap-3">
            <div class="bg-success/5 rounded-xl p-3 text-center">
              <p class="text-xl font-bold text-success">{{ analytics.auto_approved_count }}</p>
              <p class="text-[10px] text-text-light mt-0.5">موافقة تلقائية</p>
            </div>
            <div class="bg-warning/5 rounded-xl p-3 text-center">
              <p class="text-xl font-bold text-warning">{{ analytics.manual_review_count }}</p>
              <p class="text-[10px] text-text-light mt-0.5">مراجعة يدوية</p>
            </div>
            <div class="bg-blue/5 rounded-xl p-3 text-center">
              <p class="text-xl font-bold text-blue">{{ analytics.overridden_count }}</p>
              <p class="text-[10px] text-text-light mt-0.5">قرارات المالك</p>
            </div>
            <div class="bg-danger/5 rounded-xl p-3 text-center">
              <p class="text-xl font-bold text-danger">{{ analytics.high_risk_count }}</p>
              <p class="text-[10px] text-text-light mt-0.5">مخاطر عالية</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Pending Partners -->
      <div v-if="pendingPartners.length > 0" class="mb-6">
        <h2 class="text-lg font-bold text-brand mb-3 flex items-center gap-2">
          طلبات تسجيل شركاء جدد
          <span class="text-sm font-bold bg-warning/15 text-warning px-2 py-0.5 rounded-lg">{{ pendingPartners.length }}</span>
        </h2>
        <div class="space-y-3">
          <div v-for="p in pendingPartners" :key="p.id"
            class="bg-white rounded-2xl border border-warning/30 p-4 flex items-center justify-between gap-4">
            <div>
              <p class="font-bold text-brand text-sm">{{ p.name }}</p>
              <p class="text-xs text-text-light mt-0.5" dir="ltr">{{ p.phone }}</p>
            </div>
            <div class="flex gap-2 flex-shrink-0">
              <button @click="approvePartner(p.id)"
                class="text-xs font-bold text-success bg-success/10 px-3 py-2 rounded-lg hover:bg-success/20 transition-colors cursor-pointer">
                قبول
              </button>
              <button @click="rejectPartner(p.id)"
                class="text-xs font-bold text-danger bg-danger/10 px-3 py-2 rounded-lg hover:bg-danger/20 transition-colors cursor-pointer">
                رفض
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Cases Section -->
      <div class="flex items-center justify-between mb-3 mt-2">
        <h2 class="text-lg font-bold text-brand">الطلبات</h2>
        <div class="flex items-center gap-2">
          <!-- Bulk delete button -->
          <button
            v-if="selectedCaseIds.size > 0"
            @click="bulkDeleteCases"
            :disabled="bulkDeleting"
            class="flex items-center gap-1.5 text-xs font-bold text-danger bg-danger/10 px-3 py-1.5 rounded-lg hover:bg-danger/20 transition-colors cursor-pointer disabled:opacity-50"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
            {{ bulkDeleting ? 'جارٍ...' : `حذف (${selectedCaseIds.size})` }}
          </button>
          <button @click="exportCasesCSV"
            class="flex items-center gap-1.5 text-xs font-bold text-success bg-success/10 px-3 py-1.5 rounded-lg hover:bg-success/20 transition-colors cursor-pointer">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            تصدير CSV
          </button>
        </div>
      </div>

      <!-- Cases Tabs -->
      <div class="flex gap-1 bg-white rounded-xl border border-border p-1 overflow-x-auto mb-3">
        <button
          v-for="tab in caseTabs"
          :key="tab.key"
          @click="caseTab = tab.key"
          class="flex-1 min-w-[80px] py-2.5 px-3 rounded-lg text-xs font-bold text-center transition-all cursor-pointer whitespace-nowrap"
          :class="caseTab === tab.key ? 'bg-blue text-white shadow-sm' : 'text-text-light hover:bg-bg'"
        >
          {{ tab.label }}
          <span class="inline-block mr-1 min-w-[18px] h-[18px] leading-[18px] rounded-full text-[10px] text-center"
            :class="caseTab === tab.key ? 'bg-white/20' : 'bg-gray-200'">
            {{ tab.count }}
          </span>
        </button>
      </div>

      <!-- Cases loading -->
      <div v-if="casesLoading" class="bg-white rounded-2xl border border-border p-6 text-center mb-6">
        <svg class="animate-spin w-7 h-7 mx-auto text-blue" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
        </svg>
        <p class="text-sm text-text-light mt-2">جاري تحميل الطلبات...</p>
      </div>

      <!-- Select all bar -->
      <div v-if="!casesLoading && filteredOwnerCases.length > 0" class="flex items-center gap-3 bg-white rounded-xl border border-border px-4 py-2.5 mb-2">
        <input
          type="checkbox"
          :checked="allSelected"
          @change="toggleSelectAll"
          class="w-4 h-4 accent-blue cursor-pointer rounded"
        />
        <span class="text-xs text-text-light flex-1">
          {{ selectedCaseIds.size > 0 ? `تم تحديد ${selectedCaseIds.size} من ${filteredOwnerCases.length}` : 'تحديد الكل' }}
        </span>
        <button v-if="selectedCaseIds.size > 0" @click="selectedCaseIds = new Set()" class="text-xs text-text-light hover:text-danger cursor-pointer">إلغاء</button>
      </div>

      <!-- Cases list -->
      <div v-if="!casesLoading" class="space-y-2 mb-6">
        <div v-if="filteredOwnerCases.length === 0" class="bg-white rounded-2xl border border-border p-8 text-center">
          <p class="text-sm text-text-light">لا توجد طلبات</p>
        </div>

        <div
          v-for="c in filteredOwnerCases"
          :key="c.id"
          class="bg-white rounded-2xl border p-4 text-right transition-all"
          :class="selectedCaseIds.has(c.id) ? 'border-danger/40 bg-danger/2' : 'border-border hover:border-blue/30 hover:shadow-sm'"
        >
          <div class="flex items-start gap-3">
            <!-- Checkbox -->
            <div class="flex-shrink-0 pt-0.5" @click.stop>
              <input
                type="checkbox"
                :checked="selectedCaseIds.has(c.id)"
                @change="toggleSelectCase(c.id)"
                class="w-4 h-4 accent-danger cursor-pointer rounded"
              />
            </div>
            <!-- Content -->
            <div class="flex-1 min-w-0 cursor-pointer" @click="openCase(c.id)">
              <div class="flex items-start justify-between gap-3">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1 flex-wrap">
                    <span class="text-xs font-mono text-text-light">{{ c.display_id }}</span>
                    <span v-if="!c.assigned_to" class="text-[10px] font-bold bg-warning/10 text-warning px-1.5 py-0.5 rounded">غير معيّن</span>
                  </div>
                  <p class="font-bold text-brand text-sm truncate">{{ c.company_name || '—' }}</p>
                  <div class="flex items-center gap-3 mt-1 text-xs text-text-light flex-wrap">
                    <span>المنتج: <span class="font-mono text-brand">{{ c.offer_code || '—' }}</span></span>
                    <span v-if="c.entity_name" class="font-medium text-blue">{{ c.entity_name }}</span>
                  </div>
                </div>
                <div class="flex flex-col items-end gap-1.5 flex-shrink-0">
                  <span class="inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium"
                    :class="[stageConf(c.stage).bgColor, stageConf(c.stage).color]">
                    {{ stageConf(c.stage).label }}
                  </span>
                  <span class="text-[10px] text-text-light">{{ formatDate(c.updated_at) }}</span>
                </div>
              </div>
              <div class="mt-2.5">
                <div class="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all"
                    :class="c.stage === 'rejected' ? 'bg-danger' : 'bg-blue'"
                    :style="{ width: stageProgress(c.stage) + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Navigation Cards -->
      <h2 class="text-lg font-bold text-brand mb-4">الأقسام</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <router-link to="/supervisor" class="group bg-white rounded-2xl border border-border p-5 hover:border-blue/40 hover:shadow-md transition-all">
          <div class="w-12 h-12 rounded-xl bg-warning/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
          </div>
          <h3 class="text-base font-bold text-brand mb-1">لوحة المشرف</h3>
          <p class="text-xs text-text-light leading-relaxed">مؤشرات الأداء (KPIs)، توزيع المراحل، قائمة الطلبات</p>
        </router-link>

        <router-link to="/owner/entities" class="group bg-white rounded-2xl border border-border p-5 hover:border-blue/40 hover:shadow-md transition-all">
          <div class="w-12 h-12 rounded-xl bg-blue/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
          </div>
          <h3 class="text-base font-bold text-brand mb-1">إعدادات الجهات</h3>
          <p class="text-xs text-text-light leading-relaxed">إدارة أولويات الجهات التمويلية (Smart Routing)</p>
        </router-link>

        <router-link to="/owner/users" class="group bg-white rounded-2xl border border-border p-5 hover:border-blue/40 hover:shadow-md transition-all">
          <div class="w-12 h-12 rounded-xl bg-success/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
          </div>
          <h3 class="text-base font-bold text-brand mb-1">إدارة المستخدمين</h3>
          <p class="text-xs text-text-light leading-relaxed">إنشاء وتعديل الحسابات والأدوار</p>
        </router-link>

        <router-link to="/owner/contacts" class="group bg-white rounded-2xl border border-border p-5 hover:border-blue/40 hover:shadow-md transition-all">
          <div class="w-12 h-12 rounded-xl bg-blue/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/></svg>
          </div>
          <h3 class="text-base font-bold text-brand mb-1">جهات الاتصال</h3>
          <p class="text-xs text-text-light leading-relaxed">قاعدة العملاء والتواصل عبر WhatsApp</p>
        </router-link>

        <router-link to="/owner/campaigns" class="group bg-white rounded-2xl border border-border p-5 hover:border-blue/40 hover:shadow-md transition-all">
          <div class="w-12 h-12 rounded-xl bg-danger/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z"/></svg>
          </div>
          <h3 class="text-base font-bold text-brand mb-1">الحملات التسويقية</h3>
          <p class="text-xs text-text-light leading-relaxed">حملات WhatsApp الجماعية وتتبع النتائج</p>
        </router-link>

        <router-link to="/employee" class="group bg-white rounded-2xl border border-border p-5 hover:border-blue/40 hover:shadow-md transition-all">
          <div class="w-12 h-12 rounded-xl bg-text-light/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-text-light" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
          </div>
          <h3 class="text-base font-bold text-brand mb-1">عرض الموظف</h3>
          <p class="text-xs text-text-light leading-relaxed">معاينة لوحة الموظف</p>
        </router-link>

        <router-link to="/owner/entity-contacts" class="group bg-white rounded-2xl border border-border p-5 hover:border-blue/40 hover:shadow-md transition-all">
          <div class="w-12 h-12 rounded-xl bg-blue/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
          </div>
          <h3 class="text-base font-bold text-brand mb-1">موظفو الجهات</h3>
          <p class="text-xs text-text-light leading-relaxed">جهات الاتصال في كل جهة تمويلية</p>
        </router-link>

        <router-link to="/owner/brokers" class="group bg-white rounded-2xl border border-border p-5 hover:border-blue/40 hover:shadow-md transition-all">
          <div class="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/></svg>
          </div>
          <h3 class="text-base font-bold text-brand mb-1">سجل الوسطاء</h3>
          <p class="text-xs text-text-light leading-relaxed">قاعدة بيانات الوسطاء والوكلاء</p>
        </router-link>

        <router-link to="/owner/businesses" class="group bg-white rounded-2xl border border-border p-5 hover:border-blue/40 hover:shadow-md transition-all">
          <div class="w-12 h-12 rounded-xl bg-success/10 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
          </div>
          <h3 class="text-base font-bold text-brand mb-1">سجل المنشآت</h3>
          <p class="text-xs text-text-light leading-relaxed">قاعدة بيانات المنشآت التجارية</p>
        </router-link>

        <router-link to="/owner/employee-stats" class="group bg-white rounded-2xl border border-border p-5 hover:border-blue/40 hover:shadow-md transition-all">
          <div class="w-12 h-12 rounded-xl bg-amber-100 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
            <svg class="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
          </div>
          <h3 class="text-base font-bold text-brand mb-1">إحصائيات الموظفين</h3>
          <p class="text-xs text-text-light leading-relaxed">أداء الموظفين بناءً على الملفات المعالجة</p>
        </router-link>
      </div>
    </main>

    <ChangePasswordModal v-model="showChangePass" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { currentUser, logout } from '../../stores/authStore'
import { casesApi, usersApi } from '../../api/client'
import type { CaseResponse } from '../../api/client'
import { STAGE_MAP, getStageProgress } from '../../types/stages'
import type { RequestStage } from '../../types/stages'
import NotificationBell from '../../components/NotificationBell.vue'
import ChangePasswordModal from '../../components/ChangePasswordModal.vue'

const router = useRouter()
const userName = computed(() => currentUser.value?.name ?? 'المالك')

// ─── Cases list ───────────────────────────────────────
type CaseTabKey = 'all' | 'completing_request' | 'pending_approval' | 'rejected'
const caseTab = ref<CaseTabKey>('all')
const casesLoading = ref(true)
const cases = ref<CaseResponse[]>([])

async function loadCases() {
  casesLoading.value = true
  try {
    const resp = await casesApi.list({ size: 200 })
    cases.value = resp.items
  } catch { /* silent */ }
  casesLoading.value = false
}

const pendingApproval = computed(() =>
  cases.value.filter(c => (c.approvals || []).some((a: any) => a.status === 'pending'))
)
const completing = computed(() =>
  cases.value.filter(c => c.stage === 'completing_request')
)
const rejected = computed(() =>
  cases.value.filter(c => c.stage === 'rejected')
)

const caseTabs = computed(() => [
  { key: 'all' as CaseTabKey, label: 'الكل', count: cases.value.length },
  { key: 'completing_request' as CaseTabKey, label: 'استكمال', count: completing.value.length },
  { key: 'pending_approval' as CaseTabKey, label: 'يحتاج اعتماد', count: pendingApproval.value.length },
  { key: 'rejected' as CaseTabKey, label: 'مرفوض', count: rejected.value.length },
])

const filteredOwnerCases = computed(() => {
  switch (caseTab.value) {
    case 'completing_request': return completing.value
    case 'pending_approval': return pendingApproval.value
    case 'rejected': return rejected.value
    default: return cases.value
  }
})

function stageConf(stage: string) { return STAGE_MAP[stage as RequestStage] ?? STAGE_MAP['analyzing'] }
function stageProgress(stage: string) { return getStageProgress(stage as RequestStage) }

async function exportCasesCSV() {
  try {
    // Fetch all cases in batches (max 500 per request)
    const allRows: CaseResponse[] = []
    let page = 1
    while (true) {
      const resp = await casesApi.list({ size: 500, page })
      allRows.push(...resp.items)
      if (allRows.length >= resp.total || resp.items.length === 0) break
      page++
    }
    const rows = allRows
    const header = ['رقم الطلب', 'اسم المنشأة', 'السجل التجاري', 'نوع الكيان', 'الشريك', 'المرحلة', 'المنتج', 'الأهلية', 'تاريخ التقديم']
    const lines = [header.join(','), ...rows.map(c => [
      `"${c.display_id ?? ''}"`  ,
      `"${(c.company_name ?? '').replace(/"/g, '""')}"`  ,
      `"${c.registration_number ?? ''}"`,
      `"${c.entity_type ?? ''}"`,
      `"${(c.partner_name ?? '').replace(/"/g, '""')}"`,
      `"${stageConf(c.stage)?.label ?? c.stage}"`,
      `"${c.offer_code ?? ''}"`,
      `"${c.is_eligible ? 'مؤهل' : 'غير مؤهل'}"`,
      `"${c.created_at ? new Date(/[Zz]|[+\-]\d{2}:?\d{2}$/.test(c.created_at) ? c.created_at : c.created_at + 'Z').toLocaleDateString('ar-SA') : ''}"`
    ].join(','))]
    const blob = new Blob(['\uFEFF' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `طلبات_${new Date().toLocaleDateString('ar-SA').replace(/\//g, '-')}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } catch { /* silent */ }
}
function formatDate(iso: string) {
  const s = /[Zz]|[+\-]\d{2}:?\d{2}$/.test(iso) ? iso : iso + 'Z'
  return new Date(s).toLocaleDateString('ar-SA', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function openCase(id: string) { router.push(`/case/${id}`) }

// ─── Bulk select/delete cases ───────────────────────────────────────────────────────────
const selectedCaseIds = ref<Set<string>>(new Set())
const bulkDeleting = ref(false)

const allSelected = computed(() =>
  filteredOwnerCases.value.length > 0 &&
  filteredOwnerCases.value.every(c => selectedCaseIds.value.has(c.id))
)

function toggleSelectCase(id: string) {
  if (selectedCaseIds.value.has(id)) selectedCaseIds.value.delete(id)
  else selectedCaseIds.value.add(id)
  selectedCaseIds.value = new Set(selectedCaseIds.value) // trigger reactivity
}

function toggleSelectAll() {
  if (allSelected.value) {
    selectedCaseIds.value = new Set()
  } else {
    selectedCaseIds.value = new Set(filteredOwnerCases.value.map(c => c.id))
  }
}

async function bulkDeleteCases() {
  if (selectedCaseIds.value.size === 0) return
  if (!confirm(`هل تريد حذف ${selectedCaseIds.value.size} طلب نهائياً؟ لا يمكن التراجع عن هذا الإجراء.`)) return
  bulkDeleting.value = true
  const ids = [...selectedCaseIds.value]
  await Promise.allSettled(ids.map(id => casesApi.deleteCase(id)))
  selectedCaseIds.value = new Set()
  bulkDeleting.value = false
  await loadCases()
}

const analytics = ref({
  total_requests: 0,
  eligibility_rate: 0,
  entity_distribution: {} as Record<string, number>,
  rejection_rate: 0,
  avg_processing_hours: 0,
  total_pos_volume: 0,
  expected_total_financing: 0,
  completed_this_month: 0,
  rejected_this_month: 0,
  new_this_month: 0,
  overridden_count: 0,
  high_risk_count: 0,
  auto_approved_count: 0,
  manual_review_count: 0,
})

onMounted(async () => {
  loadCases()
  loadPendingPartners()
  try {
    const data = await casesApi.getOwnerAnalytics()
    Object.assign(analytics.value, data)
  } catch {
    // Silently fail — demo may not have API running
  }
})

function formatCurrency(val: number): string {
  if (!val) return '0'
  if (val >= 1_000_000) return (val / 1_000_000).toFixed(1) + 'M'
  if (val >= 1_000) return (val / 1_000).toFixed(0) + 'K'
  return val.toFixed(0)
}

function formatHours(h: number): string {
  if (!h) return '0 س'
  if (h < 1) return Math.round(h * 60) + ' د'
  if (h < 24) return h.toFixed(1) + ' س'
  return (h / 24).toFixed(1) + ' ي'
}

function entityPercent(count: number): number {
  const total = Object.values(analytics.value.entity_distribution).reduce((a, b) => a + b, 0)
  return total > 0 ? Math.round((count / total) * 100) : 0
}

function handleLogout() {
  logout()
  router.push('/')
}

// ─── Pending Partners ─────────────────────────────────────
const pendingPartners = ref<any[]>([])
const pendingLoading = ref(false)

async function loadPendingPartners() {
  pendingLoading.value = true
  try {
    const resp = await usersApi.listPending()
    pendingPartners.value = resp.items
  } catch { /* silent */ }
  pendingLoading.value = false
}

async function approvePartner(userId: string) {
  try {
    await usersApi.approveUser(userId)
    await loadPendingPartners()
  } catch { /* silent */ }
}

async function rejectPartner(userId: string) {
  if (!confirm('هل تريد رفض طلب التسجيل هذا؟')) return
  try {
    await usersApi.rejectUser(userId)
    await loadPendingPartners()
  } catch { /* silent */ }
}

const showChangePass = ref(false)
</script>

