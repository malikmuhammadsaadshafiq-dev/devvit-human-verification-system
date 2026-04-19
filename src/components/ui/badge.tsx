import { Check, Shield } from 'lucide-react'

interface VerificationBadgeProps {
  size?: 'sm' | 'md'
  verified?: boolean
  className?: string
}

export function VerificationBadge({ 
  size = 'sm', 
  verified = true, 
  className = '' 
}: VerificationBadgeProps) {
  if (!verified) return null

  return (
    <div className={`verified-badge ${size === 'md' ? 'px-3 py-1.5 text-sm' : ''} ${className}`}>
      <Shield size={size === 'sm' ? 14 : 16} />
      <span>Verified</span>
    </div>
  )
}