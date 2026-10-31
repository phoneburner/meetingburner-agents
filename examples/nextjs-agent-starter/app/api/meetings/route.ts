import { createMeeting } from '@/lib/meetingburner'
import { respond } from '@/lib/respond'

/** POST { name } -> a new meeting hosted by the API key's owner. */
export async function POST(req: Request) {
  return respond(req, async () => {
    const { name } = (await req.json().catch(() => ({}))) as { name?: string }
    return createMeeting(name?.trim() || 'Meeting with my agent')
  })
}
