'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Check, ArrowRight, BookOpen, MessageCircle, ScrollText } from 'lucide-react'

interface VerificationModalProps {
  isOpen: boolean
  onClose: () => void
  onComplete?: () => void
}

export function VerificationModal({ isOpen, onClose, onComplete }: VerificationModalProps) {
  const [step, setStep] = useState(1)
  const [answers, setAnswers] = useState({ narrative: '', dmReply: false, rulesAgreed: false })
  const [loading, setLoading] = useState(false)

  const steps = [
    {
      id: 1,
      title: 'Comprehension Check',
      description: 'Read and engage thoughtfully with the community.',
      icon: BookOpen
    },
    {
      id: 2, 
      title: 'Interaction Required',
      description: 'Reply to the automated verification DM.',
      icon: MessageCircle
    },
    {
      id: 3,
      title: 'Community Rules',
      description: 'Agree to follow the subreddit guidelines.',
      icon: ScrollText
    }
  ]

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1)
    } else {
      handleComplete()
    }
  }

  const handleComplete = async () => {
    setLoading(true)
    await new Promise(resolve => setTimeout(resolve, 1500))
    setLoading(false)
    onComplete?.()
    onClose()
    setStep(1)
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="w-full max-w-lg bg-white rounded-2xl shadow-xl overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-6 border-b border-neutral-200">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
                  <ShieldCheck size={20} className="text-primary-600" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-neutral-900">Get Verified</h2>
                  <p className="text-sm text-neutral-600">Complete 3 steps to verify you're human</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg text-neutral-500 hover:bg-neutral-100 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-6">
              {/* Progress indicators */}
              <div className="flex items-center justify-between mb-6">
                {steps.map((s, index) => {
                  const Icon = s.icon
                  const isCompleted = step > s.id
                  const isCurrent = step === s.id
                  
                  return (
                    <div key={s.id} className="flex items-center">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                        isCompleted 
                          ? 'bg-success-500 text-white' 
                          : isCurrent 
                            ? 'bg-primary-500 text-white' 
                            : 'bg-neutral-100 text-neutral-400'
                      }`}>
                        {isCompleted ? (
                          <Check size={20} />
                        ) : (
                          <Icon size={20} />
                        )}
                      </div>
                      
                      {index < steps.length - 1 && (
                        <div className={`w-12 h-0.5 mx-2 ${
                          isCompleted ? 'bg-success-500' : 'bg-neutral-200'
                        }`} />
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Step content */}
              <div className="min-h-[200px]">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={step}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="space-y-4"
                  >
                    {step === 1 && (
                      <div>
                        <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                          {steps[0].title}
                        </h3>
                        <p className="text-sm text-neutral-600 mb-4">
                          This subreddit focuses on deep discussion. What makes a good community question?
                        </p>
                        <textarea
                          className="w-full p-3 border border-neutral-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                          rows={3}
                          placeholder="Tell us what makes a good question..."
                          value={answers.narrative}
                          onChange={(e) => setAnswers({ ...answers, narrative: e.target.value })}
                        />
                      </div>
                    )}

                    {step === 2 && (
                      <div>
                        <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                          {steps[1].title}
                        </h3>
                        <p className="text-sm text-neutral-600 mb-4">
                          You'll receive a DM from our verification bot. Reply to it to confirm you're active.
                        </p>
                        <div className="p-4 bg-neutral-50 rounded-lg border">
                          <p className="text-sm text-neutral-700 mb-2">📧 Check your inbox for verification DM</p>
                          <button 
                            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                            onClick={() => setAnswers({ ...answers, dmReply: true })}
                          >
                            ✅ I've replied to the DM
                          </button>
                        </div>
                      </div>
                    )}

                    {step === 3 && (
                      <div>
                        <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                          {steps[2].title}
                        </h3>
                        <p className="text-sm text-neutral-600 mb-4">
                          Once verified, you'll help maintain community quality and follow the rules.
                        </p>
                        <div className="space-y-3">
                          <div className="p-3 bg-neutral-50 rounded-lg text-sm text-neutral-700">
                            • No spam or self-promotion
                            <br />
                            • Engage thoughtfully in discussions
                            <br />
                            • Respect fellow community members
                          </div>
                          <label className="flex items-start gap-3 cursor-pointer">
                            <input
                              type="checkbox"
                              className="mt-0.5 rounded border-neutral-300 text-primary-600 focus:ring-primary-500"
                              checked={answers.rulesAgreed}
                              onChange={(e) => setAnswers({ ...answers, rulesAgreed: e.target.checked })}
                            />
                            <span className="text-sm text-neutral-700">
                              I agree to follow community guidelines
                            </span>
                          </label>
                        </div>
                      </div>
                    )}
                  </motion.div>
                </AnimatePresence>
              </div>

              <div className="flex justify-between items-center pt-6 mt-6 border-t border-neutral-200">
                <button
                  onClick={onClose}
                  className="text-sm text-neutral-600 hover:text-neutral-900 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleNext}
                  disabled={loading}
                  className="btn-primary flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Verifying...
                    </>
                  ) : step < 3 ? (
                    <>
                      Next
                      <ArrowRight size={16} />
                    </>
                  ) : (
                    'Complete Verification'
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}