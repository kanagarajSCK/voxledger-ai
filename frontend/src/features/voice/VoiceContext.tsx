import React, { createContext, useContext, useState, useCallback } from 'react'
import { VoiceAssistantModal } from './VoiceAssistantModal'

interface VoiceContextValue {
  isVoiceModalOpen: boolean
  openVoiceModal: () => void
  closeVoiceModal: () => void
  toggleVoiceModal: () => void
}

const VoiceContext = createContext<VoiceContextValue | undefined>(undefined)

export const VoiceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isOpen, setIsOpen] = useState(false)

  const openVoiceModal = useCallback(() => setIsOpen(true), [])
  const closeVoiceModal = useCallback(() => setIsOpen(false), [])
  const toggleVoiceModal = useCallback(() => setIsOpen((prev) => !prev), [])

  return (
    <VoiceContext.Provider value={{ isVoiceModalOpen: isOpen, openVoiceModal, closeVoiceModal, toggleVoiceModal }}>
      {children}
      <VoiceAssistantModal isOpen={isOpen} onClose={closeVoiceModal} />
    </VoiceContext.Provider>
  )
}

export const useVoiceAssistant = (): VoiceContextValue => {
  const context = useContext(VoiceContext)
  if (!context) {
    throw new Error('useVoiceAssistant must be used within a VoiceProvider')
  }
  return context
}
