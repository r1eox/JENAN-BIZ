<template>
  <Teleport to="body">
    <div v-if="modelValue" class="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center" @click.self="$emit('update:modelValue', false)">
      <div class="bg-white w-full sm:max-w-md rounded-t-2xl sm:rounded-2xl p-5">
        <h3 class="text-base font-bold text-brand mb-4">تغيير كلمة المرور</h3>

        <div class="space-y-3">
          <!-- Current password -->
          <div>
            <label class="block text-xs font-medium text-text-light mb-1">كلمة المرور الحالية</label>
            <div class="relative">
              <input
                v-model="currentPass"
                :type="showCurrent ? 'text' : 'password'"
                class="w-full pr-3 pl-10 py-2.5 border-2 rounded-xl text-sm focus:outline-none transition-colors"
                :class="errors.current ? 'border-danger' : 'border-border focus:border-blue'"
                placeholder="كلمة المرور الحالية"
              />
              <button type="button" @click="showCurrent = !showCurrent" class="absolute inset-y-0 left-0 pl-3 flex items-center cursor-pointer" tabindex="-1">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path v-if="!showCurrent" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                  <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7 1.274-4.057 5.064-7 9.543-7 4.477 0 8.268 2.943 9.542 7M15 12a3 3 0 11-6 0"/>
                </svg>
              </button>
            </div>
            <p v-if="errors.current" class="mt-1 text-xs text-danger">{{ errors.current }}</p>
          </div>

          <!-- New password -->
          <div>
            <label class="block text-xs font-medium text-text-light mb-1">كلمة المرور الجديدة</label>
            <div class="relative">
              <input
                v-model="newPass"
                :type="showNew ? 'text' : 'password'"
                class="w-full pr-3 pl-10 py-2.5 border-2 rounded-xl text-sm focus:outline-none transition-colors"
                :class="errors.new ? 'border-danger' : 'border-border focus:border-blue'"
                placeholder="6 أحرف على الأقل"
              />
              <button type="button" @click="showNew = !showNew" class="absolute inset-y-0 left-0 pl-3 flex items-center cursor-pointer" tabindex="-1">
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path v-if="!showNew" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                  <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7 1.274-4.057 5.064-7 9.543-7 4.477 0 8.268 2.943 9.542 7M15 12a3 3 0 11-6 0"/>
                </svg>
              </button>
            </div>
            <p v-if="errors.new" class="mt-1 text-xs text-danger">{{ errors.new }}</p>
          </div>

          <!-- Confirm -->
          <div>
            <label class="block text-xs font-medium text-text-light mb-1">تأكيد كلمة المرور</label>
            <input
              v-model="confirmPass"
              type="password"
              class="w-full px-3 py-2.5 border-2 rounded-xl text-sm focus:outline-none transition-colors"
              :class="errors.confirm ? 'border-danger' : 'border-border focus:border-blue'"
              placeholder="أعد كتابة كلمة المرور الجديدة"
            />
            <p v-if="errors.confirm" class="mt-1 text-xs text-danger">{{ errors.confirm }}</p>
          </div>
        </div>

        <!-- Success -->
        <div v-if="successMsg" class="mt-3 p-3 rounded-xl bg-success/10 text-success text-xs font-medium text-center">
          {{ successMsg }}
        </div>

        <div class="flex gap-2 mt-4">
          <button
            @click="$emit('update:modelValue', false)"
            class="flex-1 py-2.5 rounded-xl border-2 border-border text-sm font-bold text-text-light cursor-pointer hover:border-brand/30 transition-colors"
          >إلغاء</button>
          <button
            @click="submit"
            :disabled="loading"
            class="flex-1 py-2.5 rounded-xl bg-blue text-white text-sm font-bold cursor-pointer disabled:opacity-50 hover:bg-blue/90 transition-colors"
          >
            <span v-if="!loading">حفظ</span>
            <span v-else class="flex items-center justify-center gap-1.5">
              <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              جاري الحفظ...
            </span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { authApi, ApiException } from '../api/client'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ (e: 'update:modelValue', val: boolean): void }>()

const currentPass = ref('')
const newPass = ref('')
const confirmPass = ref('')
const showCurrent = ref(false)
const showNew = ref(false)
const loading = ref(false)
const successMsg = ref('')
const errors = reactive({ current: '', new: '', confirm: '' })

// Reset when modal opens
watch(() => props.modelValue, (val) => {
  if (val) {
    currentPass.value = ''
    newPass.value = ''
    confirmPass.value = ''
    errors.current = ''
    errors.new = ''
    errors.confirm = ''
    successMsg.value = ''
  }
})

async function submit() {
  errors.current = ''
  errors.new = ''
  errors.confirm = ''
  successMsg.value = ''

  if (!currentPass.value) { errors.current = 'أدخل كلمة المرور الحالية'; return }
  if (newPass.value.length < 6) { errors.new = 'يجب أن تكون 6 أحرف على الأقل'; return }
  if (newPass.value !== confirmPass.value) { errors.confirm = 'كلمتا المرور غير متطابقتين'; return }

  loading.value = true
  try {
    await authApi.changePassword(currentPass.value, newPass.value)
    successMsg.value = 'تم تغيير كلمة المرور بنجاح ✓'
    setTimeout(() => emit('update:modelValue', false), 1500)
  } catch (e) {
    if (e instanceof ApiException) {
      errors.current = e.message
    } else {
      errors.current = 'حدث خطأ. حاول مرة أخرى.'
    }
  }
  loading.value = false
}
</script>
