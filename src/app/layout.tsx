import type { Metadata } from 'next'
import { Space_Grotesk } from 'next/font/google'
import './globals.css'

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-sans',
})

export const metadata: Metadata = {
  title: 'Reddit Verification System',
  description: 'Advanced human verification for Reddit communities',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={spaceGrotesk.variable}>
        <div className="min-h-[100dvh] bg-neutral-50">
          {children}
        </div>
      </body>
    </html>
  )
}