'use client'

import { useState } from 'react'

interface Meeting {
  roomId: string
  name: string
  joinUrl: string
  hostUrl: string
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, { method: 'POST', body: JSON.stringify(body) })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error ?? `Request failed (${res.status})`)
  return data as T
}

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

export default function Home() {
  const [meeting, setMeeting] = useState<Meeting | null>(null)
  const [connectionId, setConnectionId] = useState<string | null>(null)
  const [status, setStatus] = useState('')

  async function run(work: () => Promise<void>) {
    try {
      await work()
    } catch (err) {
      setStatus(err instanceof Error ? err.message : String(err))
    }
  }

  const create = () =>
    run(async () => {
      setStatus('Creating a meeting...')
      setMeeting(await post<Meeting>('/api/meetings', { name: 'Meeting with my agent' }))
      setStatus('Open the host link (signed in), then send the agent in.')
    })

  // The agent is admitted only while you are in the room, so keep asking until you are.
  const sendAgent = () =>
    run(async () => {
      if (!meeting) return
      for (let attempt = 0; attempt < 20; attempt++) {
        const joined = await post<{ status: string; connectionId?: string; retryAfterSeconds?: number }>(
          '/api/agent',
          { roomId: meeting.roomId },
        )
        if (joined.status === 'connected' && joined.connectionId) {
          setConnectionId(joined.connectionId)
          setStatus('The agent is in the meeting and posted a note. Look at the Intel panel.')
          return
        }
        setStatus('Waiting for you to join the meeting...')
        await sleep((joined.retryAfterSeconds ?? 15) * 1000)
      }
      setStatus('You did not join in time. Open the host link, then try again.')
    })

  const removeAgent = () =>
    run(async () => {
      if (!connectionId) return
      const left = await post<{ durationSeconds: number; tokenCost: number }>('/api/agent/leave', { connectionId })
      setConnectionId(null)
      setStatus(`The agent left after ${left.durationSeconds}s. Billed: ${left.tokenCost} token(s).`)
    })

  return (
    <main>
      <h1>MeetingBurner agent starter</h1>
      <p>Create a meeting, join it yourself, then send an agent in. Everyone in the meeting sees the agent and who added it.</p>

      <button onClick={create}>1. Create a meeting</button>

      {meeting && (
        <section>
          <p>
            <a href={meeting.hostUrl} target="_blank" rel="noreferrer">2. Open it as the host</a> (signed in to
            MeetingBurner). Share this link with guests: <code>{meeting.joinUrl}</code>
          </p>
          {connectionId ? (
            <button onClick={removeAgent}>Remove the agent</button>
          ) : (
            <button onClick={sendAgent}>3. Send the agent in</button>
          )}
        </section>
      )}

      {status && <p role="status">{status}</p>}
    </main>
  )
}
