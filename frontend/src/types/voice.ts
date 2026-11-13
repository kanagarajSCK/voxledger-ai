export type VoiceLanguage = 'en-IN' | 'hi-IN' | 'ta-IN' | 'kn-IN'

export type VoiceState =
  | 'idle'
  | 'requesting_permission'
  | 'listening'
  | 'transcribing'
  | 'confirming'
  | 'speaking'
  | 'error'

export interface PendingVoiceAction {
  action_id: string
  customer_id: number
  customer_public_id: string
  customer_name: string
  type: 'CREDIT' | 'PAYMENT'
  amount: string
  current_balance: string
  projected_balance: string
  description?: string
  raw_text?: string
}

export interface VoiceCandidate {
  id: string
  name: string
  phone?: string
}

export interface VoiceAssistantMessage {
  id: string
  sender: 'user' | 'assistant'
  text: string
  timestamp: string
  action?: PendingVoiceAction
  candidates?: VoiceCandidate[]
  audioBase64?: string
  isFinal?: boolean
}
