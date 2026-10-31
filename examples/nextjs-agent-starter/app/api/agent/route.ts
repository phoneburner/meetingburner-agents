import { joinMeeting, MeetingBurnerError, postArtifact } from '@/lib/meetingburner'
import { respond } from '@/lib/respond'

/**
 * POST { roomId } -> send the agent into the meeting. Answers
 * { status: 'waiting_for_owner' } until the key's owner is in the room; the
 * page asks again after retryAfterSeconds. Once in, the agent posts one note.
 */
export async function POST(req: Request) {
  const { roomId } = (await req.json().catch(() => ({}))) as { roomId?: string }
  return respond(async () => {
    if (!roomId) throw new MeetingBurnerError(400, 'roomId is required')
    const joined = await joinMeeting(roomId)
    if (joined.status === 'connected') {
      await postArtifact(joined.connectionId, 'Hello from the Next.js starter agent. Replace me with your own agent.')
    }
    return joined
  })
}
