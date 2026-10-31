/**
 * Who may call this app's routes. Every route acts with the owner's
 * MeetingBurner key, so a deployed copy must not be open to anyone who finds
 * its URL.
 *
 * - With STARTER_ACCESS_TOKEN set, a request must carry the same value in the
 *   `x-starter-token` header (compared in constant time).
 * - Without it, the routes answer only under `next dev` on your own machine.
 *   A deployed copy with no token refuses everything: fail closed.
 */
import 'server-only'
import { createHash, timingSafeEqual } from 'node:crypto'

export const ACCESS_HEADER = 'x-starter-token'

export type AccessDecision = { allowed: true } | { allowed: false; status: number; message: string }

export function checkAccess(req: Request): AccessDecision {
  const expected = process.env.STARTER_ACCESS_TOKEN?.trim()
  if (!expected) {
    if (process.env.NODE_ENV === 'development') return { allowed: true }
    return {
      allowed: false,
      status: 503,
      message: 'STARTER_ACCESS_TOKEN is not set, so this deployed app refuses every request. Set it and redeploy.',
    }
  }
  const given = req.headers.get(ACCESS_HEADER) ?? ''
  if (sameSecret(given, expected)) return { allowed: true }
  return { allowed: false, status: 401, message: 'Wrong or missing access token.' }
}

/** Hash both sides first so the comparison takes the same time whatever the lengths. */
function sameSecret(given: string, expected: string): boolean {
  const digest = (value: string) => createHash('sha256').update(value).digest()
  return timingSafeEqual(digest(given), digest(expected))
}
