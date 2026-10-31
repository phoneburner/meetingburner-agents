import { NextResponse } from 'next/server'
import { MeetingBurnerError } from './meetingburner'

/** Run a route body and turn a MeetingBurner refusal into a JSON error the page can show. */
export async function respond(work: () => Promise<unknown>): Promise<NextResponse> {
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
