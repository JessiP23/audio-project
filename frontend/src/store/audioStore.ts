import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

interface AudioData {
  filename: string
  duration: number
  sampleRate: number
  channels: number
}

interface BufferStatus {
  size: number
  available: number
  read_ptr: number
  write_ptr: number
  utilization: number
}

interface ProcessingHistory {
  id: string
  effect: string
  parameters: Record<string, any>
  processed_at: string
  samples_processed: number
  processing_time_ms: number
}

interface AudioStore {
  // Session state
  sessionId: string | null
  isConnected: boolean
  
  // Audio data
  audioData: AudioData | null
  bufferStatus: BufferStatus | null
  
  // Processing state
  isProcessing: boolean
  processingHistory: ProcessingHistory[]
  activeEffects: string[]
  
  // UI state
  selectedEffect: string | null
  effectParameters: Record<string, any>
  
  // Actions
  setSessionId: (sessionId: string) => void
  setConnected: (connected: boolean) => void
  setAudioData: (data: AudioData) => void
  setBufferStatus: (status: BufferStatus) => void
  setProcessing: (processing: boolean) => void
  addProcessingHistory: (history: ProcessingHistory) => void
  setActiveEffects: (effects: string[]) => void
  setSelectedEffect: (effect: string | null) => void
  setEffectParameters: (parameters: Record<string, any>) => void
  updateEffectParameter: (key: string, value: any) => void
  clearSession: () => void
}

export const useAudioStore = create<AudioStore>()(
  devtools(
    (set, get) => ({
      // Initial state
      sessionId: null,
      isConnected: false,
      audioData: null,
      bufferStatus: null,
      isProcessing: false,
      processingHistory: [],
      activeEffects: [],
      selectedEffect: null,
      effectParameters: {},
      
      // Actions
      setSessionId: (sessionId) => set({ sessionId }),
      
      setConnected: (connected) => set({ isConnected: connected }),
      
      setAudioData: (data) => set({ audioData: data }),
      
      setBufferStatus: (status) => set({ bufferStatus: status }),
      
      setProcessing: (processing) => set({ isProcessing: processing }),
      
      addProcessingHistory: (history) => 
        set((state) => ({
          processingHistory: [history, ...state.processingHistory].slice(0, 50) // Keep last 50
        })),
      
      setActiveEffects: (effects) => set({ activeEffects: effects }),
      
      setSelectedEffect: (effect) => set({ selectedEffect: effect }),
      
      setEffectParameters: (parameters) => set({ effectParameters: parameters }),
      
      updateEffectParameter: (key, value) =>
        set((state) => ({
          effectParameters: {
            ...state.effectParameters,
            [key]: value,
          },
        })),
      
      clearSession: () => set({
        sessionId: null,
        isConnected: false,
        audioData: null,
        bufferStatus: null,
        isProcessing: false,
        processingHistory: [],
        activeEffects: [],
        selectedEffect: null,
        effectParameters: {},
      }),
    }),
    {
      name: 'audio-store',
    }
  )
) 