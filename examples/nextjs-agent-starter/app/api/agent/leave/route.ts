import { leaveMeeting, MeetingBurnerError } from '@/lib/meetingburner'
import { respond } from '@/lib/respond'

/** POST { connectionId } -> take the agent out. Connections are billed by the minute. */
export async function POST(req: Request) {
  return respond(req, async () => {
    const { connectionId } = (await req.json().catch(() => ({}))) as { connectionId?: string }
    if (!connectionId) throw new MeetingBurnerError(400, 'connectionId is required')
    return leaveMeeting(connectionId)
  })
}
