<template>
  <div class="min-h-screen min-h-dvh bg-bg">
    <!-- Top bar -->
    <header class="bg-white border-b border-border sticky top-0 z-30">
      <div class="max-w-lg mx-auto px-4 h-14 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <button @click="$router.back()" class="text-text-light hover:text-brand transition-colors cursor-pointer p-1">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </button>
          <h1 class="text-sm font-bold text-brand">تحميل المستندات</h1>
        </div>
      </div>
    </header>

    <main class="max-w-lg mx-auto px-4 pb-8">
      <!-- Case Info -->
      <div class="mt-6 mb-6 bg-white rounded-2xl border border-border p-4">
        <div class="flex items-center gap-3 mb-2">
          <div class="w-10 h-10 rounded-xl bg-blue/10 flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5 text-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
          </div>
          <div>
            <p class="text-sm font-bold text-brand">طلب رقم {{ displayId }}</p>
            <p class="text-xs text-text-light">المرحلة الحالية: تحميل المستندات</p>
          </div>
        </div>
      </div>

      <!-- Required Documents List -->
      <div class="mb-4">
        <h2 class="text-base font-bold text-brand mb-3">المستندات المطلوبة</h2>
        <p class="text-xs text-text-light mb-4">يرجى تحميل جميع المستندات التالية لاستكمال الطلب</p>
      </div>

      <div class="space-y-3">
        <div
          v-for="(doc, idx) in requiredDocuments"
          :key="idx"
          class="bg-white rounded-2xl border border-border p-4"
          :class="{ 'border-success/50 bg-success/5': doc.uploaded }"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-start gap-3 flex-1">
              <div
                class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                :class="doc.uploaded ? 'bg-success/10' : 'bg-gray-100'"
              >
                <svg v-if="doc.uploaded" class="w-4 h-4 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <svg v-else class="w-4 h-4 text-text-light" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-brand">{{ doc.name }}</p>
                <p v-if="doc.uploadedName" class="text-xs text-success mt-1">
                  ✓ {{ doc.uploadedName }}
                </p>
                <p class="text-xs text-text-light mt-0.5">
                  {{ doc.required ? 'مطلوب' : 'اختياري' }} — {{ doc.hint }}
                </p>
              </div>
            </div>

            <label
              class="flex-shrink-0 cursor-pointer bg-blue/10 text-blue text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-blue/20 transition-colors"
            >
              {{ doc.uploaded ? 'تغيير' : 'تحميل' }}
              <input
                type="file"
                :accept="doc.accept"
                class="hidden"
                @change="(e: Event) => handleFileSelect(idx, e)"
              />
            </label>
          </div>
        </div>
      </div>

      <!-- Success result screen -->
      <div v-if="uploadDone" class="mt-6 bg-white rounded-2xl border border-success/30 p-6 text-center">
        <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-success/10 flex items-center justify-center">
          <svg class="w-8 h-8 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <h3 class="text-lg font-bold text-success mb-1">{{ successMsg }}</h3>
        <p class="text-xs text-text-light mb-4">تم تحليل المستندات بالذكاء الاصطناعي وانتقل الطلب للمرحلة التالية</p>

        <!-- AI Summary -->
        <div v-if="aiSummary" class="bg-blue/5 border border-blue/20 rounded-xl p-4 text-right mb-5">
          <div class="flex items-center gap-2 mb-2">
            <svg class="w-4 h-4 text-blue flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
            </svg>
            <span class="text-xs font-bold text-blue">تحليل الذكاء الاصطناعي</span>
          </div>
          <p class="text-sm text-brand leading-relaxed">{{ aiSummary }}</p>
        </div>

        <!-- Uploaded docs list -->
        <div class="bg-bg rounded-xl p-3 text-right mb-5">
          <p class="text-xs font-bold text-brand mb-2">المستندات المرفوعة:</p>
          <ul class="space-y-1">
            <li v-for="doc in requiredDocuments.filter(d => d.uploaded)" :key="doc.name"
              class="flex items-center gap-2 text-xs text-text-light">
              <svg class="w-3.5 h-3.5 text-success flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
              </svg>
              {{ doc.name }}
            </li>
          </ul>
        </div>

        <button
          @click="goToCase"
          class="w-full py-3.5 rounded-2xl bg-blue text-white font-bold text-sm shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all cursor-pointer"
        >
          عرض تفاصيل الطلب ←
        </button>
      </div>

      <!-- Upload button (shown when not done) -->
      <div v-else class="mt-6">
        <div class="flex items-center justify-between mb-3">
          <p class="text-sm text-text-light">
            {{ uploadedCount }} من {{ requiredDocuments.length }} مستند تم تحميله
          </p>
          <div class="w-24 h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div class="h-full bg-blue rounded-full transition-all"
              :style="{ width: `${(uploadedCount / requiredDocuments.length) * 100}%` }">
            </div>
          </div>
        </div>

        <!-- Upload progress bar (while submitting) -->
        <div v-if="submitting" class="mb-3">
          <div class="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <div class="h-full bg-blue rounded-full transition-all duration-700"
              :style="{ width: uploadProgress + '%' }">
            </div>
          </div>
          <p class="text-xs text-blue text-center mt-1">جاري رفع الملفات وتحليلها بالذكاء الاصطناعي...</p>
        </div>

        <button
          @click="submitDocuments"
          :disabled="uploadedCount < requiredCount || submitting"
          class="w-full py-3.5 rounded-2xl bg-blue text-white font-bold text-sm shadow-lg shadow-blue/25 hover:bg-blue-dark active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center justify-center gap-2"
        >
          <svg v-if="submitting" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
          <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
          </svg>
          {{ submitting ? 'جاري التحليل...' : 'تأكيد تحميل المستندات' }}
        </button>

        <p v-if="uploadedCount < requiredCount" class="text-xs text-warning text-center mt-2">
          يجب تحميل جميع المستندات المطلوبة ({{ requiredCount }} مستند)
        </p>

        <p v-if="errorMsg" class="text-xs text-danger text-center mt-2 font-medium bg-danger/5 rounded-xl p-3">
          {{ errorMsg }}
        </p>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { analysisApi, casesApi } from '../../api/client'

const route = useRoute()
const router = useRouter()
const caseId = computed(() => route.params.id as string)
const displayId = computed(() => caseId.value?.substring(0, 8) || '')
const submitting = ref(false)
const uploadProgress = ref(0)
const successMsg = ref('')
const errorMsg = ref('')
const aiSummary = ref('')
const uploadDone = ref(false)

type DocItem = { name: string; required: boolean; uploaded: boolean; uploadedName: string; file: File | null; accept: string; hint: string }

function makeDoc(name: string, required = true, accept = '.pdf,.png,.jpg,.jpeg', hint = 'PDF أو صورة'): DocItem {
  return { name, required, uploaded: false, uploadedName: '', file: null, accept, hint }
}

const defaultDocs: DocItem[] = [
  makeDoc('صورة السجل التجاري'),
  makeDoc('صورة الهوية / الإقامة'),
  makeDoc('عقد التأسيس (إن كانت شركة)', false),
  makeDoc('شهادة البلدية'),
  makeDoc('شهادة التوطين'),
  makeDoc('العنوان الوطني للمنشأة والملاك'),
  makeDoc('شهادة الآيبان بالباركود'),
  makeDoc('صور النشاط (داخل وخارج)', true, '.pdf,.png,.jpg,.jpeg,.heic,.webp'),
  makeDoc('موقع المنشأة Google Map', false),
  makeDoc('كشف الحساب البنكي', true, '.pdf,.xlsx,.xls,.png,.jpg,.jpeg', 'PDF أو Excel (.xlsx/.xls)'),
]

const requiredDocuments = ref<DocItem[]>([])

onMounted(async () => {
  try {
    const caseData = await casesApi.get(caseId.value)
    const aiDocs: string[] = caseData.analysis_result?.required_docs || []
    if (aiDocs.length > 0) {
      requiredDocuments.value = aiDocs.map(name => makeDoc(name))
      // Ensure bank statement is included
      const hasBs = aiDocs.some(d => d.includes('كشف') || d.toLowerCase().includes('statement'))
      if (!hasBs) requiredDocuments.value.push(makeDoc('كشف الحساب البنكي', true, '.pdf,.xlsx,.xls,.png,.jpg,.jpeg', 'PDF أو Excel'))
    } else {
      requiredDocuments.value = [...defaultDocs]
    }
  } catch {
    requiredDocuments.value = [...defaultDocs]
  }
})

const uploadedCount = computed(() => requiredDocuments.value.filter(d => d.uploaded).length)
const requiredCount = computed(() => requiredDocuments.value.filter(d => d.required).length)

function handleFileSelect(idx: number, event: Event) {
  const input = event.target as HTMLInputElement
  const file = input?.files?.[0]
  if (!file) return

  requiredDocuments.value[idx].uploaded = true
  requiredDocuments.value[idx].uploadedName = file.name
  requiredDocuments.value[idx].file = file
  errorMsg.value = ''
}

async function submitDocuments() {
  const requiredMissing = requiredDocuments.value.filter(d => d.required && !d.uploaded)
  if (requiredMissing.length > 0) {
    errorMsg.value = `يجب تحميل: ${requiredMissing.map(d => d.name).join('، ')}`
    return
  }

  submitting.value = true
  uploadProgress.value = 10
  errorMsg.value = ''

  try {
    const filesToUpload = requiredDocuments.value
      .filter(d => d.file !== null)
      .map(d => {
        const ext = d.file!.name.split('.').pop() || ''
        // Rename so backend uses document label as the filename
        return new File([d.file!], `${d.name}.${ext}`, { type: d.file!.type })
      })

    uploadProgress.value = 30
    const result = await analysisApi.uploadDocuments(caseId.value, filesToUpload)
    uploadProgress.value = 100
    aiSummary.value = result.ai_summary || ''
    successMsg.value = result.message
    uploadDone.value = true
  } catch (err: any) {
    errorMsg.value = err?.message || 'حدث خطأ أثناء التحميل'
  } finally {
    submitting.value = false
  }
}

function goToCase() {
  router.push(`/case/${caseId.value}`)
}
</script>
