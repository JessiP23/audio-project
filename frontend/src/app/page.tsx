'use client'

import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  PlayIcon, PauseIcon, StopIcon, SpeakerWaveIcon,
  SpeakerXMarkIcon, MusicalNoteIcon, Cog6ToothIcon, ChartBarIcon
} from '@heroicons/react/24/solid'
import toast from 'react-hot-toast'

export default function Home() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(0.7)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [uploadedFiles, setUploadedFiles] = useState<Array<{name: string, size: number, duration: number}>>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [activeEffects, setActiveEffects] = useState<string[]>([])
  const [audioAnalysis, setAudioAnalysis] = useState<any>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [audioLevels, setAudioLevels] = useState({ level: 0, peak: 0 })
  const [frequencyData, setFrequencyData] = useState<number[]>([])

  const audioContextRef = useRef<AudioContext | null>(null)
  const audioBufferRef = useRef<AudioBuffer | null>(null)
  const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null)
  const gainNodeRef = useRef<GainNode | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)

  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)()
    gainNodeRef.current = audioContextRef.current.createGain()
    analyserRef.current = audioContextRef.current.createAnalyser()
    
    // Configure analyser for visualization
    analyserRef.current.fftSize = 256
    analyserRef.current.smoothingTimeConstant = 0.8
    
    // Connect the audio chain
    gainNodeRef.current.connect(analyserRef.current)
    analyserRef.current.connect(audioContextRef.current.destination)
    
    createNewSession()
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  const createNewSession = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/audio/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_name: 'Studio Session' }),
      })
      if (response.ok) {
        const data = await response.json()
        setSessionId(data.session_id)
        toast.success('Audio session created successfully!')
      }
    } catch (error) {
      console.error('Failed to create session:', error)
      toast.error('Failed to create audio session')
    }
  }

  const handlePlay = () => {
    if (audioContextRef.current && audioBufferRef.current) {
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
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current)
        }
      }
      
      sourceNodeRef.current.start(0, currentTime)
      setIsPlaying(true)
      
      // Start visualization
      startVisualization()
    }
  }

  const startVisualization = () => {
    if (!analyserRef.current) return
    
    const updateVisualization = () => {
      if (!analyserRef.current || !isPlaying) return
      
      // Get frequency data
      const frequencyArray = new Uint8Array(analyserRef.current.frequencyBinCount)
      analyserRef.current.getByteFrequencyData(frequencyArray)
      
      // Get time domain data for level calculation
      const timeArray = new Uint8Array(analyserRef.current.frequencyBinCount)
      analyserRef.current.getByteTimeDomainData(timeArray)
      
      // Calculate RMS level
      let sum = 0
      for (let i = 0; i < timeArray.length; i++) {
        const value = (timeArray[i] - 128) / 128
        sum += value * value
      }
      const rms = Math.sqrt(sum / timeArray.length)
      const level = Math.min(100, rms * 100)
      
      // Calculate peak
      const peak = Math.max(...Array.from(frequencyArray).map(val => val / 255 * 100))
      
      setAudioLevels({ level, peak })
      setFrequencyData(Array.from(frequencyArray).slice(0, 64)) // Use first 64 bins
      
      animationFrameRef.current = requestAnimationFrame(updateVisualization)
    }
    
    updateVisualization()
  }

  const handlePause = () => {
    if (sourceNodeRef.current) {
      sourceNodeRef.current.stop()
      setIsPlaying(false)
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }

  const handleStop = () => {
    if (sourceNodeRef.current) {
      sourceNodeRef.current.stop()
      setIsPlaying(false)
      setCurrentTime(0)
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      setAudioLevels({ level: 0, peak: 0 })
      setFrequencyData([])
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
    console.log(`📁 Uploading file: ${file.name} (${file.size} bytes)`)
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      console.log('📤 Sending file upload request to backend')
      const response = await fetch('http://localhost:8000/api/audio/upload', {
        method: 'POST',
        body: formData,
      })
      
      console.log(`📥 Upload response status: ${response.status} ${response.statusText}`)
      
      if (response.ok) {
        const data = await response.json()
        console.log('✅ File upload successful:', data)
        console.log('📋 Session ID set to:', data.file_id)
        
        setSessionId(data.file_id)
        
        // Add file to uploaded files list
        setUploadedFiles(prev => [...prev, {
          name: file.name,
          size: file.size,
          duration: data.duration
        }])
        
        console.log('🎵 Loading audio into Web Audio API')
        const arrayBuffer = await file.arrayBuffer()
        const audioBuffer = await audioContextRef.current!.decodeAudioData(arrayBuffer)
        audioBufferRef.current = audioBuffer
        setDuration(audioBuffer.duration)
        
        toast.success(`File "${file.name}" uploaded successfully!`)
        console.log(`✅ Audio file loaded: ${audioBuffer.duration}s duration`)
      } else {
        const errorText = await response.text()
        console.error(`❌ Upload failed: ${response.status} - ${errorText}`)
        throw new Error(`Upload failed: ${response.status} - ${errorText}`)
      }
    } catch (error) {
      console.error('❌ Failed to upload file:', error)
      toast.error('Failed to upload file')
    }
  }

  const applyAudioEffect = async (effect: string) => {
    console.log(`🎵 Applying ${effect} effect to session: ${sessionId}`)
    console.log(`🔍 Session ID type: ${typeof sessionId}, value: "${sessionId}"`)
    
    if (!sessionId) {
      console.error('❌ No active session found')
      toast.error('No active session. Please upload a file first.')
      return
    }

    setIsProcessing(true)
    setActiveEffects(prev => [...prev, effect])
    
    const requestBody = {
      effect: effect.toLowerCase(),
      parameters: getDefaultParameters(effect)
    }
    
    console.log(`📤 Sending request to backend:`, {
      url: `http://localhost:8000/api/audio/${sessionId}/process`,
      method: 'POST',
      body: requestBody
    })
    
    try {
      const response = await fetch(`http://localhost:8000/api/audio/${sessionId}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      })
      
      console.log(`📥 Response status: ${response.status} ${response.statusText}`)
      
      if (response.ok) {
        const data = await response.json()
        console.log(`✅ Successfully applied ${effect}:`, data)
        console.log(`📊 Response data structure:`, {
          samples_processed: data.samples_processed,
          processed_file_path: data.processed_file_path,
          session_id: data.session_id
        })
        toast.success(`${effect} effect applied successfully!`)
        
        // Update the audio analysis with new processing results
        setAudioAnalysis((prev: any) => ({
          ...prev,
          lastProcessedEffect: effect,
          processedSamples: data.samples_processed,
          processedFile: data.processed_file_path,
          sessionId: data.session_id,
          processingHistory: [...(prev?.processingHistory || []), {
            effect,
            timestamp: new Date().toISOString(),
            samplesProcessed: data.samples_processed
          }]
        }))
        
        toast.success(`${effect} effect applied successfully! Listen to the result below.`)
      } else {
        const errorText = await response.text()
        console.error(`❌ Server error: ${response.status} - ${errorText}`)
        throw new Error(`Server error: ${response.status} - ${errorText}`)
      }
    } catch (error) {
      console.error(`❌ Failed to apply ${effect}:`, error)
      toast.error(`Failed to apply ${effect} effect`)
      setActiveEffects(prev => prev.filter(e => e !== effect))
    } finally {
      setIsProcessing(false)
    }
  }

  const getDefaultParameters = (effect: string) => {
    const params: { [key: string]: any } = {}
    
    switch (effect.toLowerCase()) {
      case 'reverb':
        params.room_size = 0.8  // Increased from 0.5
        params.damping = 0.2    // Decreased from 0.5 for more echo
        params.wet_level = 0.7  // Added wet/dry mix
        break
      case 'delay':
        params.delay_time = 0.5  // Increased from 0.3
        params.feedback = 0.6    // Increased from 0.3
        params.wet_level = 0.8   // Added wet/dry mix
        break
      case 'distortion':
        params.drive = 0.8       // Increased from 0.5
        params.tone = 0.6        // Added tone control
        break
      case 'filter':
        params.cutoff = 2000     // Increased from 1000
        params.resonance = 0.8   // Increased from 0.5
        params.filter_type = 'lowpass' // Added filter type
        break
      case 'compression':
        params.threshold = -15   // Increased from -20
        params.ratio = 8         // Increased from 4
        params.attack = 0.01     // Added attack time
        params.release = 0.1     // Added release time
        break
      case 'normalize':
        params.target_level = -3.0  // Increased from -1.0
        break
      case 'chorus':
        params.rate = 1.5        // Chorus rate
        params.depth = 0.7       // Chorus depth
        params.mix = 0.6         // Chorus mix
        break
      case 'flanger':
        params.rate = 0.5        // Flanger rate
        params.depth = 0.8       // Flanger depth
        params.feedback = 0.3    // Flanger feedback
        break
      case 'phaser':
        params.rate = 0.8        // Phaser rate
        params.depth = 0.9       // Phaser depth
        params.feedback = 0.4    // Phaser feedback
        break
    }
    
    return params
  }

  const removeEffect = (effect: string) => {
    setActiveEffects(prev => prev.filter(e => e !== effect))
    toast.success(`${effect} effect removed`)
  }

  const playProcessedAudio = async (sessionId: string, effect: string) => {
    try {
      const audioUrl = `http://localhost:8000/api/audio/processed/${sessionId}/${effect.toLowerCase()}`
      console.log(`🎵 Playing processed audio: ${audioUrl}`)
      
      // Create a new audio element for the processed audio
      const audio = new Audio(audioUrl)
      audio.volume = volume
      
      audio.onloadeddata = () => {
        console.log(`✅ Processed audio loaded: ${effect}`)
        toast.success(`Playing ${effect} processed audio`)
      }
      
      audio.onerror = (error) => {
        console.error(`❌ Error playing processed audio:`, error)
        toast.error(`Error playing ${effect} audio`)
      }
      
      await audio.play()
    } catch (error) {
      console.error(`❌ Error playing processed audio:`, error)
      toast.error(`Error playing ${effect} audio`)
    }
  }

  const analyzeAudio = async () => {
    if (!sessionId) {
      toast.error('No active session. Please upload a file first.')
      return
    }

    setIsAnalyzing(true)
    
    try {
      const response = await fetch(`http://localhost:8000/api/audio/${sessionId}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      
      if (response.ok) {
        const data = await response.json()
        setAudioAnalysis(data)
        toast.success('Audio analysis completed!')
        console.log('Audio analysis:', data)
      } else {
        throw new Error('Failed to analyze audio')
      }
    } catch (error) {
      console.error('Failed to analyze audio:', error)
      toast.error('Failed to analyze audio')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const extractFeatures = async (featureType: string = 'all') => {
    if (!sessionId) {
      toast.error('No active session. Please upload a file first.')
      return
    }

    setIsAnalyzing(true)
    
    try {
      const response = await fetch(`http://localhost:8000/api/audio/${sessionId}/extract-features?feature_type=${featureType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      
      if (response.ok) {
        const data = await response.json()
        toast.success(`${featureType} features extracted successfully!`)
        console.log('Extracted features:', data)
      } else {
        throw new Error('Failed to extract features')
      }
    } catch (error) {
      console.error('Failed to extract features:', error)
      toast.error('Failed to extract features')
    } finally {
      setIsAnalyzing(false)
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
                          <h1 className="text-xl font-bold text-gradient">David AI Audio Research Studio</h1>
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

            {/* Uploaded Files Display */}
            {uploadedFiles.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="card"
              >
                <h3 className="text-lg font-semibold mb-4">Uploaded Files</h3>
                <div className="space-y-3">
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <MusicalNoteIcon className="h-5 w-5 text-blue-500" />
                        <div>
                          <p className="font-medium text-white">{file.name}</p>
                          <p className="text-sm text-gray-400">
                            {(file.size / 1024 / 1024).toFixed(2)} MB • {file.duration.toFixed(2)}s
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handlePlay()}
                          className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                        >
                          <PlayIcon className="h-4 w-4 text-white" />
                        </button>
                        <button
                          onClick={() => handleStop()}
                          className="p-2 bg-gray-600 hover:bg-gray-700 rounded-lg transition-colors"
                        >
                          <StopIcon className="h-4 w-4 text-white" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

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
                {['Reverb'].map((effect) => (
                  <button
                    key={effect}
                    onClick={() => applyAudioEffect(effect)}
                    className={`p-3 rounded-lg border border-gray-600 hover:border-gray-500 transition-all duration-200 text-left ${
                      activeEffects.includes(effect) ? 'border-blue-500 bg-blue-500/10' : ''
                    } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
                    disabled={isProcessing}
                  >
                    <div className="flex items-center space-x-2">
                      <MusicalNoteIcon className="h-5 w-5 text-blue-500" />
                      <span className="font-medium">{effect}</span>
                      {isProcessing && activeEffects.includes(effect) && (
                        <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                      )}
                    </div>
                  </button>
                ))}
              </div>

              {/* Active Effects */}
              {activeEffects.length > 0 && (
                <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                  <p className="text-sm text-blue-400 mb-2">
                    Active Effects: {activeEffects.join(', ')}
                  </p>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => activeEffects.forEach(removeEffect)}
                      className="text-sm text-blue-400 hover:underline"
                    >
                      Remove All
                    </button>
                    <span className="text-gray-500">|</span>
                    <button
                      onClick={() => setActiveEffects([])}
                      className="text-sm text-gray-400 hover:text-white"
                    >
                      Clear List
                    </button>
                  </div>
                </div>
              )}

              {/* Analysis Controls */}
              <div className="mt-4 space-y-3">
                <button
                  onClick={analyzeAudio}
                  disabled={isAnalyzing || !sessionId}
                  className={`w-full p-3 rounded-lg border border-gray-600 hover:border-gray-500 transition-all duration-200 text-left ${
                    isAnalyzing ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <ChartBarIcon className="h-5 w-5 text-green-500" />
                      <span className="font-medium">Analyze Audio</span>
                    </div>
                    {isAnalyzing && (
                      <div className="w-4 h-4 border-2 border-green-500 border-t-transparent rounded-full animate-spin"></div>
                    )}
                  </div>
                </button>

                <div className="grid grid-cols-2 gap-2">
                  {['mfcc', 'spectral', 'rhythm', 'chroma'].map((featureType) => (
                    <button
                      key={featureType}
                      onClick={() => extractFeatures(featureType)}
                      disabled={isAnalyzing || !sessionId}
                      className={`p-2 rounded-lg border border-gray-600 hover:border-gray-500 transition-all duration-200 text-xs ${
                        isAnalyzing ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                    >
                      {featureType.charAt(0).toUpperCase() + featureType.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Analysis Results */}
              {audioAnalysis && (
                <div className="mt-4 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                  <h4 className="text-sm font-medium text-green-400 mb-2">Analysis Results</h4>
                  <div className="text-xs text-gray-400 space-y-1">
                    <div>RMS: {audioAnalysis.analysis?.rms?.toFixed(4)}</div>
                    <div>Peak: {audioAnalysis.analysis?.peak?.toFixed(4)}</div>
                    <div>Duration: {audioAnalysis.analysis?.duration?.toFixed(2)}s</div>
                    <div>Tempo: {audioAnalysis.features?.tempo?.toFixed(1)} BPM</div>
                    <div>Spectral Centroid: {audioAnalysis.analysis?.spectral_centroid?.toFixed(1)} Hz</div>
                    <div>Zero Crossing Rate: {audioAnalysis.analysis?.zero_crossing_rate?.toFixed(4)}</div>
                  </div>
                </div>
              )}

              {/* Processing Results */}
              {activeEffects.length > 0 && (
                <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                  <h4 className="text-sm font-medium text-blue-400 mb-2">Processing Results</h4>
                  <div className="text-xs text-gray-400 space-y-1">
                    <div>Applied Effects: {activeEffects.join(', ')}</div>
                    <div>Session ID: {sessionId}</div>
                    <div>Status: {isProcessing ? 'Processing...' : 'Ready'}</div>
                    {audioAnalysis?.lastProcessedEffect && (
                      <div>Last Effect: {audioAnalysis.lastProcessedEffect}</div>
                    )}
                    {audioAnalysis?.processedSamples && (
                      <div>Samples Processed: {audioAnalysis.processedSamples.toLocaleString()}</div>
                    )}
                  </div>
                  
                  {/* Processing History */}
                  {audioAnalysis?.processingHistory && audioAnalysis.processingHistory.length > 0 && (
                    <div className="mt-3">
                      <h5 className="text-xs font-medium text-blue-300 mb-1">Processing History:</h5>
                      <div className="space-y-1 max-h-20 overflow-y-auto">
                        {audioAnalysis.processingHistory.slice(-3).map((item: any, index: number) => (
                          <div key={index} className="text-xs text-gray-400">
                            {item.effect} - {(item.samplesProcessed || 0).toLocaleString()} samples
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Processed Audio Player */}
              {audioAnalysis?.processedFile && audioAnalysis?.lastProcessedEffect && (
                <div className="mt-4 p-3 bg-purple-500/10 border border-purple-500/20 rounded-lg">
                  <h4 className="text-sm font-medium text-purple-400 mb-3">
                    🎵 Processed Audio: {audioAnalysis.lastProcessedEffect}
                  </h4>
                  
                  <div className="space-y-3">
                    {/* Audio Player */}
                    <div className="flex items-center space-x-2">
                      <audio 
                        controls 
                        className="flex-1"
                        src={`http://localhost:8000/api/audio/processed/${audioAnalysis.sessionId}/${audioAnalysis.lastProcessedEffect.toLowerCase()}`}
                      >
                        Your browser does not support the audio element.
                      </audio>
                      
                      <button
                        onClick={() => playProcessedAudio(audioAnalysis.sessionId, audioAnalysis.lastProcessedEffect)}
                        className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors duration-200"
                        title="Play with Web Audio API"
                      >
                        <PlayIcon className="h-4 w-4" />
                      </button>
                    </div>
                    
                    {/* Download Link */}
                    <div className="flex items-center justify-between">
                      <div className="text-xs text-gray-400">
                        <div>Effect: {audioAnalysis.lastProcessedEffect}</div>
                        <div>Samples: {(audioAnalysis.processedSamples || 0).toLocaleString()}</div>
                        <div>File: {audioAnalysis.processedFile}</div>
                      </div>
                      
                      <a 
                        href={`http://localhost:8000/api/audio/processed/${audioAnalysis.sessionId}/${audioAnalysis.lastProcessedEffect.toLowerCase()}`}
                        download={`processed_${audioAnalysis.lastProcessedEffect}.wav`}
                        className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white text-xs rounded-lg transition-colors duration-200"
                      >
                        Download
                      </a>
                    </div>
                  </div>
                </div>
              )}

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
