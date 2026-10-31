import { createMeeting } from '@/lib/meetingburner'
import { respond } from '@/lib/respond'

/** POST { name } -> a new meeting hosted by the API key's owner. */
export async function POST(req: Request) {
  const { name } = (await req.json().catch(() => ({}))) as { name?: string }
  return respond(() => createMeeting(name?.trim() || 'Meeting with my agent'))
}
