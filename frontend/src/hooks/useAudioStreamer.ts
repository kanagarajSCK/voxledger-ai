import { useState, useRef, useCallback } from 'react'

export interface UseAudioStreamerOptions {
  onAudioChunk: (chunk: ArrayBuffer) => void
  sampleRate?: number
}

export function useAudioStreamer({ onAudioChunk, sampleRate = 16000 }: UseAudioStreamerOptions) {
  const [isRecording, setIsRecording] = useState(false)
  const [volumeLevel, setVolumeLevel] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const mediaStreamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const processorRef = useRef<ScriptProcessorNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)

  const startRecording = useCallback(async () => {
    setError(null)
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Microphone audio recording is not supported in this browser.')
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })
      mediaStreamRef.current = stream

      const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      const audioCtx = new AudioContextClass()
      audioContextRef.current = audioCtx

      if (audioCtx.state === 'suspended') {
        await audioCtx.resume()
      }

      const source = audioCtx.createMediaStreamSource(stream)
      sourceRef.current = source

      // ScriptProcessor buffer size 2048 (~42ms at 48kHz, ~128ms at 16kHz)
      const processor = audioCtx.createScriptProcessor(2048, 1, 1)
      processorRef.current = processor

      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0)

        // Calculate RMS volume level for UI visualizer
        let sumSquares = 0
        for (let i = 0; i < inputData.length; i++) {
          sumSquares += inputData[i] * inputData[i]
        }
        const rms = Math.sqrt(sumSquares / inputData.length)
        setVolumeLevel(Math.min(1, rms * 4))

        // Convert to 16kHz 16-bit mono linear PCM
        const pcm16 = downsampleTo16kPCM(inputData, audioCtx.sampleRate, sampleRate)
        onAudioChunk(pcm16.buffer as ArrayBuffer)
      }

      source.connect(processor)
      processor.connect(audioCtx.destination)

      setIsRecording(true)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to access microphone'
      setError(msg)
      setIsRecording(false)
    }
  }, [onAudioChunk, sampleRate])

  const stopRecording = useCallback(() => {
    setIsRecording(false)
    setVolumeLevel(0)

    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }

    if (sourceRef.current) {
      sourceRef.current.disconnect()
      sourceRef.current = null
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close().catch(() => {})
      audioContextRef.current = null
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      mediaStreamRef.current = null
    }
  }, [])

  return {
    isRecording,
    volumeLevel,
    error,
    startRecording,
    stopRecording,
  }
}

function downsampleTo16kPCM(
  buffer: Float32Array,
  inputSampleRate: number,
  targetSampleRate: number = 16000
): Int16Array {
  if (inputSampleRate === targetSampleRate) {
    const output = new Int16Array(buffer.length)
    for (let i = 0; i < buffer.length; i++) {
      const s = Math.max(-1, Math.min(1, buffer[i]))
      output[i] = s < 0 ? s * 0x8000 : s * 0x7fff
    }
    return output
  }

  const sampleRateRatio = inputSampleRate / targetSampleRate
  const newLength = Math.round(buffer.length / sampleRateRatio)
  const result = new Int16Array(newLength)
  let offsetResult = 0
  let offsetBuffer = 0

  while (offsetResult < result.length) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio)
    let accum = 0
    let count = 0
    for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
      accum += buffer[i]
      count++
    }
    const avg = count > 0 ? accum / count : 0
    const s = Math.max(-1, Math.min(1, avg))
    result[offsetResult] = s < 0 ? s * 0x8000 : s * 0x7fff
    offsetResult++
    offsetBuffer = nextOffsetBuffer
  }
  return result
}
