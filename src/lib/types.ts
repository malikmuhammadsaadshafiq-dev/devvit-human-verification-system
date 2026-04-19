export interface UserVerification {
  id: string
  username: string
  email?: string
  verified: boolean
  createdAt: string
  submittedAt?: string
  narrativeResponse?: string
  dmVerified?: boolean
  rulesAgreed?: boolean
  rejectReason?: string
  avatar?: string
}

export interface VerificationStats {
  pending: number
  verified: number
  rejected: number
}