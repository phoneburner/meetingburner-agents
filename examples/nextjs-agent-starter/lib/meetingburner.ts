/**
 * The MeetingBurner Bot API, server side only: one function per endpoint the
 * starter uses (https://meetingburner.com/api-docs). The API key never leaves
 * the server; the browser talks to this app's own routes.
 */
import 'server-only'

const BASE_URL = (process.env.MEETINGBURNER_API_URL ?? 'https://meetingburner.com/api/v1').replace(/\/$/, '')

export const AGENT_NAME = 'Next.js Starter Agent'
export const AGENT_PURPOSE = 'Says hello and posts a note (nextjs-agent-starter)'

export interface CreatedMeeting {
  roomId: string
  name: string
  joinUrl: string
  hostUrl: string
  expiresAt: string
}

export type JoinResult =
  | { status: 'connected'; connectionId: string }
  | { status: 'waiting_for_owner'; retryAfterSeconds: number }

/** A refusal from MeetingBurner, with its status and the server's own words. */
export class MeetingBurnerError extends Error {
  constructor(readonly status: number, message: string) {
    super(message)
  }
}

export function createMeeting(name: string): Promise<CreatedMeeting> {
  return call('/meetings', { name }, { 'Idempotency-Key': crypto.randomUUID() })
}

/** Join as a disclosed agent. While the key's owner is not in the room, the API answers 202. */
export async function joinMeeting(roomId: string): Promise<JoinResult> {
  const body = await call<{ status: string; connectionId?: string; retryAfterSeconds?: number }>('/bots/join', {
    roomId,
    botName: AGENT_NAME,
    capabilities: ['listen', 'artifact'],
    purpose: AGENT_PURPOSE,
    waitForOwner: true,
  })
  if (body.status === 'connected' && body.connectionId) {
    return { status: 'connected', connectionId: body.connectionId }
  }
  return { status: 'waiting_for_owner', retryAfterSeconds: body.retryAfterSeconds ?? 15 }
}

export function postArtifact(connectionId: string, text: string): Promise<unknown> {
  return call('/bots/post-artifact', { connectionId, artifactType: 'insight', text })
}

export function leaveMeeting(connectionId: string): Promise<{ durationSeconds: number; tokenCost: number }> {
  return call('/bots/leave', { connectionId })
}

async function call<T>(path: string, body: unknown, headers: Record<string, string> = {}): Promise<T> {
  const res = await fetch(BASE_URL + path, {
    method: 'POST',
    headers: { 'X-API-Key': apiKey(), 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
    cache: 'no-store',
  })
  const data = (await res.json().catch(() => ({}))) as { error?: string }
  if (!res.ok) throw new MeetingBurnerError(res.status, data.error ?? res.statusText)
  return data as T
}

function apiKey(): string {
  const key = process.env.MEETINGBURNER_API_KEY?.trim()
  if (!key?.startsWith('mb_')) {
    throw new MeetingBurnerError(500, 'MEETINGBURNER_API_KEY is not set to a MeetingBurner key (it starts with mb_).')
  }
  return key
}
