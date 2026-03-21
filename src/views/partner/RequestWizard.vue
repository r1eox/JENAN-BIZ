<template>
  <div class="min-h-screen min-h-dvh bg-bg">
    <!-- Top bar -->
    <header class="bg-white border-b border-border sticky top-0 z-30">
      <div class="max-w-lg mx-auto px-4 h-14 flex items-center justify-between">
        <button @click="goBack" class="flex items-center gap-1.5 text-text-light hover:text-brand transition-colors cursor-pointer p-1">
          <svg class="w-5 h-5 rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
          <span class="text-sm">رجوع</span>
        </button>
        <span class="text-sm font-bold text-brand">طلب جديد</span>
        <span class="text-xs text-text-light">{{ caseDisplayId || '' }}</span>
      </div>
    </header>

    <main class="max-w-lg mx-auto px-4 pb-8">
      <!-- Step indicator -->
      <div class="mt-4 mb-6">
        <div class="flex items-center justify-between mb-2">
          <span v-for="s in totalSteps" :key="s"
            class="flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold transition-all"
            :class="s === step ? 'bg-blue text-white shadow-md shadow-blue/25'
                   : s < step ? 'bg-success text-white'
                   : 'bg-gray-200 text-text-light'"
          >
            <svg v-if="s < step" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/>
            </svg>
            <span v-else>{{ s }}</span>
          </span>
        </div>
        <div class="flex gap-1">
          <div v-for="s in totalSteps" :key="'bar-'+s"
            class="flex-1 h-1 rounded-full transition-colors"
            :class="s <= step ? 'bg-blue' : 'bg-gray-200'"
          ></div>
        </div>
        <p class="text-xs text-text-light text-center mt-2">{{ stepLabels[step - 1] }}</p>
      </div>

      <!-- ============ STEP 1: Facility Type ============ -->
      <div v-if="step === 1" class="space-y-4">
        <div class="bg-white rounded-2xl border border-border p-5">
          <h2 class="text-lg font-bold text-brand mb-1">نوع التسهيلات</h2>
          <p class="text-sm text-text-light mb-4">اختر نوع التسهيل المطلوب لمنشأتك</p>

          <div class="space-y-3">
            <button
              v-for="ft in facilityOptions" :key="ft.value"
              @click="selectedFacilityType = ft.value"
              class="w-full flex items-center gap-3 p-4 rounded-xl border-2 transition-all cursor-pointer text-right"
              :class="selectedFacilityType === ft.value
                ? 'border-blue bg-blue/5 shadow-sm'
                : 'border-border hover:border-blue/30'"
            >
              <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                   :class="selectedFacilityType === ft.value ? 'bg-blue text-white' : 'bg-bg text-text-light'">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="ft.icon"/>
                </svg>
              </div>
              <div>
                <p class="text-sm font-bold" :class="selectedFacilityType === ft.value ? 'text-blue' : 'text-brand'">{{ ft.label }}</p>
                <p class="text-xs text-text-light mt-0.5">{{ ft.desc }}</p>
              </div>
              <div v-if="selectedFacilityType === ft.value" class="mr-auto">
                <svg class="w-5 h-5 text-blue" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
              </div>
            </button>
          </div>
        </div>

        <button
          @click="step = 2"
          :disabled="!selectedFacilityType"
          class="w-full py-3.5 rounded-xl bg-blue text-white font-bold shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          التالي — رفع السجل التجاري
        </button>
      </div>

      <!-- ============ STEP 2: Upload CR ============ -->
      <div v-if="step === 2" class="space-y-4">
        <div class="bg-white rounded-2xl border border-border p-5">
          <h2 class="text-lg font-bold text-brand mb-1">رفع السجل التجاري</h2>
          <p class="text-sm text-text-light mb-4">ارفع نسخة من السجل التجاري (PDF أو صورة واضحة)</p>

          <!-- Upload zone -->
          <div
            @click="triggerCRUpload"
            @dragover.prevent="crDragOver = true"
            @dragleave="crDragOver = false"
            @drop.prevent="handleCRDrop"
            class="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all"
            :class="crDragOver ? 'border-blue bg-blue/5' : crFile ? 'border-success bg-success/5' : 'border-border hover:border-blue/50'"
          >
            <input ref="crInput" type="file" accept=".pdf,.jpg,.jpeg,.png,.webp,.heic" class="hidden" @change="handleCRFile" />

            <div v-if="!crFile">
              <svg class="w-10 h-10 mx-auto text-text-light/40 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
              </svg>
              <p class="text-sm text-text-light font-medium">اضغط أو اسحب الملف هنا</p>
              <p class="text-xs text-text-light/60 mt-1">PDF, JPG, PNG — حد أقصى 10 MB</p>
            </div>

            <div v-else class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-success/10 flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div class="text-right min-w-0">
                <p class="text-sm font-medium text-brand truncate">{{ crFile.name }}</p>
                <p class="text-xs text-text-light">{{ formatSize(crFile.size) }}</p>
              </div>
              <button @click.stop="removeCRFile" class="mr-auto text-danger hover:text-danger/70 cursor-pointer p-1">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- CR Upload Progress -->
          <div v-if="crAnalyzing" class="mt-4">
            <div class="flex items-center gap-2 mb-2">
              <svg class="animate-spin w-4 h-4 text-blue" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              <span class="text-sm text-blue font-medium">جاري رفع الملف...</span>
            </div>
            <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
              <div class="h-full bg-blue rounded-full transition-all duration-300" :style="{ width: crProgress + '%' }"></div>
            </div>
          </div>

          <!-- CR Error -->
          <div v-if="crError" class="mt-4 flex items-start gap-2 bg-danger/5 border border-danger/20 rounded-xl p-3">
            <svg class="w-5 h-5 text-danger flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <p class="text-sm text-danger">{{ crError }}</p>
          </div>
        </div>

        <!-- CR Manual Data Form — always visible -->
        <div class="bg-white rounded-2xl border border-border p-5 space-y-4">
          <h3 class="text-base font-bold text-brand flex items-center gap-2">
            <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
            بيانات السجل التجاري
            <span class="text-xs text-text-light font-normal mr-1">(تحقق وعدّل إن لزم)</span>
          </h3>

          <!-- Company Name -->
          <div>
            <label class="block text-xs text-text-light mb-1.5">اسم المنشأة</label>
            <input
              v-model="manualForm.companyName"
              type="text"
              placeholder="مثال: مؤسسة النور للتجارة"
              class="w-full bg-bg border border-border rounded-xl px-4 py-2.5 text-sm text-brand font-medium focus:outline-none focus:border-blue transition-colors"
            />
          </div>

          <!-- Registration Number -->
          <div>
            <label class="block text-xs text-text-light mb-1.5">رقم السجل التجاري</label>
            <input
              v-model="manualForm.registrationNumber"
              type="text"
              dir="ltr"
              placeholder="1010XXXXXX"
              class="w-full bg-bg border border-border rounded-xl px-4 py-2.5 text-sm text-brand font-medium focus:outline-none focus:border-blue transition-colors text-left"
            />
          </div>

          <!-- Entity Type -->
          <div>
            <label class="block text-xs text-text-light mb-1.5">نوع الكيان</label>
            <select
              v-model="manualForm.entityType"
              class="w-full bg-bg border border-border rounded-xl px-4 py-2.5 text-sm text-brand font-medium focus:outline-none focus:border-blue transition-colors cursor-pointer"
            >
              <option value="مؤسسة فردية">مؤسسة فردية</option>
              <option value="شركة شخص واحد">شركة شخص واحد</option>
              <option value="شركة ذات مسؤولية محدودة">شركة ذات مسؤولية محدودة</option>
              <option value="شركة مساهمة">شركة مساهمة</option>
              <option value="شركة تضامن">شركة تضامن</option>
            </select>
          </div>

          <!-- Issue Date -->
          <div>
            <label class="block text-xs text-text-light mb-1.5">تاريخ إصدار السجل</label>
            <input
              v-model="manualForm.issueDate"
              type="date"
              dir="ltr"
              class="w-full bg-bg border border-border rounded-xl px-4 py-2.5 text-sm text-brand font-medium focus:outline-none focus:border-blue transition-colors"
            />
          </div>

          <!-- Live eligibility preview -->
          <div v-if="manualForm.issueDate" class="rounded-xl p-3 border"
               :class="liveEligible ? 'bg-success/5 border-success/25' : 'bg-danger/5 border-danger/20'">
            <p class="text-sm font-bold" :class="liveEligible ? 'text-success' : 'text-danger'">
              عمر المنشأة: {{ liveAge }} شهر
              <span class="font-normal text-xs mr-1">
                {{ liveEligible ? '— مؤهل للتمويل' : '— غير مؤهل (يشترط 6 أشهر على الأقل)' }}
              </span>
            </p>
          </div>

          <!-- Confirm button -->
          <button
            @click="confirmManualData"
            :disabled="!manualForm.issueDate"
            class="w-full py-3 rounded-xl bg-blue text-white font-bold shadow-md shadow-blue/20 hover:bg-blue-dark active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            تأكيد البيانات
          </button>
        </div>

        <!-- Navigation -->
        <div class="flex gap-3 mt-4">
          <button
            @click="step = 1"
            class="flex-1 py-3 rounded-xl bg-white text-brand font-bold border-2 border-border hover:border-blue active:scale-[0.98] transition-all cursor-pointer"
          >
            السابق
          </button>
          <button
            v-if="crData?.isEligible"
            @click="step = 3"
            class="flex-1 py-3.5 rounded-xl bg-blue text-white font-bold shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all cursor-pointer"
          >
            التالي — البيانات المالية
          </button>
          <button
            v-if="crData && !crData.isEligible"
            @click="finishNotEligible"
            class="flex-1 py-3.5 rounded-xl bg-white text-brand font-bold border-2 border-border hover:border-blue active:scale-[0.98] transition-all cursor-pointer"
          >
            العودة للوحة التحكم
          </button>
        </div>
      </div>

      <!-- ============ STEP 3: Financial Data ============ -->
      <div v-if="step === 3" class="space-y-4">
        <div class="bg-white rounded-2xl border border-border p-5 space-y-5">
          <div>
            <h2 class="text-lg font-bold text-brand mb-1">البيانات المالية</h2>
            <p class="text-sm text-text-light">أدخل الأرقام من كشف الحساب البنكي للمنشأة</p>
          </div>

          <!-- مجموع الدائن -->
          <div>
            <label class="block text-sm font-bold text-brand mb-1.5">مجموع الدائن (ريال) <span class="text-danger">*</span></label>
            <p class="text-xs text-text-light mb-2">إجمالي المبالغ الواردة للحساب البنكي</p>
            <input
              v-model.number="totalCredit"
              type="number"
              min="0"
              placeholder="مثال: 250000"
              dir="ltr"
              class="w-full bg-bg border border-border rounded-xl px-4 py-2.5 text-sm text-brand font-medium focus:outline-none focus:border-blue transition-colors text-left"
            />
          </div>

          <!-- مجموع المدين -->
          <div>
            <label class="block text-sm font-bold text-brand mb-1.5">مجموع المدين (ريال) <span class="text-danger">*</span></label>
            <p class="text-xs text-text-light mb-2">إجمالي المبالغ الصادرة من الحساب البنكي</p>
            <input
              v-model.number="totalDebit"
              type="number"
              min="0"
              placeholder="مثال: 200000"
              dir="ltr"
              class="w-full bg-bg border border-border rounded-xl px-4 py-2.5 text-sm text-brand font-medium focus:outline-none focus:border-blue transition-colors text-left"
            />
          </div>

          <!-- مبيعات نقاط البيع -->
          <div>
            <label class="block text-sm font-bold text-brand mb-1.5">مبيعات نقاط البيع POS (ريال)</label>
            <p class="text-xs text-text-light mb-2">إجمالي مبيعات الـ POS (0 إذا لا يوجد)</p>
            <input
              v-model.number="posSales"
              type="number"
              min="0"
              placeholder="مثال: 80000"
              dir="ltr"
              class="w-full bg-bg border border-border rounded-xl px-4 py-2.5 text-sm text-brand font-medium focus:outline-none focus:border-blue transition-colors text-left"
            />
          </div>

          <!-- إيرادات أخرى -->
          <div>
            <label class="block text-sm font-bold text-brand mb-1.5">إيرادات أخرى (ريال)</label>
            <p class="text-xs text-text-light mb-2">أي إيرادات إضافية غير مشمولة في الأعلى (اختياري)</p>
            <input
              v-model.number="otherIncome"
              type="number"
              min="0"
              placeholder="مثال: 10000"
              dir="ltr"
              class="w-full bg-bg border border-border rounded-xl px-4 py-2.5 text-sm text-brand font-medium focus:outline-none focus:border-blue transition-colors text-left"
            />
          </div>

          <div v-if="financialError" class="flex items-start gap-2 bg-danger/5 border border-danger/20 rounded-xl p-3">
            <p class="text-sm text-danger">{{ financialError }}</p>
          </div>
        </div>

        <div class="flex gap-3 mt-4">
          <button @click="step = 2" class="flex-1 py-3 rounded-xl bg-white text-brand font-bold border-2 border-border hover:border-blue active:scale-[0.98] transition-all cursor-pointer">السابق</button>
          <button
            @click="goToQuestions"
            :disabled="!totalCredit || !totalDebit"
            class="flex-1 py-3.5 rounded-xl bg-blue text-white font-bold shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            التالي — الأسئلة الإلزامية
          </button>
        </div>
      </div>

      <!-- ============ STEP 4: Mandatory Questions + Pre-filter ============ -->
      <div v-if="step === 4" class="space-y-4">
        <div class="bg-white rounded-2xl border border-border p-5">
          <h2 class="text-lg font-bold text-brand mb-1">أسئلة إلزامية</h2>
          <p class="text-sm text-text-light mb-5">يرجى الإجابة على الأسئلة التالية لتحديد الأهلية المبدئية</p>

          <!-- Q1: POS -->
          <div class="mb-5">
            <p class="text-sm font-bold text-brand mb-2">هل لدى المنشأة نقاط بيع (POS)؟</p>
            <div class="flex gap-3">
              <button @click="questions.has_pos = true"
                class="flex-1 py-3 rounded-xl border-2 font-bold text-sm transition-all cursor-pointer"
                :class="questions.has_pos === true ? 'border-blue bg-blue/5 text-blue' : 'border-border text-text-light hover:border-blue/30'"
              >نعم</button>
              <button @click="questions.has_pos = false"
                class="flex-1 py-3 rounded-xl border-2 font-bold text-sm transition-all cursor-pointer"
                :class="questions.has_pos === false ? 'border-blue bg-blue/5 text-blue' : 'border-border text-text-light hover:border-blue/30'"
              >لا</button>
            </div>
          </div>

          <!-- Q2: Partners count -->
          <div class="mb-5">
            <p class="text-sm font-bold text-brand mb-2">كم عدد الشركاء؟</p>
            <div class="flex gap-3">
              <button @click="questions.partner_count = 1"
                class="flex-1 py-3 rounded-xl border-2 font-bold text-sm transition-all cursor-pointer"
                :class="questions.partner_count === 1 ? 'border-blue bg-blue/5 text-blue' : 'border-border text-text-light hover:border-blue/30'"
              >شريك واحد</button>
              <button @click="questions.partner_count = 2"
                class="flex-1 py-3 rounded-xl border-2 font-bold text-sm transition-all cursor-pointer"
                :class="questions.partner_count >= 2 ? 'border-blue bg-blue/5 text-blue' : 'border-border text-text-light hover:border-blue/30'"
              >2 أو أكثر</button>
            </div>
          </div>

          <!-- Q3: Saudi / Foreign -->
          <div class="mb-5">
            <p class="text-sm font-bold text-brand mb-2">هل المالك سعودي أم مستثمر أجنبي؟</p>
            <div class="flex gap-3">
              <button @click="questions.is_saudi = true"
                class="flex-1 py-3 rounded-xl border-2 font-bold text-sm transition-all cursor-pointer"
                :class="questions.is_saudi === true ? 'border-blue bg-blue/5 text-blue' : 'border-border text-text-light hover:border-blue/30'"
              >سعودي</button>
              <button @click="questions.is_saudi = false"
                class="flex-1 py-3 rounded-xl border-2 font-bold text-sm transition-all cursor-pointer"
                :class="questions.is_saudi === false ? 'border-blue bg-blue/5 text-blue' : 'border-border text-text-light hover:border-blue/30'"
              >مستثمر أجنبي</button>
            </div>
          </div>

        </div>

        <!-- Pre-filter result messages -->
        <div v-if="preFilterDone && preFilterResult" class="rounded-2xl p-4 border"
             :class="preFilterResult.rejected ? 'bg-danger/5 border-danger/20' : 'bg-success/5 border-success/20'">
          <div class="flex items-start gap-2">
            <svg class="w-5 h-5 flex-shrink-0 mt-0.5" :class="preFilterResult.rejected ? 'text-danger' : 'text-success'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                :d="preFilterResult.rejected
                  ? 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
                  : 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'"
              />
            </svg>
            <div>
              <p class="text-sm font-bold" :class="preFilterResult.rejected ? 'text-danger' : 'text-success'">
                {{ preFilterResult.rejected ? 'غير مؤهل حالياً' : 'مؤهل مبدئياً!' }}
              </p>
              <p class="text-xs mt-1" :class="preFilterResult.rejected ? 'text-danger/70' : 'text-success/70'">
                {{ preFilterResult.rejected
                  ? 'لا توجد جهة تمويل مناسبة لهذا الطلب بناءً على البيانات المقدمة.'
                  : `يرجى رفع كشف الحساب البنكي لآخر ${preFilterResult.required_bs_months} شهر لاستكمال التقييم.` }}
              </p>
            </div>
          </div>
        </div>

        <!-- Pre-filter loading -->
        <div v-if="preFilterLoading" class="flex items-center gap-2 justify-center py-4">
          <svg class="animate-spin w-5 h-5 text-blue" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
          <span class="text-sm text-blue font-medium">جاري التقييم المبدئي...</span>
        </div>

        <!-- Pre-filter error -->
        <div v-if="preFilterError" class="flex items-start gap-2 bg-danger/5 border border-danger/20 rounded-xl p-3">
          <svg class="w-5 h-5 text-danger flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <p class="text-sm text-danger">{{ preFilterError }}</p>
        </div>

        <!-- Navigation -->
        <div class="flex gap-3 mt-4">
          <button
            @click="step = 3"
            class="flex-1 py-3 rounded-xl bg-white text-brand font-bold border-2 border-border hover:border-blue active:scale-[0.98] transition-all cursor-pointer"
          >
            السابق
          </button>
          <button
            v-if="!preFilterDone"
            @click="runPreFilter"
            :disabled="!questionsComplete || preFilterLoading"
            class="flex-1 py-3.5 rounded-xl bg-blue text-white font-bold shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            تحقق من الأهلية المبدئية
          </button>
          <button
            v-if="preFilterDone && !preFilterResult?.rejected"
            @click="step = 5"
            class="flex-1 py-3.5 rounded-xl bg-blue text-white font-bold shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all cursor-pointer"
          >
            التالي — رفع كشف الحساب
          </button>
          <button
            v-if="preFilterDone && preFilterResult?.rejected"
            @click="$router.push('/partner')"
            class="flex-1 py-3.5 rounded-xl bg-white text-brand font-bold border-2 border-border hover:border-blue active:scale-[0.98] transition-all cursor-pointer"
          >
            العودة للوحة التحكم
          </button>
        </div>
      </div>

      <!-- ============ STEP 5: Upload Bank Statement ============ -->
      <div v-if="step === 5" class="space-y-4">
        <div class="bg-white rounded-2xl border border-border p-5">
          <h2 class="text-lg font-bold text-brand mb-1">رفع كشف الحساب البنكي</h2>

          <!-- Required period message -->
          <div class="bg-blue/5 border border-blue/20 rounded-xl p-3 mb-4">
            <div class="flex items-start gap-2">
              <svg class="w-5 h-5 text-blue flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <p class="text-sm text-blue font-medium">يرجى رفع كشف حساب بصيغة Excel أو PDF لآخر {{ requiredBsMonths }} شهر</p>
            </div>
          </div>

          <!-- Upload zone -->
          <div
            @click="triggerBSUpload"
            @dragover.prevent="bsDragOver = true"
            @dragleave="bsDragOver = false"
            @drop.prevent="handleBSDrop"
            class="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all"
            :class="bsDragOver ? 'border-blue bg-blue/5' : bsFile ? 'border-success bg-success/5' : 'border-border hover:border-blue/50'"
          >
            <input ref="bsInput" type="file" accept=".xlsx,.xls,.pdf" class="hidden" @change="handleBSFile" />

            <div v-if="!bsFile">
              <svg class="w-10 h-10 mx-auto text-text-light/40 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
              </svg>
              <p class="text-sm text-text-light font-medium">اضغط أو اسحب الملف هنا</p>
              <p class="text-xs text-text-light/60 mt-1">Excel (.xlsx, .xls) أو PDF — حد أقصى 20 MB</p>
            </div>

            <div v-else class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-success/10 flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
              </div>
              <div class="text-right min-w-0">
                <p class="text-sm font-medium text-brand truncate">{{ bsFile.name }}</p>
                <p class="text-xs text-text-light">{{ formatSize(bsFile.size) }}</p>
              </div>
              <button @click.stop="removeBSFile" class="mr-auto text-danger hover:text-danger/70 cursor-pointer p-1">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </div>

          <!-- BS Upload Progress -->
          <div v-if="bsUploading" class="mt-4">
            <div class="flex items-center gap-2 mb-2">
              <svg class="animate-spin w-4 h-4 text-blue" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              <span class="text-sm text-blue font-medium">جاري رفع كشف الحساب...</span>
            </div>
          </div>

          <!-- BS Error -->
          <div v-if="bsError" class="mt-4 flex items-start gap-2 bg-danger/5 border border-danger/20 rounded-xl p-3">
            <svg class="w-5 h-5 text-danger flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <div>
              <p class="text-sm text-danger">{{ bsError }}</p>
              <button @click="removeBSFile" class="text-xs text-blue font-medium mt-1 hover:underline cursor-pointer">إعادة الرفع</button>
            </div>
          </div>

          <!-- BS Uploaded OK -->
          <div v-if="bsUploaded && !bsError" class="mt-4 flex items-start gap-2 bg-success/5 border border-success/20 rounded-xl p-3">
            <svg class="w-5 h-5 text-success flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <p class="text-sm text-success font-medium">تم رفع كشف الحساب بنجاح.</p>
          </div>
        </div>

        <!-- Navigation -->
        <div class="flex gap-3 mt-4">
          <button
            @click="step = 4"
            class="flex-1 py-3 rounded-xl bg-white text-brand font-bold border-2 border-border hover:border-blue active:scale-[0.98] transition-all cursor-pointer"
          >
            السابق
          </button>
          <button
            @click="step = 6"
            :disabled="!bsUploaded || !!bsError"
            class="flex-1 py-3 rounded-xl bg-blue text-white font-bold shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            التالي — المستندات الأساسية
          </button>
        </div>
      </div>

      <!-- ============ STEP 6: Basic Documents ============ -->
      <div v-if="step === 6" class="space-y-4">
        <div class="bg-white rounded-2xl border border-border p-5 space-y-5">
          <div>
            <h2 class="text-lg font-bold text-brand mb-1">المستندات الأساسية</h2>
            <p class="text-sm text-text-light">رفع المستندات التالية لإتمام الطلب</p>
          </div>

          <div v-for="(doc, i) in basicDocs" :key="i" class="border border-border rounded-xl p-4">
            <div class="flex items-center justify-between mb-2">
              <label class="text-sm font-bold text-brand">{{ doc.name }}</label>
              <span v-if="doc.uploaded" class="text-xs text-success font-medium">✔ تم الرفع</span>
              <span v-else-if="doc.uploading" class="text-xs text-blue">جاري…</span>
            </div>
            <div v-if="doc.error" class="text-xs text-danger mb-2">{{ doc.error }}</div>
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                class="hidden"
                @change="handleBasicDocSelect(i, $event)"
              />
              <div class="flex-1 py-2 px-3 rounded-lg text-xs border-2 text-center"
                   :class="doc.uploaded ? 'border-success/40 bg-success/5 text-success' : 'border-dashed border-border bg-bg text-text-light hover:border-blue hover:text-blue transition-colors'">
                {{ doc.fileName || 'اختر ملف (PDF أو صورة)' }}
              </div>
            </label>
          </div>
        </div>

        <div class="flex gap-3 mt-4">
          <button @click="step = 5" class="flex-1 py-3 rounded-xl bg-white text-brand font-bold border-2 border-border hover:border-blue active:scale-[0.98] transition-all cursor-pointer">السابق</button>
          <div class="flex-1 flex flex-col gap-2">
            <div v-if="basicDocsUploadError" class="text-xs text-danger text-center">خطأ في رفع بعض الملفات — تحقّق وحاول مجدداً</div>
            <button
              @click="uploadAllBasicDocs"
              :disabled="!basicDocsAllSelected || basicDocsUploading"
              class="w-full py-3.5 rounded-xl bg-blue text-white font-bold shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="!basicDocsUploading">التالي — المراجعة</span>
              <span v-else class="flex items-center justify-center gap-2">
                <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
                جاري رفع المستندات...
              </span>
            </button>
          </div>
        </div>
      </div>

      <!-- ============ STEP 7: Review & Submit ============ -->
      <div v-if="step === 7" class="space-y-4">
        <div class="bg-white rounded-2xl border border-border p-5">
          <h2 class="text-lg font-bold text-brand mb-4">مراجعة الطلب</h2>

          <!-- Facility type -->
          <div class="bg-bg rounded-xl p-4 mb-3">
            <div class="flex items-center gap-2 mb-2">
              <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
              </svg>
              <h3 class="text-sm font-bold text-brand">نوع التسهيلات</h3>
            </div>
            <p class="text-sm text-brand font-medium">{{ facilityTypeLabel }}</p>
          </div>

          <!-- CR Summary -->
          <div class="bg-bg rounded-xl p-4 mb-3">
            <div class="flex items-center gap-2 mb-2">
              <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
              <h3 class="text-sm font-bold text-brand">السجل التجاري</h3>
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div><span class="text-text-light">المنشأة:</span> <span class="font-medium text-brand">{{ crData?.companyName }}</span></div>
              <div><span class="text-text-light">السجل:</span> <span class="font-medium text-brand" dir="ltr">{{ crData?.registrationNumber }}</span></div>
              <div><span class="text-text-light">النوع:</span> <span class="font-medium text-brand">{{ crData?.entityType }}</span></div>
              <div><span class="text-text-light">العمر:</span> <span class="font-medium text-brand">{{ crData?.ageInMonths }} شهر</span></div>
            </div>
          </div>

          <!-- Questions Summary -->
          <div class="bg-bg rounded-xl p-4 mb-3">
            <div class="flex items-center gap-2 mb-2">
              <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <h3 class="text-sm font-bold text-brand">إجابات الأسئلة</h3>
            </div>
            <div class="space-y-1 text-xs">
              <div><span class="text-text-light">نقاط بيع:</span> <span class="font-medium text-brand">{{ questions.has_pos ? 'نعم' : 'لا' }}</span></div>
              <div><span class="text-text-light">فواتير مبيعات:</span> <span class="font-medium text-brand">{{ questions.has_invoices ? 'نعم' : 'لا' }}</span></div>
              <div><span class="text-text-light">عدد الشركاء:</span> <span class="font-medium text-brand">{{ questions.partner_count === 1 ? 'شريك واحد' : '2 أو أكثر' }}</span></div>
              <div><span class="text-text-light">الجنسية:</span> <span class="font-medium text-brand">{{ questions.is_saudi ? 'سعودي' : 'مستثمر أجنبي' }}</span></div>
            </div>
          </div>

          <!-- BS Summary -->
          <div class="bg-bg rounded-xl p-4 mb-3">
            <div class="flex items-center gap-2 mb-2">
              <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/>
              </svg>
              <h3 class="text-sm font-bold text-brand">كشف الحساب البنكي</h3>
            </div>
            <div class="grid grid-cols-2 gap-2 text-xs">
              <div><span class="text-text-light">الملف:</span> <span class="font-medium text-brand">{{ bsFile?.name }}</span></div>
              <div><span class="text-text-light">التغطية:</span> <span class="font-medium text-brand">{{ requiredBsMonths }} شهر</span></div>
            </div>
          </div>

        </div>

        <!-- Submit buttons -->
        <div class="flex gap-3 mt-4">
          <button
            @click="step = 6"
            class="flex-1 py-3 rounded-xl bg-white text-brand font-bold border-2 border-border hover:border-blue active:scale-[0.98] transition-all cursor-pointer"
          >
            السابق
          </button>
          <button
            @click="submitRequest"
            :disabled="isSubmitting"
            class="flex-1 py-3.5 rounded-xl bg-blue text-white font-bold shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="!isSubmitting">إرسال الطلب للتحليل</span>
            <span v-else class="flex items-center justify-center gap-2">
              <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              جاري الإرسال...
            </span>
          </button>
        </div>
      </div>

      <!-- ============ STEP 8: Analysis Progress / Result ============ -->
      <div v-if="step === 8" class="space-y-4">
        <div class="bg-white rounded-2xl border border-border p-6 text-center">
          <!-- Analyzing state -->
          <div v-if="!analysisDone">
            <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-blue/10 flex items-center justify-center">
              <svg class="animate-spin w-10 h-10 text-blue" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
            </div>
            <h2 class="text-lg font-bold text-brand mb-2">جاري تحليل الطلب</h2>
            <p class="text-sm text-text-light mb-4">يتم الآن تحليل البيانات المالية وتطبيق قواعد التمويل...</p>

            <!-- Progress bar -->
            <div class="w-full h-3 bg-gray-100 rounded-full overflow-hidden mb-2">
              <div class="h-full bg-gradient-to-l from-blue to-blue-light rounded-full transition-all duration-500" :style="{ width: analysisProgress + '%' }"></div>
            </div>
            <p class="text-sm font-bold text-blue">{{ analysisProgress }}%</p>

            <p class="text-xs text-text-light mt-4">
              لا تغلق هذه الصفحة. سيتم إعلامك عند اكتمال التحليل.
            </p>
          </div>

          <!-- Analysis complete -->
          <div v-else>
            <div class="w-20 h-20 mx-auto mb-4 rounded-full flex items-center justify-center"
                 :class="isEligible ? 'bg-success/10' : isPendingManualReview ? 'bg-warning/10' : 'bg-danger/10'">
              <svg class="w-10 h-10" :class="isEligible ? 'text-success' : isPendingManualReview ? 'text-warning' : 'text-danger'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  :d="isEligible
                    ? 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
                    : isPendingManualReview
                    ? 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
                    : 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'"
                />
              </svg>
            </div>

            <h2 class="text-lg font-bold text-brand mb-2">تم استلام طلبك</h2>
            <p class="text-sm text-text-light mb-6 leading-relaxed">تم استلام طلبك بنجاح وسنتواصل معك قريباً.</p>

            <!-- Required documents (if eligible) -->
            <div v-if="isEligible && requiredDocs.length > 0" class="text-right mb-6">
              <h3 class="text-sm font-bold text-brand mb-2">المستندات المطلوبة:</h3>
              <ul class="space-y-1.5">
                <li v-for="(doc, i) in requiredDocs" :key="i" class="flex items-start gap-2 text-xs text-text-light">
                  <svg class="w-4 h-4 text-blue flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                  </svg>
                  <span>{{ doc }}</span>
                </li>
              </ul>
            </div>

            <!-- Retry button for non-eligible cases -->
            <button
              v-if="!isEligible && !isPendingManualReview"
              @click="retryWizard"
              class="w-full py-3.5 rounded-xl bg-blue text-white font-bold shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all cursor-pointer mb-3"
            >
              المحاولة مجدداً
            </button>

            <button
              @click="$router.push('/partner')"
              class="w-full py-3.5 rounded-xl font-bold active:scale-[0.98] transition-all cursor-pointer"
              :class="isEligible || isPendingManualReview ? 'bg-blue text-white shadow-lg shadow-blue/25 hover:bg-blue-dark' : 'bg-gray-100 text-text-light hover:bg-gray-200'"
            >
              العودة للوحة التحكم
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, markRaw } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { calculateAgeInMonths, getRequiredStatementMonths } from '../../utils/crAnalyzer'
import { analysisApi } from '../../api/client'
import type { FacilityType, EntityType } from '../../types/request'

const router = useRouter()
const route = useRoute()

const totalSteps = 8
const stepLabels = [
  'نوع التسهيلات',
  'السجل التجاري',
  'البيانات المالية',
  'الأسئلة الإلزامية',
  'رفع كشف الحساب',
  'المستندات الأساسية',
  'المراجعة والإرسال',
  'نتيجة الطلب',
]

const step = ref(1)

// ---- Case tracking ----
const caseId = ref('')
const caseDisplayId = ref('')

// ---- Step 1: Facility Type ----
const selectedFacilityType = ref<FacilityType | null>(null)
const facilityOptions = [
  {
    value: 'pos' as FacilityType,
    label: 'نقاط بيع',
    desc: 'تمويل مبني على مبيعات نقاط البيع (POS)',
    icon: 'M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z',
  },
  {
    value: 'cash' as FacilityType,
    label: 'كاش',
    desc: 'تمويل نقدي مبني على الإيداعات والإيرادات',
    icon: 'M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z',
  },
  {
    value: 'fleet' as FacilityType,
    label: 'سيارات (أسطول)',
    desc: 'تمويل أسطول مركبات للمنشأة',
    icon: 'M8 7h8m-8 5h8m-4 5v-5m-8 5h16a1 1 0 001-1v-3a1 1 0 00-.4-.8l-2-1.5m-11.2 0l-2 1.5A1 1 0 003 13v3a1 1 0 001 1m4-7V6a2 2 0 012-2h4a2 2 0 012 2v4',
  },
]

const facilityTypeLabel = computed(() => {
  const ft = facilityOptions.find(f => f.value === selectedFacilityType.value)
  return ft?.label || ''
})

// ---- Step 2: CR ----
const crInput = ref<HTMLInputElement | null>(null)
const crFile = ref<File | null>(null)
const crDragOver = ref(false)
const crAnalyzing = ref(false)
const crProgress = ref(0)
const crError = ref('')
const crParsed = ref(false)
const manualEntryLoading = ref(false)
interface CRData {
  companyName: string
  registrationNumber: string
  entityType: EntityType
  issueDate: string
  ageInMonths: number
  isEligible: boolean
  requiredStatementMonths: number
  eligibilityMessage: string
}

const crData = ref<CRData | null>(null)

// ---- Manual CR form (editable, always shown after upload) ----
const manualForm = ref({
  companyName: '',
  registrationNumber: '',
  entityType: 'مؤسسة فردية' as EntityType,
  issueDate: '',
})

const liveAge = computed(() => {
  if (!manualForm.value.issueDate) return 0
  return calculateAgeInMonths(manualForm.value.issueDate)
})

const liveEligible = computed(() => {
  if (!manualForm.value.issueDate) return false
  const { isEligible } = getRequiredStatementMonths(liveAge.value)
  return isEligible
})

async function confirmManualData() {
  const ageInMonths = liveAge.value
  const { isEligible, requiredMonths, message } = getRequiredStatementMonths(ageInMonths)
  crData.value = {
    companyName: manualForm.value.companyName,
    registrationNumber: manualForm.value.registrationNumber,
    entityType: manualForm.value.entityType,
    issueDate: manualForm.value.issueDate,
    ageInMonths,
    isEligible,
    requiredStatementMonths: requiredMonths,
    eligibilityMessage: message,
  }
  // Create case if not created yet (manual mode, no file uploaded)
  if (!caseId.value && selectedFacilityType.value) {
    try {
      manualEntryLoading.value = true
      const result = await analysisApi.createManualCase(selectedFacilityType.value)
      caseId.value = result.case_id
      caseDisplayId.value = result.display_id
    } catch (err: any) {
      crError.value = err.message || 'خطأ في إنشاء الطلب'
      crData.value = null
      manualEntryLoading.value = false
      return
    }
    manualEntryLoading.value = false
  }
  // Sync to backend
  if (caseId.value) {
    analysisApi.updateCRInfo(caseId.value, {
      company_name: crData.value.companyName,
      registration_number: crData.value.registrationNumber,
      entity_type: crData.value.entityType,
      issue_date: crData.value.issueDate,
      age_in_months: ageInMonths,
      activity: '',
    }).catch(() => {})
  }
}

// ---- Step 6: Basic Documents ----
const basicDocs = ref([
  { name: 'صورة الهوية الوطنية / الإقامة', file: null as File | null, fileName: '', uploaded: false, uploading: false, error: '' },
  { name: 'العنوان الوطني للمنشأة والملاك', file: null as File | null, fileName: '', uploaded: false, uploading: false, error: '' },
  { name: 'شهادة الآيبان بالباركود', file: null as File | null, fileName: '', uploaded: false, uploading: false, error: '' },
])
const basicDocsAllSelected = computed(() => basicDocs.value.every(d => d.file !== null))

async function handleBasicDocSelect(idx: number, event: Event) {
  const input = event.target as HTMLInputElement
  const file = input?.files?.[0]
  if (!file) return
  basicDocs.value[idx].file = markRaw(file)
  basicDocs.value[idx].fileName = file.name
  basicDocs.value[idx].uploaded = false
  basicDocs.value[idx].error = ''
}

const basicDocsUploading = ref(false)
const basicDocsUploadError = ref('')

async function uploadAllBasicDocs() {
  if (!caseId.value) return
  basicDocsUploading.value = true
  basicDocsUploadError.value = ''
  for (let i = 0; i < basicDocs.value.length; i++) {
    const doc = basicDocs.value[i]
    if (!doc.file || doc.uploaded) continue
    basicDocs.value[i].uploading = true
    try {
      await analysisApi.uploadBasicDoc(caseId.value, doc.name, doc.file)
      basicDocs.value[i].uploaded = true
      basicDocs.value[i].error = ''
    } catch (err: any) {
      const msg = typeof err.message === 'string' && !err.message.includes('Object') ? err.message : 'خطأ في رفع الملف، حاول مرة أخرى'
      basicDocs.value[i].error = msg
      basicDocsUploadError.value = msg
    } finally {
      basicDocs.value[i].uploading = false
    }
  }
  basicDocsUploading.value = false
  if (!basicDocsUploadError.value) step.value = 7
}

// ---- Step 3: Financial data ----
const totalCredit = ref<number | null>(null)
const totalDebit = ref<number | null>(null)
const posSales = ref<number | null>(null)
const otherIncome = ref<number | null>(null)
const financialSaved = ref(false)
const financialError = ref('')

async function saveFinancialData() {
  if (!caseId.value) return
  financialError.value = ''
  try {
    await analysisApi.saveFinancial(caseId.value, {
      total_credit: totalCredit.value || 0,
      total_debit: totalDebit.value || 0,
      pos_sales: posSales.value || 0,
      other_income: otherIncome.value || 0,
    })
    financialSaved.value = true
  } catch (err: any) {
    financialError.value = err.message || 'خطأ في حفظ البيانات'
  }
}

async function goToQuestions() {
  if (!caseId.value) {
    financialError.value = 'لم يتم إنشاء الطلب بعد. يرجى العودة للخطوة السابقة وتأكيد بيانات السجل التجاري.'
    return
  }
  await saveFinancialData()
  if (!financialError.value) step.value = 4
}

// ---- Step 4: Questions + Pre-filter ----
const questions = ref({
  has_pos: null as boolean | null,
  partner_count: 1,
  is_saudi: null as boolean | null,
})

// has_invoices is NOT a user question — derived from facility_type
// (pos = no invoices path, cash/fleet = invoices path)
const questionsComplete = computed(() => {
  return questions.value.has_pos !== null && questions.value.is_saudi !== null
})

const preFilterLoading = ref(false)
const preFilterDone = ref(false)
const preFilterResult = ref<{
  has_eligible: boolean
  eligible_count: number
  required_bs_months: number
  rejected: boolean
} | null>(null)
const preFilterError = ref('')
const requiredBsMonths = ref(0)

// ---- Step 4: BS ----
const bsInput = ref<HTMLInputElement | null>(null)
const bsFile = ref<File | null>(null)
const bsDragOver = ref(false)
const bsUploading = ref(false)
const bsError = ref('')
const bsUploaded = ref(false)

// ---- Step 5/6: Submit & Analysis ----
const isSubmitting = ref(false)
const analysisProgress = ref(0)
const analysisDone = ref(false)
const resultSummary = ref('')
const isEligible = ref(false)
const requiredDocs = ref<string[]>([])
let pollTimer: ReturnType<typeof setInterval> | null = null

// True when PDF bank statement couldn't be parsed → awaiting manual review (not a rejection)
// Empty result_summary also means PDF parse failure (manual review needed), not a rejection
const isPendingManualReview = computed(() =>
  !isEligible.value && (resultSummary.value.includes('مراجعة يدوية') || resultSummary.value === '')
)

onMounted(() => {
  // No pre-loading needed — wizard starts fresh
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// ---- CR Upload Handlers ----
function triggerCRUpload() {
  if (!crAnalyzing.value) crInput.value?.click()
}

function handleCRFile(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) startCRAnalysis(input.files[0])
}

function handleCRDrop(e: DragEvent) {
  crDragOver.value = false
  if (e.dataTransfer?.files?.[0]) startCRAnalysis(e.dataTransfer.files[0])
}

function removeCRFile() {
  crFile.value = null
  crError.value = ''
  crProgress.value = 0
  // NOTE: do NOT clear caseId — the case already exists in the DB.
  // A new upload will update the same case instead of creating a new one.
  if (crInput.value) crInput.value.value = ''
}

async function startCRAnalysis(file: File) {
  crFile.value = file
  crError.value = ''
  crAnalyzing.value = true
  crProgress.value = 0

  const validExt = /\.(pdf|jpe?g|png|webp|heic)$/i.test(file.name)
  const validMime = ['application/pdf','image/jpeg','image/png','image/webp','image/heic'].includes(file.type)
  if (!validMime && !validExt) {
    crAnalyzing.value = false
    crError.value = 'صيغة الملف غير مدعومة. يرجى رفع PDF أو صورة (JPG, PNG).'
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    crAnalyzing.value = false
    crError.value = 'حجم الملف كبير جداً. الحد الأقصى 10 ميجابايت.'
    return
  }

  crProgress.value = 40
  try {
    const uploadResult = await analysisApi.uploadCR(file, selectedFacilityType.value!)
    caseId.value = uploadResult.case_id
    caseDisplayId.value = uploadResult.display_id
    crProgress.value = 100
  } catch (err: any) {
    crError.value = err.message || 'خطأ أثناء رفع الملف. يمكنك تعبئة البيانات يدوياً.'
  }

  crAnalyzing.value = false
}

function finishNotEligible() {
  router.push('/partner')
}



// ---- Pre-filter ----
async function runPreFilter() {
  if (!caseId.value) {
    preFilterError.value = 'لم يتم إنشاء الطلب بعد. يرجى العودة للخطوة السابقة والتأكد من رفع السجل التجاري أو تأكيد البيانات.'
    return
  }

  preFilterLoading.value = true
  preFilterError.value = ''
  preFilterDone.value = false
  preFilterResult.value = null

  try {
    // has_invoices is determined by facility_type: cash/fleet → true, pos → false
    const derivedHasInvoices = selectedFacilityType.value !== 'pos'

    // Save questions to backend
    await analysisApi.updateQuestions(caseId.value, {
      has_pos: questions.value.has_pos!,
      has_invoices: derivedHasInvoices,
      partner_count: questions.value.partner_count,
      is_saudi: questions.value.is_saudi!,
    })

    // Run pre-filter
    const result = await analysisApi.preFilter(caseId.value)
    preFilterResult.value = result
    preFilterDone.value = true
    requiredBsMonths.value = result.required_bs_months
  } catch (err: any) {
    preFilterError.value = err.message || 'حدث خطأ أثناء التقييم المبدئي'
  }

  preFilterLoading.value = false
}

// ---- BS Upload Handlers ----
function triggerBSUpload() {
  if (!bsUploading.value) bsInput.value?.click()
}

function handleBSFile(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.[0]) startBSUpload(input.files[0])
}

function handleBSDrop(e: DragEvent) {
  bsDragOver.value = false
  if (e.dataTransfer?.files?.[0]) startBSUpload(e.dataTransfer.files[0])
}

function removeBSFile() {
  bsFile.value = null
  bsUploaded.value = false
  bsError.value = ''
  if (bsInput.value) bsInput.value.value = ''
}

async function startBSUpload(file: File) {
  // Validate file format: Excel or PDF
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!['xlsx', 'xls', 'pdf'].includes(ext || '')) {
    bsError.value = 'يرجى رفع ملف بصيغة Excel (.xlsx أو .xls) أو PDF فقط'
    return
  }

  bsFile.value = file
  bsError.value = ''
  bsUploaded.value = false
  bsUploading.value = true

  try {
    await analysisApi.uploadBS(caseId.value, file)
    bsUploaded.value = true
  } catch (err: any) {
    bsError.value = err.message || 'خطأ أثناء رفع كشف الحساب'
  }

  bsUploading.value = false
}

// ---- Submit & Poll Analysis ----
async function submitRequest() {
  isSubmitting.value = true

  // The BS upload already triggers analysis on the backend
  // Just move to analysis tracking step
  isSubmitting.value = false
  step.value = 8

  startPolling()
}

function startPolling() {
  analysisDone.value = false
  analysisProgress.value = 0

  pollTimer = setInterval(async () => {
    try {
      const status = await analysisApi.getStatus(caseId.value)
      analysisProgress.value = status.analysis_progress

      if (status.stage !== 'analyzing' || status.analysis_progress >= 100) {
        // Analysis done
        if (pollTimer) clearInterval(pollTimer)
        pollTimer = null

        analysisDone.value = true
        isEligible.value = status.is_eligible
        resultSummary.value = status.result_summary

        // Get full result for documents & AI summary
        try {
          const fullResult = await analysisApi.getResult(caseId.value)
          if (fullResult?.required_docs) {
            requiredDocs.value = fullResult.required_docs
          }
          // Show AI-generated narrative summary if available
          if (fullResult?.ai_summary) {
            resultSummary.value = fullResult.ai_summary
          }
        } catch {
          // Non-critical
        }
      }
    } catch {
      // Keep polling even on error
    }
  }, 2000)
}

function goBack() {
  if (step.value > 1 && step.value < 6) {
    step.value--
  } else {
    router.push('/partner')
  }
}

function retryWizard() {
  // Reset all state back to step 1
  step.value = 1
  selectedFacilityType.value = null
  crFile.value = null
  crParsed.value = false
  crData.value = null
  crError.value = ''
  crProgress.value = 0
  caseId.value = ''
  caseDisplayId.value = ''
  questions.value = { has_pos: null, partner_count: 1, is_saudi: null }
  preFilterDone.value = false
  preFilterResult.value = null
  preFilterError.value = ''
  bsFile.value = null
  bsUploaded.value = false
  bsError.value = ''
  analysisDone.value = false
  analysisProgress.value = 0
  isEligible.value = false
  resultSummary.value = ''
  requiredDocs.value = []
  manualForm.value = { companyName: '', registrationNumber: '', entityType: 'مؤسسة فردية', issueDate: '' }
  totalCredit.value = null
  totalDebit.value = null
  posSales.value = null
  otherIncome.value = null
  basicDocs.value.forEach(d => { d.file = null; d.fileName = ''; d.uploaded = false; d.uploading = false; d.error = '' })
  basicDocsUploading.value = false
  basicDocsUploadError.value = ''
  financialSaved.value = false
  financialError.value = ''
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}
</script>
