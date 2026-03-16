/**
 * Commercial Registration Analyzer — Jenan BIZ
 *
 * Simulates OCR / parsing of commercial registration documents.
 * In production, this would call a backend API with actual OCR (e.g., Google Vision, AWS Textract).
 *
 * Extracts:  issue date → age in months → entity type → eligibility + required statement period
 */

import type { EntityType, CommercialRegistration } from '../types/request'

export interface CRAnalysisResult {
  success: boolean
  error?: string
  data?: {
    issueDate: string
    companyName: string
    registrationNumber: string
    entityType: EntityType
    ageInMonths: number
    isEligible: boolean
    requiredStatementMonths: number
    eligibilityMessage: string
  }
}

/**
 * Calculate age in months from issue date to today.
 */
export function calculateAgeInMonths(issueDateStr: string): number {
  const issueDate = new Date(issueDateStr)
  const today = new Date()

  let months = (today.getFullYear() - issueDate.getFullYear()) * 12
  months += today.getMonth() - issueDate.getMonth()

  // Adjust if today's day is before issue day
  if (today.getDate() < issueDate.getDate()) {
    months--
  }

  return Math.max(0, months)
}

/**
 * Determine required bank statement period based on establishment age.
 *
 * Rules:
 * - < 6 months → not eligible (0)
 * - = 6 months → 6 months
 * - 7–11 months → full age
 * - ≥ 12 months → 12 months
 */
export function getRequiredStatementMonths(ageInMonths: number): {
  isEligible: boolean
  requiredMonths: number
  message: string
} {
  if (ageInMonths < 6) {
    return {
      isEligible: false,
      requiredMonths: 0,
      message: `عمر المنشأة (${ageInMonths} ${ageInMonths <= 2 ? 'شهر' : 'أشهر'}) أقل من 6 أشهر. المنشأة غير مؤهلة حالياً.`,
    }
  }

  if (ageInMonths === 6) {
    return {
      isEligible: true,
      requiredMonths: 6,
      message: `حسب عمر منشأتك (6 أشهر)، يرجى رفع كشف حساب يغطي آخر 6 أشهر.`,
    }
  }

  if (ageInMonths >= 7 && ageInMonths <= 11) {
    return {
      isEligible: true,
      requiredMonths: ageInMonths,
      message: `حسب عمر منشأتك (${ageInMonths} أشهر)، يرجى رفع كشف حساب يغطي آخر ${ageInMonths} أشهر.`,
    }
  }

  // 12+
  return {
    isEligible: true,
    requiredMonths: 12,
    message: `حسب عمر منشأتك (${ageInMonths} شهر)، يرجى رفع كشف حساب يغطي آخر 12 شهر.`,
  }
}

/**
 * Detect entity type from text (simulated).
 */
function detectEntityType(text: string): EntityType {
  const lower = text.toLowerCase()
  if (lower.includes('مؤسسة') || lower.includes('فردية')) return 'مؤسسة فردية'
  if (lower.includes('محدودة') || lower.includes('ذ.م.م')) return 'شركة ذات مسؤولية محدودة'
  if (lower.includes('مساهمة')) return 'شركة مساهمة'
  if (lower.includes('تضامن')) return 'شركة تضامنية'
  if (lower.includes('أجنبية') || lower.includes('فرع')) return 'فرع شركة أجنبية'
  return 'مؤسسة فردية' // default for demo
}

/**
 * Generate a simulated registration number.
 */
function generateRegNumber(): string {
  return (
    Math.floor(1000000000 + Math.random() * 9000000000).toString()
  )
}

/**
 * Simulate analysis of a commercial registration file.
 * In a real app, this would send the file to a backend OCR service.
 *
 * @param file    Uploaded file (PDF or image)
 * @param onProgress  Progress callback (0–100)
 */
export async function analyzeCR(
  file: File,
  onProgress?: (pct: number) => void
): Promise<CRAnalysisResult> {
  // Validate file type
  const validTypes = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/heic',
  ]

  if (!validTypes.includes(file.type) && !file.name.match(/\.(pdf|jpe?g|png|webp|heic)$/i)) {
    return {
      success: false,
      error: 'صيغة الملف غير مدعومة. يرجى رفع PDF أو صورة (JPG, PNG).',
    }
  }

  // Max 10 MB
  if (file.size > 10 * 1024 * 1024) {
    return {
      success: false,
      error: 'حجم الملف كبير جداً. الحد الأقصى 10 ميجابايت.',
    }
  }

  // Simulate OCR processing with progress
  for (let i = 0; i <= 100; i += 10) {
    await new Promise(r => setTimeout(r, 200))
    onProgress?.(i)
  }

  // ---- Simulated extraction ----
  // In production, the backend would parse the actual document.
  // For demo, we generate plausible data.

  // Generate a random issue date between 1 and 36 months ago for demo variety
  const monthsAgo = Math.floor(Math.random() * 36) + 1
  const issueDate = new Date()
  issueDate.setMonth(issueDate.getMonth() - monthsAgo)
  const issueDateStr = issueDate.toISOString().split('T')[0]

  const ageInMonths = calculateAgeInMonths(issueDateStr)
  const statementReq = getRequiredStatementMonths(ageInMonths)
  const entityType = detectEntityType(file.name)

  // Simulated Arabic company names
  const companyNames = [
    'مؤسسة النور للتجارة',
    'شركة الخليج للمقاولات',
    'مجموعة الريادة للتقنية',
    'مؤسسة البناء الحديث',
    'شركة الأمان للاستثمار',
  ]

  return {
    success: true,
    data: {
      issueDate: issueDateStr,
      companyName: companyNames[Math.floor(Math.random() * companyNames.length)],
      registrationNumber: generateRegNumber(),
      entityType,
      ageInMonths,
      isEligible: statementReq.isEligible,
      requiredStatementMonths: statementReq.requiredMonths,
      eligibilityMessage: statementReq.message,
    },
  }
}

/**
 * Analyze CR with a manually entered issue date (for manual override / testing).
 */
export function analyzeFromDate(issueDateStr: string): CRAnalysisResult {
  const ageInMonths = calculateAgeInMonths(issueDateStr)
  const statementReq = getRequiredStatementMonths(ageInMonths)

  return {
    success: true,
    data: {
      issueDate: issueDateStr,
      companyName: '',
      registrationNumber: '',
      entityType: 'أخرى',
      ageInMonths,
      isEligible: statementReq.isEligible,
      requiredStatementMonths: statementReq.requiredMonths,
      eligibilityMessage: statementReq.message,
    },
  }
}
