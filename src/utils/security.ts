/**
 * Security utilities for Jenan BIZ
 * - Password hashing (SHA-256 via Web Crypto API)
 * - Rate limiting for login attempts
 * - Input sanitization
 */

// ============================================
// Password Hashing (client-side pre-hash)
// In production, always hash again on the server with bcrypt/argon2
// ============================================

/**
 * Hash a password using SHA-256 via Web Crypto API.
 * This is a client-side pre-hash — server should re-hash with bcrypt/argon2.
 */
export async function hashPassword(password: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(password)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('')
}

// ============================================
// Rate Limiter (client-side)
// Prevents brute-force by tracking attempts in memory + localStorage
// ============================================

interface RateLimitEntry {
  attempts: number
  firstAttempt: number
  lockedUntil: number
}

interface RateLimitResult {
  allowed: boolean
  retryAfter: number // seconds
  remainingAttempts: number
}

const MAX_ATTEMPTS = 5
const WINDOW_MS = 5 * 60 * 1000      // 5 minutes window
const LOCKOUT_MS = 60 * 1000          // 60 seconds lockout

class RateLimiter {
  private store: Map<string, RateLimitEntry> = new Map()

  constructor() {
    // Restore from localStorage
    try {
      const saved = localStorage.getItem('__rl_store')
      if (saved) {
        const parsed = JSON.parse(saved) as Record<string, RateLimitEntry>
        for (const [k, v] of Object.entries(parsed)) {
          this.store.set(k, v)
        }
      }
    } catch {
      // Ignore corrupt data
    }
  }

  private save() {
    try {
      const obj: Record<string, RateLimitEntry> = {}
      this.store.forEach((v, k) => { obj[k] = v })
      localStorage.setItem('__rl_store', JSON.stringify(obj))
    } catch {
      // Ignore
    }
  }

  /**
   * Check if an action is allowed (without recording).
   */
  check(key: string): RateLimitResult {
    const now = Date.now()
    const entry = this.store.get(key)

    if (!entry) {
      return { allowed: true, retryAfter: 0, remainingAttempts: MAX_ATTEMPTS }
    }

    // Check if currently locked
    if (entry.lockedUntil > now) {
      return {
        allowed: false,
        retryAfter: Math.ceil((entry.lockedUntil - now) / 1000),
        remainingAttempts: 0,
      }
    }

    // Reset if window expired
    if (now - entry.firstAttempt > WINDOW_MS) {
      this.store.delete(key)
      this.save()
      return { allowed: true, retryAfter: 0, remainingAttempts: MAX_ATTEMPTS }
    }

    const remaining = MAX_ATTEMPTS - entry.attempts
    return {
      allowed: remaining > 0,
      retryAfter: remaining <= 0 ? Math.ceil(LOCKOUT_MS / 1000) : 0,
      remainingAttempts: Math.max(0, remaining),
    }
  }

  /**
   * Record a failed attempt.
   */
  record(key: string) {
    const now = Date.now()
    let entry = this.store.get(key)

    if (!entry || now - entry.firstAttempt > WINDOW_MS) {
      entry = { attempts: 0, firstAttempt: now, lockedUntil: 0 }
    }

    entry.attempts++

    if (entry.attempts >= MAX_ATTEMPTS) {
      entry.lockedUntil = now + LOCKOUT_MS
    }

    this.store.set(key, entry)
    this.save()
  }

  /**
   * Reset attempts for a key (e.g., after successful login).
   */
  reset(key: string) {
    this.store.delete(key)
    this.save()
  }
}

export const rateLimiter = new RateLimiter()

// ============================================
// Input Sanitization
// ============================================

/**
 * Basic XSS sanitization — strip HTML tags.
 */
export function sanitize(input: string): string {
  return input.replace(/<[^>]*>/g, '').trim()
}

/**
 * Validate Saudi phone number format.
 */
export function isValidSaudiPhone(phone: string): boolean {
  return /^05\d{8}$/.test(phone.replace(/\s/g, ''))
}
