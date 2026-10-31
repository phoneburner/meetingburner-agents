import type { ReactNode } from 'react'

export const metadata = {
  title: 'MeetingBurner agent starter',
  description: 'Create a MeetingBurner meeting and send an agent into it.',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: 'system-ui, sans-serif', maxWidth: 640, margin: '48px auto', padding: '0 16px', lineHeight: 1.5 }}>
        {children}
      </body>
    </html>
  )
}
