'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Shield, Users, BarChart3, Settings } from '@phosphor-icons/react'
import { AdminDashboard } from '@/components/admin/admin-dashboard'
import { getUsers, updateUserStatus } from '@/lib/api'
import type { UserVerification } from '@/lib/types'

export default function AdminPage() {
  const [users, setUsers] = useState<UserVerification[]>([])
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // In real app, check auth here
    fetchUsers()
  }, [])

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const users = await getUsers()
      setUsers(users)
    } catch (error) {
      console.error('Failed to fetch users:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleUserAction = async (userId: string, action: 'verify' | 'reject') => {
    try {
      await updateUserStatus(userId, action)
      await fetchUsers() // Refresh the list
    } catch (error) {
      console.error('Failed to update user:', error)
    }
  }

  return (
    <main className="min-h-[100dvh] bg-neutral-50">
      {/* Admin Header */}
      <div className="border-b border-neutral-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
                <Settings size={20} className="text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-neutral-900">Admin Dashboard</h1>
                <p className="text-sm text-neutral-600">Reddit Verification Management</p>
              </div>
            </div>
            
            <button
              onClick={() => router.push('/')}
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              View Community →
            </button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading ? (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-neutral-600">Loading verification data...</p>
          </div>
        </div>
      ) : (
        <AdminDashboard users={users} onUserAction={handleUserAction} />
      )}
    </main>
  )
}