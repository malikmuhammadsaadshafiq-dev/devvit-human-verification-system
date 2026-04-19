import type { UserVerification, VerificationStats } from './types'

// Mock API - replace with real endpoints
const MOCK_USERS: UserVerification[] = [
  {
    id: '1',
    username: 'alex_schneider',
    verified: true,
    createdAt: '2024-01-15T10:30:00Z',
    submittedAt: '2024-01-15T15:45:00Z',
    narrativeResponse: 'Good questions encourage deeper thinking and provide value to the community. They should be specific enough to generate meaningful discussion.',
    dmVerified: true,
    rulesAgreed: true,
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop&crop=face'
  },
  {
    id: '2',
    username: 'sarah_chen',
    verified: false,
    createdAt: '2024-01-20T14:20:00Z',
    submittedAt: '2024-01-20T16:30:00Z',
    narrativeResponse: 'Questions are the foundation of knowledge sharing. The best ones invite diverse perspectives.',
    dmVerified: true,
    rulesAgreed: true
  },
  {
    id: '3',
    username: 'mike_rodriguez',
    verified: false,
    createdAt: '2024-01-18T09:15:00Z',
    narrativeResponse: '',
    dmVerified: false,
    rulesAgreed: false
  },
  {
    id: '4',
    username: 'emma_watson',
    verified: false,
    createdAt: '2024-01-22T11:00:00Z',
    submittedAt: '2024-01-22T11:30:00Z',
    rejectReason: 'Bot-like behavior detected'
  }
]

export async function getUsers(): Promise<UserVerification[]> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 500))
  return MOCK_USERS
}

export async function updateUserStatus(
  userId: string, 
  action: 'verify' | 'reject', 
  reason?: string
): Promise<UserVerification> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 800))
  
  const user = MOCK_USERS.find(u => u.id === userId)
  if (!user) throw new Error('User not found')
  
  if (action === 'verify') {
    user.verified = true
  } else if (action === 'reject') {
    user.rejectReason = reason || 'Verification rejected'
  }
  
  return user
}

export async function getVerificationStats(): Promise<VerificationStats> {
  const users = await getUsers()
  return {
    pending: users.filter(u => !u.verified && !u.rejectReason).length,
    verified: users.filter(u => u.verified).length,
    rejected: users.filter(u => !!u.rejectReason).length
  }
}