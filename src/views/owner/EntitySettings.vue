<template>
  <div class="min-h-screen min-h-dvh bg-bg">
    <!-- Top bar -->
    <header class="bg-white border-b border-border sticky top-0 z-30">
      <div class="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <img src="/logo.svg" alt="Jenan BIZ" class="h-8" />
          <span class="text-xs font-bold bg-blue/10 text-blue px-2 py-0.5 rounded-lg">المالك</span>
        </div>
        <div class="flex items-center gap-3">
          <NotificationBell />
          <router-link to="/owner/users" class="text-sm text-text-light hover:text-blue transition-colors">المستخدمون</router-link>
          <router-link to="/owner/campaigns" class="text-sm text-text-light hover:text-blue transition-colors">الحملات</router-link>
          <router-link to="/supervisor" class="text-sm text-text-light hover:text-blue transition-colors">لوحة المشرف</router-link>
          <button @click="handleLogout" class="text-text-light hover:text-danger transition-colors cursor-pointer p-1">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
            </svg>
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-5xl mx-auto px-4 pb-8">
      <!-- Page title -->
      <div class="mt-6 mb-4 flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 class="text-xl font-bold text-brand">إعدادات الجهات التمويلية</h1>
          <p class="text-sm text-text-light mt-1">إدارة أولويات تقييم الجهات في محرك التوجيه الذكي (Smart Routing)</p>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="openCreate"
            class="bg-success text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-success/90 transition-colors cursor-pointer flex items-center gap-1.5"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            إضافة جهة جديدة
          </button>
          <button
            v-if="hasChanges"
            @click="saveReorder"
            :disabled="saving"
            class="bg-blue text-white text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-blue/90 transition-colors disabled:opacity-50 cursor-pointer flex items-center gap-2"
          >
            <svg v-if="saving" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            حفظ الترتيب
          </button>
        </div>
      </div>

      <!-- Info Banner -->
      <div class="bg-blue/5 border border-blue/20 rounded-2xl p-4 mb-5">
        <div class="flex gap-3">
          <div class="flex-shrink-0 mt-0.5">
            <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <div class="text-sm text-brand leading-relaxed">
            <p class="font-semibold mb-1">كيف يعمل محرك التوجيه الذكي؟</p>
            <ul class="list-disc list-inside space-y-0.5 text-text-light">
              <li>يتم تقييم الجهات <strong class="text-brand">بالتسلسل</strong> حسب الأولوية (الأقل رقمًا = الأعلى أولوية)</li>
              <li>عند العثور على أول جهة مؤهلة يتوقف التقييم فورًا</li>
              <li>الشريك <strong class="text-brand">لا يعرف</strong> أي جهة رفضته — يرى فقط "مؤهل" أو "غير مؤهل"</li>
              <li>تغيير الترتيب لا يؤثر على الطلبات الجارية</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-16">
        <div class="w-8 h-8 border-3 border-blue/30 border-t-blue rounded-full animate-spin"></div>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="bg-danger/5 border border-danger/20 text-danger rounded-2xl p-4 text-sm text-center">
        {{ error }}
        <button @click="loadRules" class="underline mr-2 cursor-pointer">إعادة المحاولة</button>
      </div>

      <!-- Entity List -->
      <div v-else class="space-y-3">
        <div
          v-for="(rule, index) in localRules"
          :key="rule.id"
          class="bg-white rounded-2xl border border-border overflow-hidden transition-all"
          :class="{ 'opacity-50': !rule.is_active, 'ring-2 ring-blue/30': dragIndex === index }"
          draggable="true"
          @dragstart="onDragStart(index)"
          @dragover.prevent="onDragOver(index)"
          @dragend="onDragEnd"
        >
          <div class="flex items-stretch">
            <!-- Drag handle -->
            <div class="w-12 flex-shrink-0 bg-bg/50 flex flex-col items-center justify-center gap-1 cursor-grab active:cursor-grabbing border-l border-border">
              <svg class="w-5 h-5 text-text-light" fill="currentColor" viewBox="0 0 24 24">
                <circle cx="9" cy="6" r="1.5"/><circle cx="15" cy="6" r="1.5"/>
                <circle cx="9" cy="12" r="1.5"/><circle cx="15" cy="12" r="1.5"/>
                <circle cx="9" cy="18" r="1.5"/><circle cx="15" cy="18" r="1.5"/>
              </svg>
              <span class="text-xs font-bold text-text-light">{{ index + 1 }}</span>
            </div>

            <!-- Entity content -->
            <div class="flex-1 p-4">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <span class="text-base font-bold text-brand">{{ rule.entity_name }}</span>
                  <span class="text-xs font-mono bg-bg text-text-light px-2 py-0.5 rounded-lg">{{ rule.product_code }}</span>
                  <span v-if="rule.product_name" class="text-xs bg-blue/10 text-blue px-2 py-0.5 rounded-lg">{{ rule.product_name }}</span>
                  <span
                    :class="rule.is_active ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'"
                    class="text-xs font-semibold px-2 py-0.5 rounded-lg"
                  >
                    {{ rule.is_active ? 'مفعّلة' : 'معطّلة' }}
                  </span>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    @click="openEdit(rule)"
                    class="text-sm px-3 py-1.5 rounded-lg border border-blue/30 text-blue hover:bg-blue/5 transition-colors cursor-pointer"
                  >
                    تعديل
                  </button>
                  <button
                    @click="toggleEntity(rule)"
                    :disabled="toggling === rule.id"
                    class="text-sm px-3 py-1.5 rounded-lg border transition-colors cursor-pointer"
                    :class="rule.is_active
                      ? 'border-danger/30 text-danger hover:bg-danger/5'
                      : 'border-success/30 text-success hover:bg-success/5'"
                  >
                    {{ rule.is_active ? 'تعطيل' : 'تفعيل' }}
                  </button>
                </div>
              </div>

              <!-- Priority & facility types -->
              <div class="flex items-center gap-4 mb-2 flex-wrap">
                <div class="flex items-center gap-1">
                  <span class="text-xs text-text-light">الأولوية:</span>
                  <input
                    type="number"
                    v-model.number="rule.priority"
                    min="1"
                    class="w-16 text-center text-sm font-bold border border-border rounded-lg px-2 py-1 focus:ring-2 focus:ring-blue/30 focus:border-blue outline-none"
                    @input="markChanged"
                  />
                </div>
                <span class="text-xs text-text-light">بادئة كود العرض: <strong class="text-brand">{{ rule.offer_code_prefix }}</strong></span>
                <div class="flex items-center gap-1">
                  <span class="text-xs text-text-light">أنواع التسهيلات:</span>
                  <span v-for="ft in (rule.facility_types || [])" :key="ft" class="text-[11px] bg-blue/5 text-blue border border-blue/10 px-2 py-0.5 rounded-lg">
                    {{ ft === 'pos' ? 'نقاط بيع' : ft === 'cash' ? 'كاش' : ft === 'fleet' ? 'أسطول' : ft }}
                  </span>
                </div>
              </div>

              <!-- Description -->
              <p v-if="rule.description" class="text-xs text-text-light leading-relaxed mb-2">{{ rule.description }}</p>

              <!-- Required docs -->
              <div v-if="rule.required_docs && rule.required_docs.length" class="mt-2">
                <p class="text-xs font-semibold text-brand mb-1">المستندات المطلوبة:</p>
                <div class="flex flex-wrap gap-1.5">
                  <span
                    v-for="doc in rule.required_docs"
                    :key="doc"
                    class="text-[11px] bg-blue/5 text-blue border border-blue/10 px-2 py-0.5 rounded-lg"
                  >
                    {{ doc }}
                  </span>
                </div>
              </div>

              <!-- Key thresholds (collapsed) -->
              <details class="mt-3">
                <summary class="text-xs text-blue cursor-pointer hover:underline">عرض معايير القبول</summary>
                <div class="mt-2 space-y-2">
                  <!-- Pre-filter conditions -->
                  <p class="text-xs font-semibold text-brand">شروط التصفية المبدئية (قبل كشف الحساب):</p>
                  <div class="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                    <div class="bg-bg rounded-lg p-2">
                      <p class="text-text-light">عمر السجل الأدنى</p>
                      <p class="font-bold text-brand">≥ {{ rule.min_age_months }} شهر</p>
                    </div>
                    <div class="bg-bg rounded-lg p-2">
                      <p class="text-text-light">يتطلب POS</p>
                      <p class="font-bold text-brand">{{ rule.requires_pos ? 'نعم' : 'لا' }}</p>
                    </div>
                    <div class="bg-bg rounded-lg p-2">
                      <p class="text-text-light">يتطلب فواتير</p>
                      <p class="font-bold text-brand">{{ rule.requires_invoices ? 'نعم' : 'لا' }}</p>
                    </div>
                    <div class="bg-bg rounded-lg p-2">
                      <p class="text-text-light">أقصى عدد شركاء</p>
                      <p class="font-bold text-brand">{{ rule.max_partners ?? 'بلا حد' }}</p>
                    </div>
                    <div class="bg-bg rounded-lg p-2">
                      <p class="text-text-light">يقبل أجانب</p>
                      <p class="font-bold text-brand">{{ rule.accepts_foreign ? 'نعم' : 'لا' }}</p>
                    </div>
                    <div v-if="rule.blocked_activities?.length" class="bg-bg rounded-lg p-2 col-span-2">
                      <p class="text-text-light">أنشطة محظورة</p>
                      <p class="font-bold text-danger">{{ rule.blocked_activities.join('، ') }}</p>
                    </div>
                  </div>

                  <!-- Financial conditions -->
                  <p class="text-xs font-semibold text-brand mt-3">شروط مالية (بعد كشف الحساب):</p>
                  <div class="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
                    <div v-if="rule.min_pos_rajhi" class="bg-bg rounded-lg p-2">
                      <p class="text-text-light">POS (حساب راجحي)</p>
                      <p class="font-bold text-brand">≥ {{ formatNum(rule.min_pos_rajhi) }} ر.س</p>
                    </div>
                    <div v-if="rule.min_pos_other" class="bg-bg rounded-lg p-2">
                      <p class="text-text-light">POS (حسابات أخرى)</p>
                      <p class="font-bold text-brand">≥ {{ formatNum(rule.min_pos_other) }} ر.س</p>
                    </div>
                    <div v-if="rule.min_total_deposits" class="bg-bg rounded-lg p-2">
                      <p class="text-text-light">إجمالي الإيداعات</p>
                      <p class="font-bold text-brand">≥ {{ formatNum(rule.min_total_deposits) }} ر.س</p>
                    </div>
                    <div v-if="rule.min_total_revenue" class="bg-bg rounded-lg p-2">
                      <p class="text-text-light">إجمالي الإيرادات</p>
                      <p class="font-bold text-brand">≥ {{ formatNum(rule.min_total_revenue) }} ر.س</p>
                    </div>
                    <div v-if="rule.min_profit_ratio" class="bg-bg rounded-lg p-2">
                      <p class="text-text-light">نسبة صافي الربح</p>
                      <p class="font-bold text-brand">≥ {{ (rule.min_profit_ratio * 100).toFixed(0) }}%</p>
                    </div>
                    <div v-if="rule.requires_stability_check" class="bg-bg rounded-lg p-2">
                      <p class="text-text-light">فحص الاستقرار</p>
                      <p class="font-bold text-brand">لا انخفاض > 20%</p>
                    </div>
                    <div v-if="rule.tax_returns_count" class="bg-bg rounded-lg p-2">
                      <p class="text-text-light">إقرارات زكوية</p>
                      <p class="font-bold text-brand">{{ rule.tax_returns_count }} ({{ rule.tax_returns_frequency || 'ربع سنوي' }})</p>
                    </div>
                    <div v-if="rule.financial_statement_rule" class="bg-bg rounded-lg p-2">
                      <p class="text-text-light">القوائم المالية</p>
                      <p class="font-bold text-brand">{{ rule.financial_statement_rule === 'certified' ? 'معتمدة' : rule.financial_statement_rule === 'internal' ? 'داخلية' : rule.financial_statement_rule }}</p>
                    </div>
                    <div v-if="!rule.min_pos_rajhi && !rule.min_pos_other && !rule.min_total_deposits && !rule.min_total_revenue && !rule.min_profit_ratio" class="bg-bg rounded-lg p-2 col-span-2">
                      <p class="text-text-light">لا توجد شروط مالية إضافية</p>
                    </div>
                  </div>
                </div>
              </details>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="localRules.length === 0" class="bg-white rounded-2xl border border-border p-10 text-center">
          <svg class="w-12 h-12 mx-auto text-text-light/50 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
          </svg>
          <p class="text-sm text-text-light">لم يتم إضافة أي جهات تمويلية</p>
        </div>
      </div>

      <!-- Duplicate priority warning -->
      <div v-if="hasDuplicatePriorities" class="mt-4 bg-warning/10 border border-warning/30 rounded-2xl p-3 flex items-center gap-2">
        <svg class="w-5 h-5 text-warning flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/>
        </svg>
        <p class="text-sm text-warning font-semibold">تحذير: توجد أولويات مكررة — كل جهة يجب أن تحصل على أولوية فريدة</p>
      </div>

      <!-- Success toast -->
      <Transition name="toast">
        <div v-if="toastMessage" class="fixed bottom-6 left-1/2 -translate-x-1/2 bg-brand text-white text-sm font-semibold px-6 py-3 rounded-2xl shadow-xl z-50 flex items-center gap-2">
          <svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
          </svg>
          {{ toastMessage }}
        </div>
      </Transition>
    </main>
  </div>

  <!-- Create Modal -->
  <Teleport to="body">
    <div v-if="showCreate" class="fixed inset-0 z-50 flex items-start justify-center p-4 bg-black/40 overflow-y-auto" @click.self="showCreate = false">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl my-6 p-6" @click.stop>
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-lg font-bold text-brand">إضافة جهة تمويلية جديدة</h3>
          <button @click="showCreate = false" class="text-text-light hover:text-danger cursor-pointer">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="space-y-5">
          <!-- اسم الجهة + اسم المنتج -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">اسم الجهة <span class="text-danger">*</span></label>
              <input v-model="createForm.entity_name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="مثال: مصرف الراجحي" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">اسم المنتج <span class="text-danger">*</span></label>
              <input v-model="createForm.product_name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="مثال: نقاط بيع" />
            </div>
          </div>

          <!-- كود الجهة + كود المنتج + بادئة العرض -->
          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">كود الجهة <span class="text-danger">*</span></label>
              <input v-model="createForm.entity_code" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue font-mono" placeholder="RAJHI" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">كود المنتج <span class="text-danger">*</span></label>
              <input v-model="createForm.product_code" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue font-mono" placeholder="RAJHI_POS" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">بادئة كود العرض</label>
              <input v-model="createForm.offer_code_prefix" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue font-mono" placeholder="RAJ" />
            </div>
          </div>

          <!-- أنواع التسهيلات -->
          <div>
            <label class="block text-xs font-medium text-text-light mb-2">أنواع التسهيلات <span class="text-danger">*</span></label>
            <div class="flex gap-4">
              <label class="flex items-center gap-2 cursor-pointer text-sm">
                <input type="checkbox" :checked="createForm.facility_types.includes('pos')" @change="toggleFacility('pos')" class="w-4 h-4" />
                نقاط بيع (POS)
              </label>
              <label class="flex items-center gap-2 cursor-pointer text-sm">
                <input type="checkbox" :checked="createForm.facility_types.includes('cash')" @change="toggleFacility('cash')" class="w-4 h-4" />
                كاش
              </label>
              <label class="flex items-center gap-2 cursor-pointer text-sm">
                <input type="checkbox" :checked="createForm.facility_types.includes('fleet')" @change="toggleFacility('fleet')" class="w-4 h-4" />
                أسطول
              </label>
            </div>
          </div>

          <!-- الوصف -->
          <div>
            <label class="block text-xs font-medium text-text-light mb-1">شرح / الوصف</label>
            <textarea v-model="createForm.description" rows="2" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue resize-none" placeholder="شرح مختصر عن هذه الجهة..."></textarea>
          </div>

          <!-- المستندات المطلوبة -->
          <div>
            <label class="block text-xs font-medium text-text-light mb-2">المستندات المطلوبة</label>
            <div class="space-y-2 mb-2">
              <div v-for="(doc, i) in createForm.required_docs" :key="i" class="flex items-center gap-2">
                <input
                  v-model="createForm.required_docs[i]"
                  class="flex-1 px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue"
                  :placeholder="'مستند ' + (i+1)"
                />
                <button @click="createForm.required_docs.splice(i, 1)" class="text-danger hover:text-red-700 cursor-pointer flex-shrink-0">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
              </div>
            </div>
            <button @click="createForm.required_docs.push('')" class="text-sm text-blue hover:underline cursor-pointer flex items-center gap-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
              إضافة مستند
            </button>
          </div>

          <!-- معايير القبول -->
          <details class="border border-border rounded-xl">
            <summary class="px-4 py-3 text-sm font-semibold text-brand cursor-pointer">معايير القبول (اختياري)</summary>
            <div class="px-4 pb-4 pt-2 grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">الأولوية (كلما قل الرقم كلما كان أعلى)</label>
                <input type="number" v-model.number="createForm.priority" class="w-full px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">عمر السجل الأدنى (شهر)</label>
                <input type="number" v-model.number="createForm.min_age_months" class="w-full px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">أقصى عدد شركاء</label>
                <input type="number" v-model.number="createForm.max_partners" class="w-full px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="بلا حد" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">حد POS راجحي (ر.س)</label>
                <input type="number" v-model.number="createForm.min_pos_rajhi" class="w-full px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">حد POS أخرى (ر.س)</label>
                <input type="number" v-model.number="createForm.min_pos_other" class="w-full px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">حد الإيداعات (ر.س)</label>
                <input type="number" v-model.number="createForm.min_total_deposits" class="w-full px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">حد الإيرادات (ر.س)</label>
                <input type="number" v-model.number="createForm.min_total_revenue" class="w-full px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div class="col-span-2 flex flex-wrap gap-4">
                <label class="flex items-center gap-2 cursor-pointer text-sm">
                  <input type="checkbox" v-model="createForm.requires_pos" class="w-4 h-4" />
                  يتطلب POS
                </label>
                <label class="flex items-center gap-2 cursor-pointer text-sm">
                  <input type="checkbox" v-model="createForm.requires_invoices" class="w-4 h-4" />
                  يتطلب فواتير
                </label>
                <label class="flex items-center gap-2 cursor-pointer text-sm">
                  <input type="checkbox" v-model="createForm.accepts_foreign" class="w-4 h-4" />
                  يقبل أجانب
                </label>
              </div>
            </div>
          </details>

          <!-- خطأ -->
          <p v-if="createError" class="text-sm text-danger bg-danger/5 rounded-xl px-3 py-2">{{ createError }}</p>

          <!-- أزرار -->
          <div class="flex gap-2 pt-1">
            <button
              @click="saveCreate"
              :disabled="createSaving"
              class="flex-1 py-2.5 rounded-xl bg-success text-white text-sm font-semibold hover:bg-success/90 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {{ createSaving ? 'جاري الإضافة...' : 'إضافة الجهة' }}
            </button>
            <button @click="showCreate = false" class="px-5 py-2.5 rounded-xl bg-gray-100 text-text-light text-sm hover:bg-gray-200 transition-colors cursor-pointer">
              إلغاء
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Edit Modal -->
  <Teleport to="body">
    <div v-if="editRule" class="fixed inset-0 z-50 flex items-start justify-center p-4 bg-black/40 overflow-y-auto" @click.self="editRule = null">
      <div class="bg-white rounded-2xl shadow-xl w-full max-w-2xl my-6 p-6" @click.stop>
        <div class="flex items-center justify-between mb-5">
          <h3 class="text-lg font-bold text-brand">تعديل: {{ editRule.entity_name }}</h3>
          <button @click="editRule = null" class="text-text-light hover:text-danger cursor-pointer">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="space-y-5">
          <!-- Name + product name -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">اسم الجهة</label>
              <input v-model="editForm.entity_name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
            </div>
            <div>
              <label class="block text-xs font-medium text-text-light mb-1">اسم المنتج</label>
              <input v-model="editForm.product_name" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
            </div>
          </div>

          <!-- Description -->
          <div>
            <label class="block text-xs font-medium text-text-light mb-1">شرح / الوصف</label>
            <textarea v-model="editForm.description" rows="3" class="w-full px-3 py-2 text-sm border border-border rounded-xl focus:outline-none focus:border-blue resize-none" placeholder="شرح عن هذه الجهة ومتطلباتها..."></textarea>
          </div>

          <!-- Required docs -->
          <div>
            <label class="block text-xs font-medium text-text-light mb-2">المستندات المطلوبة</label>
            <div class="space-y-2 mb-2">
              <div v-for="(doc, i) in editForm.required_docs" :key="i" class="flex items-center gap-2">
                <input
                  v-model="editForm.required_docs[i]"
                  class="flex-1 px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue"
                  :placeholder="'مستند ' + (i+1)"
                />
                <button @click="removeDoc(i)" class="text-danger hover:text-red-700 cursor-pointer flex-shrink-0">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
                </button>
              </div>
            </div>
            <button @click="addDoc" class="text-sm text-blue hover:underline cursor-pointer flex items-center gap-1">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
              إضافة مستند
            </button>
          </div>

          <!-- Key thresholds -->
          <details class="border border-border rounded-xl">
            <summary class="px-4 py-3 text-sm font-semibold text-brand cursor-pointer">معايير القبول (اختياري)</summary>
            <div class="px-4 pb-4 pt-2 grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">عمر السجل الأدنى (شهر)</label>
                <input type="number" v-model.number="editForm.min_age_months" class="w-full px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">أقصى عدد شركاء</label>
                <input type="number" v-model.number="editForm.max_partners" class="w-full px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" placeholder="بلا حد" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">حد إيداعات راجحي (ر.س)</label>
                <input type="number" v-model.number="editForm.min_pos_rajhi" class="w-full px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">حد إيداعات أخرى (ر.س)</label>
                <input type="number" v-model.number="editForm.min_pos_other" class="w-full px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">حد إجمالي الإيداعات (ر.س)</label>
                <input type="number" v-model.number="editForm.min_total_deposits" class="w-full px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div>
                <label class="block text-xs font-medium text-text-light mb-1">حد إجمالي الإيرادات (ر.س)</label>
                <input type="number" v-model.number="editForm.min_total_revenue" class="w-full px-3 py-1.5 text-sm border border-border rounded-xl focus:outline-none focus:border-blue" />
              </div>
              <div class="col-span-2 flex gap-4">
                <label class="flex items-center gap-2 cursor-pointer text-sm">
                  <input type="checkbox" v-model="editForm.requires_pos" class="w-4 h-4" />
                  يتطلب POS
                </label>
                <label class="flex items-center gap-2 cursor-pointer text-sm">
                  <input type="checkbox" v-model="editForm.requires_invoices" class="w-4 h-4" />
                  يتطلب فواتير
                </label>
                <label class="flex items-center gap-2 cursor-pointer text-sm">
                  <input type="checkbox" v-model="editForm.accepts_foreign" class="w-4 h-4" />
                  يقبل أجانب
                </label>
              </div>
            </div>
          </details>

          <!-- Error -->
          <p v-if="editError" class="text-sm text-danger">{{ editError }}</p>

          <!-- Actions -->
          <div class="flex gap-2 pt-1">
            <button
              @click="saveEdit"
              :disabled="editSaving"
              class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-semibold hover:bg-blue/90 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {{ editSaving ? 'جاري الحفظ...' : 'حفظ التعديلات' }}
            </button>
            <button @click="editRule = null" class="px-5 py-2.5 rounded-xl bg-gray-100 text-text-light text-sm hover:bg-gray-200 transition-colors cursor-pointer">
              إلغاء
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { entityRulesApi } from '../../api/client'
import { logout } from '../../stores/authStore'
import NotificationBell from '../../components/NotificationBell.vue'

const router = useRouter()

// State
const loading = ref(true)
const error = ref('')
const saving = ref(false)
const toggling = ref<string | null>(null)
const toastMessage = ref('')
const localRules = ref<any[]>([])
const originalPriorities = ref<Record<string, number>>({})
const dragIndex = ref<number | null>(null)

// Computed
const hasChanges = computed(() => {
  return localRules.value.some(r => r.priority !== originalPriorities.value[r.id])
})

const hasDuplicatePriorities = computed(() => {
  const priorities = localRules.value.map(r => r.priority)
  return new Set(priorities).size !== priorities.length
})

// Load rules
async function loadRules() {
  loading.value = true
  error.value = ''
  try {
    const rules = await entityRulesApi.list()
    localRules.value = rules.sort((a: any, b: any) => a.priority - b.priority)
    originalPriorities.value = {}
    rules.forEach((r: any) => {
      originalPriorities.value[r.id] = r.priority
    })
  } catch (e: any) {
    error.value = e.message || 'حدث خطأ في تحميل الجهات'
  } finally {
    loading.value = false
  }
}

// Drag & drop
function onDragStart(index: number) {
  dragIndex.value = index
}

function onDragOver(index: number) {
  if (dragIndex.value === null || dragIndex.value === index) return

  const rules = [...localRules.value]
  const [moved] = rules.splice(dragIndex.value, 1)
  rules.splice(index, 0, moved)

  // Reassign priorities based on new order
  rules.forEach((r, i) => {
    r.priority = i + 1
  })

  localRules.value = rules
  dragIndex.value = index
}

function onDragEnd() {
  dragIndex.value = null
}

function markChanged() {
  // Trigger reactivity — priorities edited via input
}

// Save reorder
async function saveReorder() {
  if (hasDuplicatePriorities.value) return

  saving.value = true
  try {
    const items = localRules.value.map(r => ({ id: r.id, priority: r.priority }))
    const updated = await entityRulesApi.reorder(items)
    localRules.value = updated.sort((a: any, b: any) => a.priority - b.priority)
    originalPriorities.value = {}
    updated.forEach((r: any) => {
      originalPriorities.value[r.id] = r.priority
    })
    showToast('تم حفظ ترتيب الأولويات بنجاح')
  } catch (e: any) {
    error.value = e.message || 'فشل في حفظ الترتيب'
  } finally {
    saving.value = false
  }
}

// Toggle entity
async function toggleEntity(rule: any) {
  toggling.value = rule.id
  try {
    const res = await entityRulesApi.toggle(rule.id)
    rule.is_active = res.is_active
    showToast(`${rule.entity_name}: ${res.status}`)
  } catch (e: any) {
    error.value = e.message || 'فشل في تغيير الحالة'
  } finally {
    toggling.value = null
  }
}

// Edit modal
const editRule = ref<any>(null)
const editSaving = ref(false)
const editError = ref('')
const editForm = ref<any>({})

// Create modal
const showCreate = ref(false)
const createSaving = ref(false)
const createError = ref('')
const createForm = ref<any>({})

function openCreate() {
  createError.value = ''
  createForm.value = {
    entity_name: '',
    entity_code: '',
    product_code: '',
    product_name: '',
    offer_code_prefix: '',
    facility_types: ['pos'],
    description: '',
    required_docs: [],
    priority: (localRules.value.length ? Math.max(...localRules.value.map(r => r.priority)) + 1 : 1),
    min_age_months: 12,
    max_partners: '',
    min_pos_rajhi: '',
    min_pos_other: '',
    min_total_deposits: '',
    min_total_revenue: '',
    requires_pos: false,
    requires_invoices: false,
    accepts_foreign: true,
  }
  showCreate.value = true
}

function toggleFacility(ft: string) {
  const arr: string[] = createForm.value.facility_types
  const idx = arr.indexOf(ft)
  if (idx === -1) arr.push(ft)
  else if (arr.length > 1) arr.splice(idx, 1)
}

async function saveCreate() {
  createError.value = ''
  if (!createForm.value.entity_name.trim()) { createError.value = 'اسم الجهة مطلوب'; return }
  if (!createForm.value.entity_code.trim()) { createError.value = 'كود الجهة مطلوب'; return }
  if (!createForm.value.product_code.trim()) { createError.value = 'كود المنتج مطلوب'; return }
  if (!createForm.value.product_name.trim()) { createError.value = 'اسم المنتج مطلوب'; return }
  if (!createForm.value.facility_types.length) { createError.value = 'اختر نوع تسهيل واحد على الأقل'; return }

  createSaving.value = true
  try {
    const payload: any = {
      entity_name: createForm.value.entity_name.trim(),
      entity_code: createForm.value.entity_code.trim().toUpperCase(),
      product_code: createForm.value.product_code.trim().toUpperCase(),
      product_name: createForm.value.product_name.trim(),
      offer_code_prefix: createForm.value.offer_code_prefix.trim().toUpperCase(),
      facility_types: createForm.value.facility_types,
      description: createForm.value.description.trim(),
      required_docs: createForm.value.required_docs.filter((d: string) => d.trim()),
      priority: Number(createForm.value.priority) || 100,
      min_age_months: Number(createForm.value.min_age_months) || 6,
      max_partners: createForm.value.max_partners === '' ? null : Number(createForm.value.max_partners),
      min_pos_rajhi: createForm.value.min_pos_rajhi === '' ? null : Number(createForm.value.min_pos_rajhi),
      min_pos_other: createForm.value.min_pos_other === '' ? null : Number(createForm.value.min_pos_other),
      min_total_deposits: createForm.value.min_total_deposits === '' ? null : Number(createForm.value.min_total_deposits),
      min_total_revenue: createForm.value.min_total_revenue === '' ? null : Number(createForm.value.min_total_revenue),
      requires_pos: createForm.value.requires_pos,
      requires_invoices: createForm.value.requires_invoices,
      accepts_foreign: createForm.value.accepts_foreign,
    }
    const newRule = await entityRulesApi.create(payload)
    localRules.value.push(newRule)
    localRules.value.sort((a: any, b: any) => a.priority - b.priority)
    originalPriorities.value[newRule.id] = newRule.priority
    showCreate.value = false
    showToast(`تمت إضافة ${newRule.entity_name} بنجاح`)
  } catch (e: any) {
    createError.value = e.message || 'فشل في إضافة الجهة'
  } finally {
    createSaving.value = false
  }
}

function openEdit(rule: any) {
  editRule.value = rule
  editError.value = ''
  editForm.value = {
    entity_name: rule.entity_name,
    product_name: rule.product_name,
    description: rule.description || '',
    required_docs: [...(rule.required_docs || [])],
    min_age_months: rule.min_age_months,
    max_partners: rule.max_partners ?? '',
    min_pos_rajhi: rule.min_pos_rajhi ?? '',
    min_pos_other: rule.min_pos_other ?? '',
    min_total_deposits: rule.min_total_deposits ?? '',
    min_total_revenue: rule.min_total_revenue ?? '',
    requires_pos: rule.requires_pos,
    requires_invoices: rule.requires_invoices,
    accepts_foreign: rule.accepts_foreign,
  }
}

function addDoc() {
  editForm.value.required_docs.push('')
}

function removeDoc(i: number) {
  editForm.value.required_docs.splice(i, 1)
}

async function saveEdit() {
  if (!editRule.value) return
  editError.value = ''
  editSaving.value = true
  try {
    const payload: any = {
      entity_name: editForm.value.entity_name,
      product_name: editForm.value.product_name,
      description: editForm.value.description,
      required_docs: editForm.value.required_docs.filter((d: string) => d.trim()),
      min_age_months: editForm.value.min_age_months,
      max_partners: editForm.value.max_partners === '' ? null : Number(editForm.value.max_partners),
      min_pos_rajhi: editForm.value.min_pos_rajhi === '' ? null : Number(editForm.value.min_pos_rajhi),
      min_pos_other: editForm.value.min_pos_other === '' ? null : Number(editForm.value.min_pos_other),
      min_total_deposits: editForm.value.min_total_deposits === '' ? null : Number(editForm.value.min_total_deposits),
      min_total_revenue: editForm.value.min_total_revenue === '' ? null : Number(editForm.value.min_total_revenue),
      requires_pos: editForm.value.requires_pos,
      requires_invoices: editForm.value.requires_invoices,
      accepts_foreign: editForm.value.accepts_foreign,
    }
    const updated = await entityRulesApi.update(editRule.value.id, payload)
    // Update in-place
    const idx = localRules.value.findIndex(r => r.id === editRule.value.id)
    if (idx !== -1) localRules.value[idx] = { ...localRules.value[idx], ...updated }
    editRule.value = null
    showToast(`تم حفظ تعديلات ${updated.entity_name}`)
  } catch (e: any) {
    editError.value = e.message || 'فشل في حفظ التعديلات'
  } finally {
    editSaving.value = false
  }
}

// Utils
function formatNum(n: number) {
  return new Intl.NumberFormat('ar-SA').format(n)
}

function showToast(msg: string) {
  toastMessage.value = msg
  setTimeout(() => { toastMessage.value = '' }, 3000)
}

function handleLogout() {
  logout()
  router.push('/login')
}

onMounted(loadRules)
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, 10px);
}
</style>
