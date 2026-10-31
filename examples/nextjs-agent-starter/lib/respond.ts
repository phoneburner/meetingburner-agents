import { NextResponse } from 'next/server'
import { checkAccess } from './access'
import { MeetingBurnerError } from './meetingburner'

/**
 * Refuse a caller without the access token, then run a route body and turn a
 * MeetingBurner refusal into a JSON error the page can show.
 */
export async function respond(req: Request, work: () => Promise<unknown>): Promise<NextResponse> {
  const access = checkAccess(req)
  if (!access.allowed) return NextResponse.json({ error: access.message }, { status: access.status })
  try {
    return NextResponse.json(await work())
  } catch (err) {
    if (err instanceof MeetingBurnerError) {
      return NextResponse.json({ error: err.message }, { status: err.status })
    }
    console.error(err)
    return NextResponse.json({ error: 'Something went wrong. Check the server log.' }, { status: 500 })
  }
}
