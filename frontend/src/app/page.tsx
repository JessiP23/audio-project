'use client'

import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { 
  PlayIcon, 
  PauseIcon, 
  StopIcon, 
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  MusicalNoteIcon,
  Cog6ToothIcon,
  ChartBarIcon
} from '@heroicons/react/24/solid'

export default function Home() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(0.7)
  const [sessionId, setSessionId] = useState<string | null>(null)
  
  const audioContextRef = useRef<AudioContext | null>(null)
  const audioBufferRef = useRef<AudioBuffer | null>(null)
  const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null)
  const gainNodeRef = useRef<GainNode | null>(null)

  useEffect(() => {
    // Initialize audio context
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
    gainNodeRef.current = audioContextRef.current.createGain()
    gainNodeRef.current.connect(audioContextRef.current.destination)
    
    // Create new session
    createNewSession()
    
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  const createNewSession = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/audio/session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_name: 'Studio Session' }),
      })
      
      if (response.ok) {
        const data = await response.json()
        setSessionId(data.session_id)
      }
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  const handlePlay = () => {
    if (!audioContextRef.current || !audioBufferRef.current) return
    
    if (audioContextRef.current.state === 'suspended') {
      audioContextRef.current.resume()
    }
    
    if (sourceNodeRef.current) {
      sourceNodeRef.current.stop()
    }
    
    sourceNodeRef.current = audioContextRef.current.createBufferSource()
    sourceNodeRef.current.buffer = audioBufferRef.current
    sourceNodeRef.current.connect(gainNodeRef.current!)
    
    sourceNodeRef.current.onended = () => {
      setIsPlaying(false)
      setCurrentTime(0)
    }
    
    sourceNodeRef.current.start(0, currentTime)
    setIsPlaying(true)
  }

  const handlePause = () => {
    if (sourceNodeRef.current) {
      sourceNodeRef.current.stop()
      setIsPlaying(false)
    }
  }

  const handleStop = () => {
    if (sourceNodeRef.current) {
      sourceNodeRef.current.stop()
      setIsPlaying(false)
      setCurrentTime(0)
    }
  }

  const handleVolumeChange = (newVolume: number) => {
    setVolume(newVolume)
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.value = newVolume
    }
  }

  const handleMute = () => {
    setIsMuted(!isMuted)
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.value = isMuted ? volume : 0
    }
  }

  const handleFileUpload = async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await fetch('http://localhost:8000/api/audio/upload', {
        method: 'POST',
        body: formData,
      })
      
      if (response.ok) {
        const data = await response.json()
        setSessionId(data.session_id)
        
        // Load audio file into buffer
        const arrayBuffer = await file.arrayBuffer()
        const audioBuffer = await audioContextRef.current!.decodeAudioData(arrayBuffer)
        audioBufferRef.current = audioBuffer
        setDuration(audioBuffer.duration)
      }
    } catch (error) {
      console.error('Failed to upload file:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <MusicalNoteIcon className="h-8 w-8 text-blue-500" />
              <h1 className="text-xl font-bold text-gradient">Audio Processing Studio</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button className="btn-secondary flex items-center space-x-2">
                <Cog6ToothIcon className="h-5 w-5" />
                <span>Settings</span>
              </button>
              <button className="btn-secondary flex items-center space-x-2">
                <ChartBarIcon className="h-5 w-5" />
                <span>Analytics</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Audio Interface */}
          <div className="lg:col-span-2 space-y-6">
            {/* File Upload */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="card"
            >
              <div className="text-center">
                <h2 className="text-xl font-semibold mb-4">Upload Audio File</h2>
                
                <div className="border-2 border-dashed border-gray-600 rounded-lg p-8 cursor-pointer hover:border-gray-500 transition-colors">
                  <input 
                    type="file" 
                    accept="audio/*"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) handleFileUpload(file)
                    }}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <div className="flex flex-col items-center space-y-4">
                      <MusicalNoteIcon className="h-8 w-8 text-gray-400" />
                      <div className="text-center">
                        <p className="text-lg font-medium mb-2">Click to upload audio file</p>
                        <p className="text-sm text-gray-400">
                          Supports WAV, MP3, FLAC, OGG, AAC, M4A (max 50MB)
                        </p>
                      </div>
                    </div>
                  </label>
                </div>
              </div>
            </motion.div>

            {/* Audio Controls */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="card"
            >
              <div className="flex items-center justify-between">
                {/* Playback Controls */}
                <div className="flex items-center space-x-4">
                  <button
                    onClick={isPlaying ? handlePause : handlePlay}
                    className="w-12 h-12 bg-blue-600 hover:bg-blue-700 rounded-full flex items-center justify-center transition-colors duration-200"
                  >
                    {isPlaying ? (
                      <PauseIcon className="h-6 w-6 text-white" />
                    ) : (
                      <PlayIcon className="h-6 w-6 text-white ml-1" />
                    )}
                  </button>
                  
                  <button
                    onClick={handleStop}
                    className="w-10 h-10 bg-gray-600 hover:bg-gray-700 rounded-full flex items-center justify-center transition-colors duration-200"
                  >
                    <StopIcon className="h-5 w-5 text-white" />
                  </button>
                </div>

                {/* Volume Controls */}
                <div className="flex items-center space-x-3">
                  <button
                    onClick={handleMute}
                    className="w-8 h-8 bg-gray-600 hover:bg-gray-700 rounded-full flex items-center justify-center transition-colors duration-200"
                  >
                    {isMuted || volume === 0 ? (
                      <SpeakerXMarkIcon className="h-5 w-5" />
                    ) : (
                      <SpeakerWaveIcon className="h-5 w-5" />
                    )}
                  </button>
                  
                  <div className="flex items-center space-x-2">
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={isMuted ? 0 : volume}
                      onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                      className="w-20 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <span className="text-sm text-gray-400 w-12">
                      {Math.round((isMuted ? 0 : volume) * 100)}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Status */}
              <div className="mt-4 flex items-center justify-between text-sm">
                <div className="flex items-center space-x-4">
                  <span className="text-gray-400">
                    Status: {isPlaying ? 'Playing' : 'Stopped'}
                  </span>
                  {isMuted && (
                    <span className="text-red-400 font-medium">Muted</span>
                  )}
                </div>
                
                <div className="text-gray-400">
                  Volume: {Math.round((isMuted ? 0 : volume) * 100)}%
                </div>
              </div>
            </motion.div>

            {/* Audio Visualizer Placeholder */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="card"
            >
              <div className="mb-4">
                <h3 className="text-lg font-semibold mb-2">Audio Visualizer</h3>
                <div className="flex items-center justify-between text-sm">
                  <span>Real-time frequency spectrum</span>
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <span className="text-gray-400">Level:</span>
                      <span className="text-green-500">0.0%</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-gray-400">Peak:</span>
                      <span className="text-green-500">0.0%</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="relative">
                <div className="w-full h-32 bg-gray-800 rounded-lg border border-gray-700 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-gray-400 text-sm mb-2">No audio playing</div>
                    <div className="flex items-center justify-center space-x-1">
                      {[...Array(8)].map((_, i) => (
                        <div
                          key={i}
                          className="w-1 h-8 bg-gray-600 rounded-full animate-pulse"
                          style={{
                            animationDelay: `${i * 0.1}s`,
                            animationDuration: '1s',
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Effects Panel */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="lg:col-span-1"
          >
            <div className="card">
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-2">Audio Effects</h3>
                <p className="text-sm text-gray-400">Apply real-time audio processing effects</p>
              </div>

              {/* Effects Grid */}
              <div className="grid grid-cols-2 gap-3 mb-6">
                {['Reverb', 'Delay', 'Distortion', 'Filter', 'Compression', 'Normalize'].map((effect) => (
                  <button
                    key={effect}
                    className="p-3 rounded-lg border border-gray-600 hover:border-gray-500 transition-all duration-200 text-left"
                  >
                    <div className="flex items-center space-x-2">
                      <MusicalNoteIcon className="h-5 w-5 text-blue-500" />
                      <span className="font-medium">{effect}</span>
                    </div>
                  </button>
                ))}
              </div>

              {/* Connection Status */}
              {!sessionId && (
                <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                  <p className="text-sm text-yellow-400">
                    Not connected to audio session
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        </div>

        {/* Session Info */}
        {sessionId && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="mt-8 p-4 bg-gray-800 rounded-lg border border-gray-700"
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Session Info</h3>
                <p className="text-gray-400">Session ID: {sessionId}</p>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-400">Connected</span>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}
