/**
 * Bank Statement Analyzer — Jenan BIZ
 *
 * Validates and analyzes uploaded bank statements (Excel/CSV).
 * Checks:  file type → basic structure → date coverage → column presence
 *
 * In production, the heavy analysis would run server-side via a job queue.
 */

import type { BankStatement } from '../types/request'

export interface BSValidationResult {
  success: boolean
  error?: string
  data?: BankStatement
}

export interface BSAnalysisResult {
  success: boolean
  error?: string
  progress: number
  resultSummary?: string
}

/** Required column names (Arabic + English variants) */
const REQUIRED_COLUMN_PATTERNS = [
  /تاريخ|date/i,
  /مبلغ|قيمة|amount|value/i,
  /رصيد|balance/i,
]

/**
 * Validate a bank statement file before analysis.
 *
 * @param file               The uploaded file
 * @param requiredMonths     Required coverage in months
 * @param onProgress         Progress callback
 */
export async function validateBankStatement(
  file: File,
  requiredMonths: number,
  onProgress?: (pct: number) => void
): Promise<BSValidationResult> {
  // 1. Check file type
  const validExtensions = /\.(xlsx|xls|csv)$/i
  const validMimeTypes = [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // xlsx
    'application/vnd.ms-excel', // xls
    'text/csv',
    'application/csv',
  ]

  if (!validMimeTypes.includes(file.type) && !file.name.match(validExtensions)) {
    return {
      success: false,
      error: 'صيغة الملف غير مدعومة. يرجى رفع ملف Excel (.xlsx, .xls) أو CSV.',
    }
  }

  onProgress?.(10)

  // 2. Check file size (max 20 MB)
  if (file.size > 20 * 1024 * 1024) {
    return {
      success: false,
      error: 'حجم الملف كبير جداً. الحد الأقصى 20 ميجابايت.',
    }
  }

  onProgress?.(20)

  // 3. Simulate reading file content
  await new Promise(r => setTimeout(r, 800))
  onProgress?.(40)

  // 4. Simulate column check
  // In production, parse CSV/Excel headers and validate
  const hasRequiredColumns = true // simulated pass
  if (!hasRequiredColumns) {
    return {
      success: false,
      error: 'الملف لا يحتوي على الأعمدة المطلوبة (التاريخ، المبلغ، الرصيد). يرجى التأكد من صحة الملف.',
    }
  }

  onProgress?.(60)
  await new Promise(r => setTimeout(r, 500))

  // 5. Simulate date coverage check
  const today = new Date()
  const periodEnd = today.toISOString().split('T')[0]
  const periodStart = new Date(today)
  periodStart.setMonth(periodStart.getMonth() - requiredMonths)
  const periodStartStr = periodStart.toISOString().split('T')[0]

  // Simulate coverage validation
  // Random chance of insufficient coverage for demo realism
  const coverageRatio = 0.7 + Math.random() * 0.35 // 70%–105%
  const actualCoverageMonths = Math.round(requiredMonths * coverageRatio)

  onProgress?.(80)
  await new Promise(r => setTimeout(r, 400))

  if (actualCoverageMonths < requiredMonths) {
    return {
      success: false,
      error: `كشف الحساب يغطي ${actualCoverageMonths} أشهر فقط من أصل ${requiredMonths} المطلوبة. يرجى رفع كشف حساب مكتمل يغطي الفترة المطلوبة.`,
    }
  }

  onProgress?.(100)

  return {
    success: true,
    data: {
      file,
      fileName: file.name,
      periodStart: periodStartStr,
      periodEnd: periodEnd,
      coverageMonths: actualCoverageMonths,
      hasRequiredColumns: true,
      isValid: true,
      parsed: true,
    },
  }
}

/**
 * Simulate the backend analysis queue.
 * In production this would be a server-side job.
 *
 * @param onProgress  Progress callback (0–100)
 */
export async function runAnalysis(
  onProgress?: (pct: number) => void
): Promise<BSAnalysisResult> {
  // Simulate analysis in steps
  const steps = [
    { pct: 10, delay: 500, label: 'قراءة البيانات...' },
    { pct: 25, delay: 700, label: 'التحقق من الأعمدة...' },
    { pct: 40, delay: 600, label: 'تحليل التدفقات المالية...' },
    { pct: 55, delay: 800, label: 'حساب المتوسطات...' },
    { pct: 70, delay: 600, label: 'تطبيق قواعد الجهات...' },
    { pct: 85, delay: 500, label: 'إعداد التقرير...' },
    { pct: 100, delay: 300, label: 'اكتمل التحليل' },
  ]

  for (const step of steps) {
    await new Promise(r => setTimeout(r, step.delay))
    onProgress?.(step.pct)
  }

  // Random outcome for demo
  const outcomes = [
    {
      summary: 'المنشأة مؤهلة مبدئياً. يرجى استكمال المستندات المطلوبة.',
      status: 'eligible_need_docs' as const,
    },
    {
      summary: 'المنشأة غير مؤهلة حالياً بناءً على تحليل التدفقات المالية.',
      status: 'not_eligible_currently' as const,
    },
    {
      summary: 'المنشأة مؤهلة مبدئياً. يرجى استكمال المستندات المطلوبة.',
      status: 'eligible_need_docs' as const,
    },
  ]

  const outcome = outcomes[Math.floor(Math.random() * outcomes.length)]

  return {
    success: true,
    progress: 100,
    resultSummary: outcome.summary,
  }
}
