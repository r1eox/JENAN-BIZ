<template>
  <div class="min-h-screen min-h-dvh bg-bg">
    <!-- Top bar -->
    <header class="bg-white border-b border-border sticky top-0 z-30">
      <div class="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
        <button @click="goBack" class="flex items-center gap-1.5 text-text-light hover:text-brand transition-colors cursor-pointer p-1">
          <svg class="w-5 h-5 rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
          <span class="text-sm">رجوع</span>
        </button>
        <span class="text-sm font-bold text-brand">تفاصيل الطلب</span>
        <span class="text-xs text-text-light font-mono">{{ caseData?.display_id || caseId }}</span>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="max-w-3xl mx-auto px-4 py-16 text-center">
      <svg class="animate-spin w-10 h-10 mx-auto text-blue" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
      </svg>
      <p class="text-sm text-text-light mt-3">جاري تحميل البيانات...</p>
    </div>

    <main v-else-if="caseData" class="max-w-3xl mx-auto px-4 pb-8">
      <!-- Stage indicator -->
      <div class="mt-4 bg-white rounded-2xl border border-border p-4">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-sm font-bold text-brand">المرحلة الحالية</h2>
          <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold" :class="[currentStageConfig.bgColor, currentStageConfig.color]">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="currentStageConfig.icon"/>
            </svg>
            {{ currentStageConfig.label }}
          </span>
        </div>

        <!-- Step progress -->
        <div class="flex items-center gap-1">
          <div v-for="(s, i) in STAGES_ORDER" :key="s"
            class="flex-1 h-2 rounded-full transition-colors"
            :class="getStageIndex(caseData.stage as RequestStage) >= i ? 'bg-blue' : caseData.stage === 'rejected' ? 'bg-danger/20' : 'bg-gray-200'"
          ></div>
        </div>
        <div class="flex justify-between mt-1">
          <span class="text-[9px] text-text-light">التحليل</span>
          <span class="text-[9px] text-text-light">الأتعاب</span>
        </div>
      </div>

      <!-- Info cards -->
      <div class="mt-4 grid grid-cols-2 gap-3">
        <div class="bg-white rounded-xl border border-border p-3">
          <p class="text-xs text-text-light">المنشأة</p>
          <p class="text-sm font-bold text-brand mt-0.5">{{ caseData.company_name || '—' }}</p>
        </div>
        <div class="bg-white rounded-xl border border-border p-3">
          <p class="text-xs text-text-light">السجل التجاري</p>
          <p class="text-sm font-bold text-brand mt-0.5" dir="ltr">{{ caseData.registration_number || '—' }}</p>
        </div>
        <div class="bg-white rounded-xl border border-border p-3">
          <p class="text-xs text-text-light">نوع الكيان</p>
          <p class="text-sm font-bold text-brand mt-0.5">{{ caseData.entity_type || '—' }}</p>
        </div>
        <div class="bg-white rounded-xl border border-border p-3">
          <p class="text-xs text-text-light">عمر المنشأة</p>
          <p class="text-sm font-bold text-brand mt-0.5">{{ caseData.age_in_months }} شهر</p>
        </div>
        <div class="bg-white rounded-xl border border-border p-3">
          <p class="text-xs text-text-light">الشريك</p>
          <p class="text-sm font-bold text-brand mt-0.5">{{ caseData.partner_name || caseData.partner_id }}</p>
        </div>
        <div class="bg-white rounded-xl border border-border p-3">
          <p class="text-xs text-text-light">المنتج / الجهة</p>
          <p class="text-sm font-bold mt-0.5" :class="showEntityName ? 'text-success' : 'text-brand'">
            {{ showEntityName ? (caseData.entity_name || caseData.offer_code) : caseData.offer_code }}
          </p>
          <p v-if="showEntityName && caseData.entity_name" class="text-[10px] text-success">(ظاهر للمدير فقط)</p>
        </div>
      </div>

      <!-- Assignment info -->
      <div v-if="role !== 'partner'" class="mt-4 bg-white rounded-xl border border-border p-3 flex items-center justify-between">
        <div>
          <p class="text-xs text-text-light">معيّن إلى</p>
          <p class="text-sm font-bold text-brand">{{ caseData.assigned_to_name || (caseData.assigned_to ? caseData.assigned_to : 'غير معيّن') }}</p>
        </div>
        <div>
          <p class="text-xs text-text-light">SLA</p>
          <p class="text-sm font-bold" :class="caseSLA > 48 ? 'text-danger' : caseSLA > 24 ? 'text-warning' : 'text-success'">
            {{ caseSLA }}h
          </p>
        </div>
      </div>

      <!-- ═══ Financial Data (Employee/Supervisor/Owner) ═══ -->
      <div v-if="role !== 'partner' && (caseData.analysis_result?.total_credit || caseData.analysis_result?.total_debit)" class="mt-4 bg-white rounded-2xl border border-border p-4">
        <div class="flex items-center gap-2 mb-3">
          <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 11h.01M12 11h.01M15 11h.01M4 19h16a2 2 0 002-2V7a2 2 0 00-2-2H4a2 2 0 00-2 2v10a2 2 0 002 2z"/>
          </svg>
          <h3 class="text-sm font-bold text-brand">البيانات المالية</h3>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div class="bg-bg rounded-xl p-3 text-center">
            <p class="text-[10px] text-text-light mb-1">مجموع الدائن</p>
            <p class="text-sm font-bold text-success" dir="ltr">{{ Number(caseData.analysis_result?.total_credit || 0).toLocaleString('en-US') }} ر.س</p>
          </div>
          <div class="bg-bg rounded-xl p-3 text-center">
            <p class="text-[10px] text-text-light mb-1">مجموع المدين</p>
            <p class="text-sm font-bold text-danger" dir="ltr">{{ Number(caseData.analysis_result?.total_debit || 0).toLocaleString('en-US') }} ر.س</p>
          </div>
          <div v-if="caseData.analysis_result?.pos_sales" class="bg-bg rounded-xl p-3 text-center">
            <p class="text-[10px] text-text-light mb-1">مبيعات POS</p>
            <p class="text-sm font-bold text-brand" dir="ltr">{{ Number(caseData.analysis_result?.pos_sales || 0).toLocaleString('en-US') }} ر.س</p>
          </div>
          <div v-if="caseData.analysis_result?.other_income" class="bg-bg rounded-xl p-3 text-center">
            <p class="text-[10px] text-text-light mb-1">إيرادات أخرى</p>
            <p class="text-sm font-bold text-brand" dir="ltr">{{ Number(caseData.analysis_result?.other_income || 0).toLocaleString('en-US') }} ر.س</p>
          </div>
          <div class="bg-blue/5 rounded-xl p-3 text-center col-span-2">
            <p class="text-[10px] text-text-light mb-1">صافي الدائن - المدين</p>
            <p class="text-sm font-bold" :class="(caseData.analysis_result?.total_credit||0) >= (caseData.analysis_result?.total_debit||0) ? 'text-success' : 'text-danger'" dir="ltr">
              {{ Number((caseData.analysis_result?.total_credit||0) - (caseData.analysis_result?.total_debit||0)).toLocaleString('en-US') }} ر.س
            </p>
          </div>
        </div>
      </div>

      <!-- ═══ Risk Flags (Supervisor/Owner) ═══ -->
      <div v-if="role !== 'partner' && riskFlags.length > 0" class="mt-4 bg-white rounded-2xl border border-border p-4">
        <div class="flex items-center gap-2 mb-3">
          <svg class="w-5 h-5 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <h3 class="text-sm font-bold text-danger">علامات المخاطر ({{ riskFlags.length }})</h3>
        </div>
        <div class="space-y-2">
          <div v-for="(flag, idx) in riskFlags" :key="idx"
            class="flex items-start gap-2 p-2.5 rounded-lg"
            :class="flag.level === 'high' ? 'bg-danger/5 border border-danger/20' : flag.level === 'medium' ? 'bg-warning/5 border border-warning/20' : 'bg-blue/5 border border-blue/20'"
          >
            <span class="text-[10px] font-bold px-1.5 py-0.5 rounded mt-0.5"
              :class="flag.level === 'high' ? 'bg-danger/10 text-danger' : flag.level === 'medium' ? 'bg-warning/10 text-warning' : 'bg-blue/10 text-blue'"
            >{{ flag.level === 'high' ? 'عالي' : flag.level === 'medium' ? 'متوسط' : 'منخفض' }}</span>
            <div>
              <p class="text-xs font-bold text-brand">{{ flag.title_ar }}</p>
              <p class="text-xs text-text-light mt-0.5">{{ flag.detail_ar }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Files with download -->
      <div class="mt-4 bg-white rounded-xl border border-border p-4">
        <h3 class="text-sm font-bold text-brand mb-2">الملفات</h3>
        <div class="space-y-2">
          <div v-if="caseData.cr_file_name" class="flex items-center justify-between bg-bg rounded-lg p-2.5">
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
              <span class="text-xs text-brand">{{ caseData.cr_file_name }}</span>
            </div>
            <button @click="downloadFile('cr')" class="text-xs font-bold text-blue hover:underline cursor-pointer">تحميل</button>
          </div>
          <div v-if="caseData.bs_file_name" class="flex items-center justify-between bg-bg rounded-lg p-2.5">
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/>
              </svg>
              <span class="text-xs text-brand">{{ caseData.bs_file_name }}</span>
            </div>
            <button @click="downloadFile('bs')" class="text-xs font-bold text-blue hover:underline cursor-pointer">تحميل</button>
          </div>
          <p v-if="!caseData.cr_file_name && !caseData.bs_file_name" class="text-xs text-text-light">لا توجد ملفات مرفقة</p>

          <!-- Basic docs uploaded in wizard step 6 (stored in supplementary_docs with type=basic_doc) -->
          <template v-if="basicDocs.length > 0">
            <p class="text-xs font-bold text-brand mt-3 mb-1.5">المستندات الأساسية ({{ basicDocs.length }})</p>
            <div v-for="doc in basicDocs" :key="doc.stored_name"
              class="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg p-2.5">
              <div class="flex items-center gap-2">
                <svg class="w-4 h-4 text-success flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                <div>
                  <p class="text-xs text-brand font-medium">{{ doc.label }}</p>
                  <p class="text-[10px] text-text-light">{{ doc.original_name }}</p>
                </div>
              </div>
              <button @click="downloadSupDoc(doc)" class="text-xs font-bold text-blue hover:underline cursor-pointer">تحميل</button>
            </div>
          </template>

          <!-- Supplementary docs from partner completing_request stage -->
          <template v-if="completionDocs.length > 0">
            <p class="text-xs font-bold text-brand mt-3 mb-1.5">مستندات الاستكمال ({{ completionDocs.length }})</p>
            <div v-for="doc in completionDocs" :key="doc.stored_name"
              class="flex items-center justify-between bg-blue/5 border border-blue/15 rounded-lg p-2.5">
              <div class="flex items-center gap-2">
                <svg class="w-4 h-4 text-blue flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                <div>
                  <p class="text-xs text-brand font-medium">{{ doc.label }}</p>
                  <p class="text-[10px] text-text-light">{{ doc.original_name }}</p>
                </div>
              </div>
              <span class="text-[10px] text-text-light">{{ doc.size ? Math.round(doc.size/1024) + ' KB' : '' }}</span>
              <button @click="downloadSupDoc(doc)" class="text-xs font-bold text-blue hover:underline cursor-pointer">تحميل</button>
            </div>
          </template>
        </div>
      </div>

      <!-- Result summary (skip internal PDF-review message) -->
      <div v-if="caseData.result_summary && !caseData.result_summary.includes('تعذّر التحليل')" class="mt-4 rounded-xl p-3 text-sm font-medium"
        :class="
          caseData.stage === 'rejected' || caseData.result_summary.includes('غير مؤهل')
            ? 'bg-danger/5 text-danger border border-danger/20'
            : caseData.result_summary.includes('مراجعة') || caseData.result_summary.includes('تحتاج')
              ? 'bg-warning/5 text-warning border border-warning/20'
              : 'bg-success/5 text-success border border-success/20'
        ">
        {{ caseData.result_summary }}
      </div>

      <!-- ═══ Employee/Supervisor Actions ═══ -->
      <div v-if="role !== 'partner' && caseData.stage !== 'rejected' && caseData.stage !== 'fees_received'" class="mt-4 bg-white rounded-2xl border border-border p-4">
        <h3 class="text-sm font-bold text-brand mb-3">إجراءات</h3>

        <div class="flex flex-wrap gap-2">
          <!-- Claim (employee, if unassigned) -->
          <button
            v-if="role === 'employee' && !caseData.assigned_to"
            @click="doClaim"
            class="text-xs font-bold text-blue bg-blue/10 px-3 py-2 rounded-lg hover:bg-blue/20 transition-colors cursor-pointer"
          >
            استلام الطلب
          </button>

          <!-- Advance stage -->
          <button
            v-if="nextStage && (role === 'supervisor' || role === 'owner' || (role === 'employee' && !isGatedStage(nextStage)))"
            @click="doAdvance"
            :disabled="actionLoading"
            class="text-xs font-bold text-success bg-success/10 px-3 py-2 rounded-lg hover:bg-success/20 transition-colors cursor-pointer disabled:opacity-50"
          >
            نقل لـ: {{ STAGE_MAP[nextStage].label }}
          </button>

          <!-- Propose gated stage (employee) -->
          <button
            v-if="nextStage && isGatedStage(nextStage) && role === 'employee'"
            @click="showProposeModal = true"
            class="text-xs font-bold text-warning bg-warning/10 px-3 py-2 rounded-lg hover:bg-warning/20 transition-colors cursor-pointer"
          >
            طلب اعتماد: {{ STAGE_MAP[nextStage].label }}
          </button>

          <!-- Request completion from partner -->
          <button
            v-if="role !== 'partner'"
            @click="showCompletionModal = true"
            class="text-xs font-bold text-brand bg-brand/10 px-3 py-2 rounded-lg hover:bg-brand/20 transition-colors cursor-pointer"
          >
            طلب استكمال من الشريك
          </button>

          <!-- Reject (supervisor/owner) -->
          <button
            v-if="(role === 'supervisor' || role === 'owner') && caseData.stage !== 'fees_received'"
            @click="showRejectModal = true"
            class="text-xs font-bold text-danger bg-danger/10 px-3 py-2 rounded-lg hover:bg-danger/20 transition-colors cursor-pointer"
          >
            رفض الطلب
          </button>

          <!-- Send to entity (supervisor/owner) -->
          <button
            v-if="(role === 'supervisor' || role === 'owner') && !['analyzing','rejected','fees_received','submitted'].includes(caseData.stage)"
            @click="showSubmitEntityModal = true"
            class="text-xs font-bold text-blue bg-blue/10 px-3 py-2 rounded-lg hover:bg-blue/20 transition-colors cursor-pointer"
          >
            ✉️ إرسال للجهة التمويلية
          </button>
        </div>
      </div>

      <!-- ═══ Owner Override ═══ -->
      <div v-if="role === 'owner' && caseData.stage !== 'fees_received'" class="mt-4 bg-white rounded-2xl border-2 border-success/30 p-4">
        <div class="flex items-center gap-2 mb-3">
          <svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
          </svg>
          <h3 class="text-sm font-bold text-success">تجاوز القرار (صلاحية المدير)</h3>
        </div>
        <div v-if="caseData.is_overridden" class="bg-success/5 rounded-xl p-3 mb-3">
          <p class="text-xs text-success font-bold">تم تجاوز القرار: {{ caseData.override_decision }}</p>
          <p class="text-xs text-text-light mt-1">السبب: {{ caseData.override_reason }}</p>
        </div>
        <div class="flex gap-2">
          <button @click="showOverrideModal = true" class="text-xs font-bold text-success bg-success/10 px-4 py-2 rounded-lg hover:bg-success/20 cursor-pointer">
            {{ caseData.is_overridden ? 'تعديل التجاوز' : 'تجاوز القرار' }}
          </button>
        </div>
      </div>

      <!-- ═══ Internal Notes (not for partner) ═══ -->
      <div v-if="role !== 'partner'" class="mt-4 bg-white rounded-2xl border border-border p-4">
        <h3 class="text-sm font-bold text-brand mb-3">الملاحظات الداخلية</h3>

        <div v-if="(caseData.notes || []).length === 0" class="text-xs text-text-light py-3 text-center">لا توجد ملاحظات</div>

        <div v-else class="space-y-2 mb-3 max-h-60 overflow-y-auto">
          <div v-for="note in caseData.notes" :key="note.id" class="bg-bg rounded-xl p-3">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-xs font-bold text-brand">{{ note.author_name || note.user_id }}</span>
              <span class="text-[10px] text-text-light mr-auto">{{ fmtDate(note.created_at) }}</span>
            </div>
            <p class="text-xs text-brand leading-relaxed">{{ note.note }}</p>
          </div>
        </div>

        <!-- Add note form -->
        <div class="flex gap-2">
          <input
            v-model="newNote"
            type="text"
            placeholder="أضف ملاحظة داخلية..."
            class="flex-1 border-2 border-border rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-blue"
            @keydown.enter="doAddNote"
          />
          <button
            @click="doAddNote"
            :disabled="!newNote.trim() || actionLoading"
            class="px-4 py-2 rounded-xl bg-blue text-white text-xs font-bold hover:bg-blue-dark transition-colors disabled:opacity-50 cursor-pointer"
          >إضافة</button>
        </div>
      </div>

      <!-- ═══ Stage History (Audit Log) ═══ -->
      <div class="mt-4 bg-white rounded-2xl border border-border p-4">
        <h3 class="text-sm font-bold text-brand mb-3">
          سجل المراحل
          <span v-if="role !== 'partner'" class="text-[10px] text-text-light font-normal">(سجل التدقيق)</span>
        </h3>

        <div class="relative pr-4">
          <!-- Timeline line -->
          <div class="absolute right-1.5 top-0 bottom-0 w-0.5 bg-border"></div>

          <div v-for="(entry, idx) in (caseData.stage_history || [])" :key="entry.id || idx" class="relative pb-4 last:pb-0">
            <!-- Timeline dot -->
            <div class="absolute right-0 top-1 w-3 h-3 rounded-full border-2 z-10"
              :class="idx === (caseData.stage_history || []).length - 1 ? 'bg-blue border-blue' : 'bg-white border-border'"
            ></div>

            <div class="mr-5">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-xs font-bold" :class="stageConf(entry.stage || entry.to_stage).color">
                  {{ stageConf(entry.stage || entry.to_stage).label }}
                </span>
                <span v-if="role !== 'partner' && entry.changed_by" class="text-[10px] text-text-light">
                  بواسطة: {{ entry.changed_by }}
                </span>
              </div>
              <p v-if="entry.note" class="text-xs text-text-light mt-0.5">{{ entry.note }}</p>
              <p class="text-[10px] text-text-light/60 mt-0.5">{{ fmtDate(entry.created_at || entry.timestamp) }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Partner-only: pending completion -->
      <div v-if="role === 'partner' && caseData.stage === 'completing_request'" class="mt-4 bg-warning/5 border border-warning/30 rounded-2xl p-4">
        <div class="flex items-start gap-3 mb-3">
          <div class="w-9 h-9 rounded-xl bg-warning/20 flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
          </div>
          <div class="flex-1">
            <h3 class="text-sm font-bold text-warning">مطلوب استكمال الطلب</h3>
            <p class="text-xs text-warning/80 mt-0.5 leading-relaxed">يرجى رفع المستندات المطلوبة لاستكمال طلبك.</p>
          </div>
        </div>

        <!-- Required docs specified by staff -->
        <div v-if="(caseData.completion_required_docs || []).length > 0" class="mb-3 bg-white rounded-xl p-3">
          <p class="text-xs font-bold text-brand mb-2">المستندات المطلوبة منك:</p>
          <ul class="space-y-1">
            <li v-for="doc in (caseData.completion_required_docs || [])" :key="doc"
              class="text-xs text-text-light flex items-center gap-1.5">
              <svg class="w-3 h-3 text-warning flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clip-rule="evenodd"/>
              </svg>
              {{ doc }}
            </li>
          </ul>
        </div>

        <button
          @click="router.push(`/partner/documents/${caseData.id}`)"
          class="w-full py-3 rounded-xl bg-warning text-white text-sm font-bold flex items-center justify-center gap-2 hover:bg-yellow-500 active:scale-[0.98] transition-all cursor-pointer"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
          </svg>
          استكمال الطلب — رفع المستندات
        </button>
      </div>
    </main>

    <!-- Not found -->
    <div v-else-if="!loading" class="max-w-3xl mx-auto px-4 py-16 text-center">
      <p class="text-sm text-text-light">الطلب غير موجود</p>
      <button @click="goBack" class="mt-4 text-sm text-blue font-bold hover:underline cursor-pointer">العودة</button>
    </div>

    <!-- ═══ Modals ═══ -->

    <!-- Propose stage approval modal -->
    <Teleport to="body">
      <div v-if="showProposeModal" class="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center" @click.self="showProposeModal = false">
        <div class="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-5">
          <h3 class="text-base font-bold text-brand mb-3">طلب اعتماد انتقال مرحلة</h3>
          <p class="text-xs text-text-light mb-3">المرحلة المطلوبة: <span class="font-bold text-blue">{{ nextStage ? STAGE_MAP[nextStage].label : '' }}</span></p>
          <textarea v-model="proposeNote" rows="2" placeholder="ملاحظة (اختياري)..." class="w-full border-2 border-border rounded-xl p-3 text-sm focus:outline-none focus:border-blue resize-none"></textarea>
          <div class="flex gap-2 mt-4">
            <button @click="showProposeModal = false" class="flex-1 py-2.5 rounded-xl border-2 border-border text-sm font-bold text-text-light cursor-pointer">إلغاء</button>
            <button @click="doPropose" :disabled="actionLoading" class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-bold cursor-pointer disabled:opacity-50">إرسال الطلب</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Request completion modal -->
    <Teleport to="body">
      <div v-if="showCompletionModal" class="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center" @click.self="showCompletionModal = false">
        <div class="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-5 max-h-[90vh] overflow-y-auto">
          <h3 class="text-base font-bold text-brand mb-1">طلب استكمال من الشريك</h3>
          <p class="text-xs text-text-light mb-3">اختر المستندات المطلوبة من الشريك</p>

          <!-- Preset doc checkboxes -->
          <div class="grid grid-cols-2 gap-2 mb-3">
            <label
              v-for="doc in PRESET_DOCS"
              :key="doc"
              class="flex items-center gap-2 text-xs cursor-pointer border-2 rounded-xl px-3 py-2 transition-colors"
              :class="selectedDocs.includes(doc) ? 'border-blue bg-blue/5 text-blue font-bold' : 'border-border text-text-light'"
            >
              <input type="checkbox" :value="doc" v-model="selectedDocs" class="hidden" />
              <span class="w-4 h-4 rounded border-2 flex items-center justify-center flex-shrink-0 transition-colors"
                :class="selectedDocs.includes(doc) ? 'border-blue bg-blue' : 'border-gray-300'">
                <svg v-if="selectedDocs.includes(doc)" class="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
                </svg>
              </span>
              {{ doc }}
            </label>
          </div>

          <!-- Custom doc input -->
          <div class="flex gap-2 mb-3">
            <input v-model="customDoc" type="text" placeholder="مستند آخر (اكتب واضغط +)..."
              class="flex-1 border-2 border-border rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-blue"
              @keydown.enter="addCustomDoc" />
            <button @click="addCustomDoc" class="px-3 py-2 rounded-xl bg-blue/10 text-blue font-bold text-sm hover:bg-blue/20 cursor-pointer">+</button>
          </div>

          <!-- Selected docs chips -->
          <div v-if="selectedDocs.length" class="flex flex-wrap gap-1.5 mb-3">
            <span v-for="doc in selectedDocs" :key="doc"
              class="inline-flex items-center gap-1 bg-blue/10 text-blue text-xs font-bold px-2.5 py-1 rounded-full">
              {{ doc }}
              <button @click="selectedDocs = selectedDocs.filter(d => d !== doc)" class="hover:text-danger cursor-pointer">×</button>
            </span>
          </div>

          <!-- Optional note -->
          <textarea v-model="completionNote" rows="2" placeholder="ملاحظة إضافية (اختياري)..." class="w-full border-2 border-border rounded-xl p-3 text-sm focus:outline-none focus:border-blue resize-none"></textarea>

          <div class="flex gap-2 mt-4">
            <button @click="showCompletionModal = false" class="flex-1 py-2.5 rounded-xl border-2 border-border text-sm font-bold text-text-light cursor-pointer">إلغاء</button>
            <button @click="doRequestCompletion" :disabled="!selectedDocs.length || actionLoading" class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-bold disabled:opacity-50 cursor-pointer">إرسال</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Submit to entity modal -->
    <Teleport to="body">
      <div v-if="showSubmitEntityModal" class="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center" @click.self="showSubmitEntityModal = false">
        <div class="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-5">
          <h3 class="text-base font-bold text-blue mb-1">إرسال الطلب للجهة التمويلية</h3>
          <p class="text-xs text-text-light mb-3">سيتم تسجيل هذا الإجراء في سجل الطلب وإشعار الشريك.</p>
          <textarea v-model="submitEntityNote" rows="2" placeholder="ملاحظة إضافية (اختياري)..." class="w-full border-2 border-border rounded-xl p-3 text-sm focus:outline-none focus:border-blue resize-none"></textarea>
          <div class="flex gap-2 mt-4">
            <button @click="showSubmitEntityModal = false" class="flex-1 py-2.5 rounded-xl border-2 border-border text-sm font-bold text-text-light cursor-pointer">إلغاء</button>
            <button @click="doSubmitToEntity" :disabled="actionLoading" class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-bold disabled:opacity-50 cursor-pointer">تأكيد الإرسال</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Reject modal -->
    <Teleport to="body">
      <div v-if="showRejectModal" class="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center" @click.self="showRejectModal = false">
        <div class="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-5">
          <h3 class="text-base font-bold text-danger mb-3">رفض الطلب</h3>
          <textarea v-model="rejectReason" rows="3" placeholder="سبب الرفض (مطلوب)..." class="w-full border-2 border-border rounded-xl p-3 text-sm focus:outline-none focus:border-danger resize-none"></textarea>
          <div class="flex gap-2 mt-4">
            <button @click="showRejectModal = false" class="flex-1 py-2.5 rounded-xl border-2 border-border text-sm font-bold text-text-light cursor-pointer">إلغاء</button>
            <button @click="doReject" :disabled="!rejectReason.trim() || actionLoading" class="flex-1 py-2.5 rounded-xl bg-danger text-white text-sm font-bold disabled:opacity-50 cursor-pointer">تأكيد الرفض</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Override modal (owner only) -->
    <Teleport to="body">
      <div v-if="showOverrideModal" class="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center" @click.self="showOverrideModal = false">
        <div class="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-5">
          <h3 class="text-base font-bold text-success mb-3">تجاوز القرار</h3>
          <div class="mb-3">
            <label class="block text-xs font-bold text-brand mb-1.5">القرار الجديد</label>
            <select v-model="overrideDecision" class="w-full border-2 border-border rounded-xl p-3 text-sm focus:outline-none focus:border-success">
              <option value="">اختر...</option>
              <option value="approved">موافقة</option>
              <option value="rejected">رفض</option>
              <option value="refer_to_review">إحالة للمراجعة</option>
            </select>
          </div>
          <textarea v-model="overrideReason" rows="3" placeholder="سبب التجاوز (مطلوب)..." class="w-full border-2 border-border rounded-xl p-3 text-sm focus:outline-none focus:border-success resize-none"></textarea>
          <div class="flex gap-2 mt-4">
            <button @click="showOverrideModal = false" class="flex-1 py-2.5 rounded-xl border-2 border-border text-sm font-bold text-text-light cursor-pointer">إلغاء</button>
            <button @click="doOverride" :disabled="!overrideDecision || !overrideReason.trim() || actionLoading" class="flex-1 py-2.5 rounded-xl bg-success text-white text-sm font-bold disabled:opacity-50 cursor-pointer">تأكيد التجاوز</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { currentUser, canSeeEntityNames } from '../../stores/authStore'
import { casesApi, analysisApi } from '../../api/client'
import type { CaseResponse } from '../../api/client'
import {
  STAGE_MAP,
  STAGES_ORDER,
  getStageIndex,
  getNextStage,
  isGatedStage,
} from '../../types/stages'
import type { RequestStage } from '../../types/stages'

const router = useRouter()
const route = useRoute()
const caseId = route.params.id as string

const loading = ref(true)
const actionLoading = ref(false)
const caseData = ref<CaseResponse | null>(null)

const role = computed(() => (currentUser.value?.role ?? 'partner') as string)
const showEntityName = computed(() => canSeeEntityNames())
const currentStageConfig = computed(() => STAGE_MAP[(caseData.value?.stage as RequestStage) ?? 'analyzing'])
const nextStage = computed<RequestStage | null>(() => caseData.value ? getNextStage(caseData.value.stage as RequestStage) : null)

function stageConf(stage: string) { return STAGE_MAP[stage as RequestStage] ?? STAGE_MAP['analyzing'] }

const caseSLA = computed(() => {
  if (!caseData.value) return 0
  const ms = Date.now() - new Date(caseData.value.last_stage_change_at || caseData.value.updated_at).getTime()
  return Math.floor(ms / 3600000)
})

const riskFlags = computed(() => {
  const c = caseData.value as any
  // risk_flags live inside analysis_result JSON, not at the top-level response field
  return c?.analysis_result?.risk_flags || c?.risk_flags || []
})

// Split supplementary_docs into basic docs (wizard step 6) and completion docs
const basicDocs = computed(() =>
  (caseData.value?.supplementary_docs || []).filter((d: any) => d.type === 'basic_doc')
)
const completionDocs = computed(() =>
  (caseData.value?.supplementary_docs || []).filter((d: any) => d.type !== 'basic_doc')
)

async function loadCase() {
  loading.value = true
  try {
    caseData.value = await casesApi.get(caseId)
  } catch {
    caseData.value = null
  }
  loading.value = false
}

onMounted(loadCase)

// Notes
const newNote = ref('')
async function doAddNote() {
  if (!newNote.value.trim() || actionLoading.value) return
  actionLoading.value = true
  try {
    await casesApi.addNote(caseId, newNote.value.trim())
    newNote.value = ''
    await loadCase()
  } catch { /* silent */ }
  actionLoading.value = false
}

// Claim
async function doClaim() {
  actionLoading.value = true
  try {
    await casesApi.claim(caseId)
    await loadCase()
  } catch { /* silent */ }
  actionLoading.value = false
}

// Advance stage
async function doAdvance() {
  if (!nextStage.value || actionLoading.value) return
  actionLoading.value = true
  try {
    await casesApi.advance(caseId)
    await loadCase()
  } catch { /* silent */ }
  actionLoading.value = false
}

// Propose gated stage
const showProposeModal = ref(false)
const proposeNote = ref('')
async function doPropose() {
  if (!nextStage.value || actionLoading.value) return
  actionLoading.value = true
  try {
    await casesApi.propose(caseId, nextStage.value, proposeNote.value.trim())
    showProposeModal.value = false
    proposeNote.value = ''
    await loadCase()
  } catch { /* silent */ }
  actionLoading.value = false
}

// Request completion
const showCompletionModal = ref(false)
const completionNote = ref('')
const selectedDocs = ref<string[]>([])
const customDoc = ref('')

const PRESET_DOCS = [
  'صورة الهوية الوطنية',
  'كشف الحساب البنكي',
  'السجل التجاري',
  'عقد الإيجار',
  'وثيقة ملكية العقار',
  'شهادة الزكاة والدخل',
  'رخصة البلدية',
  'ضريبة القيمة المضافة',
  'عقد التأسيس',
  'فواتير المبيعات',
]

function addCustomDoc() {
  const val = customDoc.value.trim()
  if (val && !selectedDocs.value.includes(val)) {
    selectedDocs.value.push(val)
  }
  customDoc.value = ''
}

async function doRequestCompletion() {
  if (!selectedDocs.value.length || actionLoading.value) return
  actionLoading.value = true
  try {
    await casesApi.requestCompletion(caseId, completionNote.value.trim(), selectedDocs.value)
    showCompletionModal.value = false
    completionNote.value = ''
    selectedDocs.value = []
    await loadCase()
  } catch { /* silent */ }
  actionLoading.value = false
}

// Submit to entity
const showSubmitEntityModal = ref(false)
const submitEntityNote = ref('')
async function doSubmitToEntity() {
  if (actionLoading.value) return
  actionLoading.value = true
  try {
    await casesApi.submitToEntity(caseId, submitEntityNote.value.trim())
    showSubmitEntityModal.value = false
    submitEntityNote.value = ''
    await loadCase()
  } catch { /* silent */ }
  actionLoading.value = false
}

// Reject
const showRejectModal = ref(false)
const rejectReason = ref('')
async function doReject() {
  if (!rejectReason.value.trim() || actionLoading.value) return
  actionLoading.value = true
  try {
    await casesApi.reject(caseId, rejectReason.value.trim())
    showRejectModal.value = false
    rejectReason.value = ''
    await loadCase()
  } catch { /* silent */ }
  actionLoading.value = false
}

// Override (Owner only)
const showOverrideModal = ref(false)
const overrideDecision = ref('')
const overrideReason = ref('')
async function doOverride() {
  if (!overrideDecision.value || !overrideReason.value.trim() || actionLoading.value) return
  actionLoading.value = true
  try {
    await casesApi.overrideDecision(caseId, overrideDecision.value, overrideReason.value.trim())
    showOverrideModal.value = false
    overrideDecision.value = ''
    overrideReason.value = ''
    await loadCase()
  } catch { /* silent */ }
  actionLoading.value = false
}

// File download
async function downloadFile(type: 'cr' | 'bs') {
  try {
    const blob = await casesApi.downloadFile(caseId, type)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = type === 'cr' ? (caseData.value?.cr_file_name || 'cr.pdf') : (caseData.value?.bs_file_name || 'bs.xlsx')
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  } catch { /* silent */ }
}

// Supplementary doc download
async function downloadSupDoc(doc: any) {
  try {
    await analysisApi.downloadDoc(caseId, doc.stored_name, doc.original_name)
  } catch { /* silent */ }
}

// Basic docs download
async function downloadBasicDoc(docName: string, docInfo: any) {
  try {
    const originalName = typeof docInfo === 'object' ? (docInfo?.original_name || docName) : String(docInfo)
    await analysisApi.downloadBasicDoc(caseId, docName, originalName)
  } catch { /* silent */ }
}

function fmtDate(iso: string): string {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('ar-SA', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function goBack() {
  const r = role.value
  if (r === 'employee') router.push('/employee')
  else if (r === 'supervisor') router.push('/supervisor')
  else if (r === 'owner') router.push('/owner')
  else router.push('/partner')
}
</script>
