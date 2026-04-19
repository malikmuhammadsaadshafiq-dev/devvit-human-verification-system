'use client'

import { ShieldStar, User } from '@phosphor-icons/react'
import { motion, AnimatePresence } from 'framer-motion'

interface VerificationTriggerProps {
  verified?: boolean
  onClick: () => void
  className?: string
}

export function VerificationTrigger({ 
  verified = false, 
  onClick, 
  className = '' 
}: VerificationTriggerProps) {
  return (
    <motion.button
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all ${
        verified 
          ? 'bg-success-50 text-success-700 hover:bg-success-100' 
          : 'bg-primary-50 text-primary-700 hover:bg-primary-100 border border-primary-200'
      } ${className}`}
    >
      {verified ? (
        <ShieldStar size={16} weight="fill" />
      ) : (
        <User size={16} />
      )}
      <span className="text-sm font-medium">
        {verified ? 'Verified' : 'Get Verified'}
      </span>
    </motion.button>
  )
}