import { useState, useEffect, useRef, useCallback } from 'react'
import { apiClient } from '@/services/api/client'
import { ENDPOINTS } from '@/services/api/endpoints'

/**
 * Custom React hook for MediaRecorder-based Speech-to-Text.
 *
 * Captures audio via navigator.mediaDevices.getUserMedia() + MediaRecorder,
 * posts the recorded audio Blob to backend FastAPI /api/v1/ai/transcribe,
 * and feeds the returned transcript to the parent text input state.
 */
export function useSpeechToText(options = {}) {
  const { lang = 'en-IN', onTranscript = null, maxDurationSeconds = 45 } = options

  const [isSupported, setIsSupported] = useState(() => {
    const hasMedia =
      typeof navigator !== 'undefined' && Boolean(navigator.mediaDevices?.getUserMedia)
    const hasRecorder = typeof window !== 'undefined' && Boolean(window.MediaRecorder)
    return hasMedia && hasRecorder
  })
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [error, setError] = useState(null)
  const [transcript, setTranscript] = useState('')

  const mediaRecorderRef = useRef(null)
  const streamRef = useRef(null)
  const chunksRef = useRef([])
  const timerRef = useRef(null)
  const baseTextRef = useRef('')
  const onTranscriptRef = useRef(onTranscript)
  const langRef = useRef(lang)

  useEffect(() => {
    onTranscriptRef.current = onTranscript
  }, [onTranscript])

  useEffect(() => {
    langRef.current = lang || 'en-IN'
  }, [lang])

  const getSupportedMimeType = () => {
    if (typeof MediaRecorder === 'undefined') return 'audio/webm'
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/mp4',
      'audio/ogg;codecs=opus',
      'audio/wav',
    ]
    for (const t of types) {
      if (MediaRecorder.isTypeSupported(t)) return t
    }
    return 'audio/webm'
  }

  const stopTracks = () => {
    if (streamRef.current) {
      try {
        streamRef.current.getTracks().forEach((track) => track.stop())
      } catch (err) {
        console.warn('Error stopping audio tracks:', err)
      }
      streamRef.current = null
    }
  }

  const stopRecording = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop()
      } catch (err) {
        console.warn('Error stopping MediaRecorder:', err)
        stopTracks()
        setIsRecording(false)
      }
    } else {
      stopTracks()
      setIsRecording(false)
    }
  }, [])

  const startRecording = useCallback(
    async (initialText = '') => {
      setError(null)
      baseTextRef.current = initialText ? initialText.trim() : ''
      chunksRef.current = []

      if (
        typeof navigator === 'undefined' ||
        !navigator.mediaDevices?.getUserMedia ||
        !window.MediaRecorder
      ) {
        setError('Voice recording is not supported in this browser.')
        setIsSupported(false)
        return
      }

      // Cleanup any active stream/recorder
      stopRecording()

      let stream
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        streamRef.current = stream
      } catch (mediaErr) {
        console.warn('getUserMedia failed:', mediaErr)
        if (mediaErr.name === 'NotAllowedError' || mediaErr.name === 'PermissionDeniedError') {
          setError(
            'Microphone access was denied. Please allow microphone access in browser settings.'
          )
        } else if (mediaErr.name === 'NotFoundError' || mediaErr.name === 'DevicesNotFoundError') {
          setError('No microphone hardware input device was detected.')
        } else {
          setError('Microphone could not be accessed. Please check hardware permissions.')
        }
        setIsRecording(false)
        return
      }

      try {
        const mimeType = getSupportedMimeType()
        const recorder = new MediaRecorder(stream, { mimeType })
        mediaRecorderRef.current = recorder

        recorder.ondataavailable = (e) => {
          if (e.data && e.data.size > 0) {
            chunksRef.current.push(e.data)
          }
        }

        recorder.onstop = async () => {
          stopTracks()
          setIsRecording(false)

          const audioBlob = new Blob(chunksRef.current, { type: mimeType })
          chunksRef.current = []

          if (audioBlob.size === 0) {
            setError('No audio captured. Please try speaking again.')
            return
          }

          setIsTranscribing(true)
          try {
            const formData = new FormData()
            const ext = mimeType.includes('mp4') ? 'mp4' : mimeType.includes('wav') ? 'wav' : 'webm'
            formData.append('file', audioBlob, `recording.${ext}`)
            if (langRef.current) {
              formData.append('lang', langRef.current)
            }

            const response = await apiClient.post(ENDPOINTS.ai.transcribe, formData)
            const textResult = (response?.text || '').trim()

            if (!textResult) {
              setError('No speech detected. Please try speaking again.')
            } else {
              const combined = baseTextRef.current
                ? `${baseTextRef.current} ${textResult}`
                : textResult

              setTranscript(combined)
              if (onTranscriptRef.current) {
                onTranscriptRef.current(combined)
              }
            }
          } catch (err) {
            console.error('Transcription API call failed:', err)
            setError(err.message || 'Speech transcription failed. Please try again.')
          } finally {
            setIsTranscribing(false)
          }
        }

        recorder.start(250) // Slice chunks every 250ms
        setIsRecording(true)

        // Set max duration auto-stop timer
        timerRef.current = setTimeout(() => {
          console.log(`Max recording duration reached (${maxDurationSeconds}s). Stopping...`)
          stopRecording()
        }, maxDurationSeconds * 1000)
      } catch (err) {
        console.error('Failed to start MediaRecorder:', err)
        stopTracks()
        setError('Failed to start recording. Please try again.')
        setIsRecording(false)
      }
    },
    [maxDurationSeconds, stopRecording]
  )

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        try {
          mediaRecorderRef.current.stop()
        } catch {
          /* ignore */
        }
      }
      stopTracks()
    }
  }, [])

  return {
    isSupported,
    isRecording,
    isTranscribing,
    error,
    transcript,
    setTranscript,
    startRecording,
    stopRecording,
    // Alias methods for compatibility with ChatWorkspace toolbar
    startListening: startRecording,
    stopListening: stopRecording,
    isListening: isRecording,
    clearError: () => setError(null),
  }
}

export default useSpeechToText
