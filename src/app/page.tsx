'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Shield, Users, BarChart3, Check } from '@phosphor-icons/react'
import { VerificationTrigger } from '@/components/verification/verification-trigger'
import { VerificationModal } from '@/components/verification/verification-modal'
import { VerificationBadge } from '@/components/ui/badge'

interface RedditUser {
  id: string
  username: string
  verified: boolean
  karma: number
  joined: string
}

export default function HomePage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<string | null>(null)
  
  // Mock Reddit-style posts
  const posts = [
    {
      id: 1,
      title: 'What makes a discussion truly valuable in online communities?',
      author: {
        username: 'alex_schneider',
        verified: true,
        karma: 2847
      },
      content: 'I\'ve been thinking about what separates meaningful engagement from simple interaction. In my experience, the most valuable discussions share three key characteristics...',
      upvotes: 342,
      comments: 45
    },
    {
      id: 2,
      title: 'The hidden complexity of human verification systems',
      author: {
        username: 'sarah_chen',
        verified: false,
        karma: 1823
      },
      content: 'We're implementing a new verification system, and I\'m researching effective methods beyond traditional CAPTCHAs. The challenge is balancing friction with accessibility...',
      upvotes: 127,
      comments: 23
    }
  ]

  const handleVerificationComplete = () => {
    console.log('Verification completed!')
  }

  return (
    <main className="min-h-[100dvh] bg-neutral-50">
      {/* Header */}
      <div className="border-b border-neutral-200 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
                <Shield size={20} className="text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-neutral-900">r/CommunityQuality</h1>
                <p className="text-sm text-neutral-600">Human-verified discussion</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-sm text-neutral-600">
                2.4k members
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 pt-8">
        {/* Verification Overview */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-6 mb-8"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-neutral-900 mb-1">Community Verification</h2>
              <p className="text-sm text-neutral-600">Get verified to contribute to high-quality discussions</p>
            </div>
            <div className="w-16 h-16 bg-primary-50 rounded-full flex items-center justify-center">
              <Users size={32} className="text-primary-600" />
            </div>
          </div>
        </motion.div>

        {/* Posts */}
        <div className="space-y-4">
          {posts.map((post, index) => (
            <motion.div
              key={post.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="card p-4 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-neutral-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-bold text-neutral-600">
                    {post.author.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-neutral-900">{post.author.username}</span>
                    <span className="text-xs text-neutral-500">• {post.author.karma} karma</span>
                    <VerificationBadge verified={post.author.verified} />
                    {!post.author.verified && post.author.username === selectedUser && (
                      <VerificationTrigger 
                        verified={false} 
                        onClick={() => setSelectedUser(post.author.username)}
                        className="text-xs"
                      />
                    )}
                  </div>
                  
                  <h3 className="text-lg font-semibold text-neutral-900 mb-2">{post.title}</h3>
                  <p className="text-neutral-700 text-sm leading-relaxed">{post.content}</p>
                  
                  <div className="flex items-center gap-4 mt-3 text-sm text-neutral-500">
                    <span>↑ {post.upvotes} points</span>
                    <span>💬 {post.comments} comments</span>
                    <span>award</span>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Verification Modal */}
        <VerificationModal 
          isOpen={isModalOpen} 
          onClose={() => setIsModalOpen(false)}
          onComplete={handleVerificationComplete}
        />
      </div>
    </main>
  )
}