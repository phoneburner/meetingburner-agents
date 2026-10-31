/**
 * Who may call this app's routes. Every route acts with the owner's
 * MeetingBurner key, so neither a stranger who finds a deployed copy nor a
 * web page you happen to visit may call them.
 *
 * Every request, in dev too, must:
 * - be same-origin: a browser's `Sec-Fetch-Site` must say `same-origin`, and
 *   an `Origin` header must name this app's own host (stops CSRF from other
 *   pages);
 * - send `Content-Type: application/json`, which no cross-site "simple"
 *   request can do without a CORS preflight this app never grants.
 * Then:
 * - with STARTER_ACCESS_TOKEN set, it must carry the same value in the
 *   `x-starter-token` header (compared in constant time);
 * - without it, the routes answer only under `next dev`, addressed as
 *   localhost (stops DNS rebinding). A deployed copy with no token refuses
 *   everything: fail closed.
 */
import 'server-only'
import { createHash, timingSafeEqual } from 'node:crypto'

export const ACCESS_HEADER = 'x-starter-token'

const LOOPBACK_HOSTS = new Set(['localhost', '127.0.0.1', '[::1]'])

export type AccessDecision = { allowed: true } | { allowed: false; status: number; message: string }

const refuse = (status: number, message: string): AccessDecision => ({ allowed: false, status, message })

export function checkAccess(req: Request): AccessDecision {
  const host = req.headers.get('host') ?? ''
  if (!isSameOrigin(req, host)) return refuse(403, 'Cross-site requests are refused.')
  if (!(req.headers.get('content-type') ?? '').toLowerCase().startsWith('application/json')) {
    return refuse(415, 'Send Content-Type: application/json.')
  }
  const expected = process.env.STARTER_ACCESS_TOKEN?.trim()
  if (!expected) {
    if (process.env.NODE_ENV === 'development' && LOOPBACK_HOSTS.has(hostname(host))) return { allowed: true }
    return refuse(503, 'STARTER_ACCESS_TOKEN is not set, so this app refuses every request except under `npm run dev` on localhost. Set it and redeploy.')
  }
  const given = req.headers.get(ACCESS_HEADER) ?? ''
  if (sameSecret(given, expected)) return { allowed: true }
  return refuse(401, 'Wrong or missing access token.')
}

/** A browser marks every request with where it came from; refuse any that is not this app. */
function isSameOrigin(req: Request, host: string): boolean {
  const site = req.headers.get('sec-fetch-site')
  if (site !== null && site !== 'same-origin') return false
  const origin = req.headers.get('origin')
  if (origin === null) return true // not a browser fetch (curl, a server); the token still applies
  try {
    return new URL(origin).host === host
  } catch {
    return false
  }
}

/** `localhost:3000` -> `localhost`, `[::1]:3000` -> `[::1]`. */
function hostname(host: string): string {
  return host.startsWith('[') ? host.slice(0, host.indexOf(']') + 1) : host.split(':')[0]
}

/** Hash both sides first so the comparison takes the same time whatever the lengths. */
function sameSecret(given: string, expected: string): boolean {
  const digest = (value: string) => createHash('sha256').update(value).digest()
  return timingSafeEqual(digest(given), digest(expected))
}
