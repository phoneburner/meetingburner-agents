import { joinMeeting, MeetingBurnerError, postArtifact } from '@/lib/meetingburner'
import { respond } from '@/lib/respond'

/**
 * POST { roomId } -> send the agent into the meeting. Answers
 * { status: 'waiting_for_owner' } until the key's owner is in the room; the
 * page asks again after retryAfterSeconds. Once in, the agent posts one note.
 *
 * The connectionId is returned even when the note fails (with `noteError`),
 * so the page can always take the agent out: a connection is billed by the
 * minute until it leaves.
 */
export async function POST(req: Request) {
  return respond(req, async () => {
    const { roomId } = (await req.json().catch(() => ({}))) as { roomId?: string }
    if (!roomId) throw new MeetingBurnerError(400, 'roomId is required')
    const joined = await joinMeeting(roomId)
    if (joined.status !== 'connected') return joined
    try {
      await postArtifact(joined.connectionId, 'Hello from the Next.js starter agent. Replace me with your own agent.')
      return joined
    } catch (err) {
      const noteError = err instanceof MeetingBurnerError ? err.message : 'The note could not be posted.'
      return { ...joined, noteError }
    }
  })
}
