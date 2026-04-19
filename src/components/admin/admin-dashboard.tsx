'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Shield, ShieldCheck, ShieldX, User, Clock, Check, X, AlertCircle } from '@phosphor-icons/react'
import type { UserVerification } from '@/lib/types'

interface AdminDashboardProps {
  users: UserVerification[]
  onUserAction: (userId: string, action: 'verify' | 'reject') => void
}

export function AdminDashboard({ users, onUserAction }: AdminDashboardProps) {
  const [selectedTab, setSelectedTab] = useState<'pending' | 'verified' | 'rejected'>('pending')
  const [selectedUser, setSelectedUser] = useState<string | null>(null)

  const filteredUsers = users.filter(user => {
    switch (selectedTab) {
      case 'pending': return !user.verified && !user.rejectReason
      case 'verified': return user.verified
      case 'rejected': return !!user.rejectReason
      default: return true
    }
  })

  const stats = {
    pending: users.filter(u => !u.verified && !u.rejectReason).length,
    verified: users.filter(u => u.verified).length,
    rejected: users.filter(u => !!u.rejectReason).length,
  }

  return (
    <div className="min-h-[100dvh] bg-neutral-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-neutral-900 mb-2">Verification Dashboard</h1>
          <p className="text-neutral-600">Manage user verification requests</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card p-6"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-warning-50 rounded-full flex items-center justify-center">
                <Clock size={24} className="text-warning-600" />
              </div>
              <div>
                <p className="text-sm text-neutral-600">Pending</p>
                <p className="text-2xl font-bold text-neutral-900">{stats.pending}</p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="card p-6"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-success-50 rounded-full flex items-center justify-center">
                <Check size={24} className="text-success-600" />
              </div>
              <div>
                <p className="text-sm text-neutral-600">Verified</p>
                <p className="text-2xl font-bold text-neutral-900">{stats.verified}</p>
              </div>
            </div>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="card p-6"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-error-50 rounded-full flex items-center justify-center">
                <AlertCircle size={24} className="text-error-600" />
              </div>
              <div>
                <p className="text-sm text-neutral-600">Rejected</p>
                <p className="text-2xl font-bold text-neutral-900">{stats.rejected}</p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-neutral-200 mb-6">
          <nav className="flex space-x-8">
            {[
              { id: 'pending', label: 'Pending', icon: Clock },
              { id: 'verified', label: 'Verified', icon: Check },
              { id: 'rejected', label: 'Rejected', icon: ShieldX },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setSelectedTab(id as any)}
                className={`flex items-center gap-2 py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                  selectedTab === id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-neutral-500 hover:text-neutral-700'
                }`}
              >
                <Icon size={16} />
                {label}
              </button>
            ))}
          </nav>
        </div>

        {/* User List */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          {filteredUsers.map((user, index) => (
            <motion.div
              key={user.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => setSelectedUser(selectedUser === user.id ? null : user.id)}
              className="card p-4 hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-neutral-100 rounded-full flex items-center justify-center">
                    <User size={20} className="text-neutral-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-neutral-900">{user.username}</h3>
                    <p className="text-sm text-neutral-600">Joined {new Date(user.createdAt).toLocaleDateString()}</p>
                  </div>
                </div>

                {selectedTab === 'pending' && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        onUserAction(user.id, 'verify')
                      }}
                      className="p-2 rounded-lg text-success-600 hover:bg-success-50 transition-colors"
                    >
                      <Check size={20} />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        onUserAction(user.id, 'reject')
                      }}
                      className="p-2 rounded-lg text-error-600 hover:bg-error-50 transition-colors"
                    >
                      <X size={20} />
                    </button>
                  </div>
                )}

                {user.verified && (
                  <div className="flex items-center gap-1 text-sm text-success-600">
                    <ShieldCheck size={16} />
                    Verified
                  </div>
                )}

                {user.rejectReason && (
                  <div className="text-sm text-error-600">
                    Rejected: {user.rejectReason}
                  </div>
                )}
              </div>

              {/* Expanded content */}
              <AnimatePresence>
                {selectedUser === user.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="mt-4 pt-4 border-t border-neutral-100"
                  >
                    <div className="space-y-3">
                      <div>
                        <h4 className="font-medium text-neutral-900 mb-1">Comprehension Response</h4>
                        <p className="text-sm text-neutral-600 bg-neutral-50 p-3 rounded-lg">
                          {user.narrativeResponse || 'No response provided'}
                        </p>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-neutral-600">Status:</span>
                          <span className={`ml-2 font-medium ${
                            user.verified ? 'text-success-600' : user.rejectReason ? 'text-error-600' : 'text-warning-600'
                          }`}>
                            {user.verified ? 'Verified' : user.rejectReason ? 'Rejected' : 'Pending'}
                          </span>
                        </div>
                        <div>
                          <span className="text-neutral-600">DM Replied:</span>
                          <span className={`ml-2 font-medium ${user.dmVerified ? 'text-success-600' : 'text-neutral-400'}`}>
                            {user.dmVerified ? 'Yes' : 'No'}
                          </span>
                        </div>
                        <div>
                          <span className="text-neutral-600">Rules Agreed:</span>
                          <span className={`ml-2 font-medium ${user.rulesAgreed ? 'text-success-600' : 'text-neutral-400'}`}>
                            {user.rulesAgreed ? 'Yes' : 'No'}
                          </span>
                        </div>
                        <div>
                          <span className="text-neutral-600">Submitted:</span>
                          <span className="ml-2 font-medium">
                            {new Date(user.submittedAt || user.createdAt).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </motion.div>

        {filteredUsers.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-neutral-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <User size={24} className="text-neutral-400" />
            </div>
            <h3 className="text-lg font-medium text-neutral-900 mb-1">
              No {selectedTab} users found
            </h3>
            <p className="text-neutral-600">
              {selectedTab === 'pending' && 'Check back for new verification requests'}
              {selectedTab === 'verified' && 'No users have been verified yet'}
              {selectedTab === 'rejected' && 'No rejections at this time'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}