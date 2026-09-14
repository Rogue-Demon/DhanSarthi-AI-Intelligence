import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useProfile, useSpeechToText } from '@/hooks'
import {
  useConversationDetail,
  useSendMessage,
  useCreateConversation,
  streamChatMessage,
  AI_KEYS,
} from '@/hooks/useAI'
import { useQueryClient } from '@tanstack/react-query'
import { getAIAdvisorConfig } from '@/config'
import { motion } from 'framer-motion'
import { Badge, Button } from '@/components/ui'
import * as LucideIcons from 'lucide-react'
import { cn } from '@/utils'

/**
 * ChatWorkspace Component
 *
 * Full-featured interactive ChatGPT-style chat interface.
 *
 * Guarantees:
 *   - 1 User message = exactly 1 AI response (no duplicates).
 *   - Isolated conversation context per `conversationId`.
 *   - Auto-creates conversation on initial prompt from welcome screen.
 *   - SSE streaming with seamless non-duplicating fallback.
 *   - Single history item per conversation thread.
 *   - Speech-to-text voice input via browser Web Speech API.
 */
export function ChatWorkspace({ conversationId = null, initialPrompt = '' }) {
  const { profile } = useProfile()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const location = useLocation()
  const advisorConfig = getAIAdvisorConfig(profile)

  const [inputText, setInputText] = useState(initialPrompt || '')
  const [optimisticMessages, setOptimisticMessages] = useState([])
  const [streamingMsg, setStreamingMsg] = useState(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isCreatingConv, setIsCreatingConv] = useState(false)
  const [expandedCalcMsgId, setExpandedCalcMsgId] = useState(null)

  const speech = useSpeechToText({
    lang: 'en-IN',
    onTranscript: (updatedText) => {
      setInputText(updatedText)
    },
  })

  const messagesEndRef = useRef(null)
  const abortControllerRef = useRef(null)
  const activeConvIdRef = useRef(conversationId)

  // Sync ref to track current active conversation
  useEffect(() => {
    activeConvIdRef.current = conversationId
  }, [conversationId])

  // Reset local transient state whenever active conversation ID changes
  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    Promise.resolve().then(() => {
      setIsStreaming(false)
      setStreamingMsg(null)
      setOptimisticMessages([])
      setIsSubmitting(false)
    })
  }, [conversationId])

  // ── Real data: load conversation messages ────────────────────────────────
  const { data: convDetail, isLoading: isLoadingHistory } = useConversationDetail(conversationId)

  // ── Mutations ────────────────────────────────────────────────────────────
  const sendMutation = useSendMessage(conversationId)
  const createMutation = useCreateConversation()

  // Auto-scroll to bottom when messages change
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [
    convDetail,
    optimisticMessages,
    streamingMsg,
    isStreaming,
    sendMutation.isPending,
    scrollToBottom,
  ])

  // Cleanup stream abort controller on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  // ── De-duplicated displayed message list ─────────────────────────────────
  const realMessages = convDetail?.messages ?? []
  const displayMessages = []
  const seenIds = new Set()

  // 1. Add real persisted messages from database
  for (const m of realMessages) {
    if (!seenIds.has(m.id)) {
      seenIds.add(m.id)
      displayMessages.push(m)
    }
  }

  // 2. Append optimistic user message only if not already present in real messages
  if (optimisticMessages.length > 0) {
    for (const optMsg of optimisticMessages) {
      const lastRealUserMsg = [...realMessages]
        .reverse()
        .find((m) => m.role === 'USER' || m.role === 'user')
      const lastRealUserTime = lastRealUserMsg?.created_at
        ? new Date(lastRealUserMsg.created_at).getTime()
        : 0
      const optMsgTime = optMsg?.created_at ? new Date(optMsg.created_at).getTime() : 0
      const isAlreadyInReal =
        lastRealUserMsg &&
        lastRealUserMsg.content.trim() === optMsg.content.trim() &&
        lastRealUserTime >= optMsgTime - 15000

      if (!isAlreadyInReal && !seenIds.has(optMsg.id)) {
        seenIds.add(optMsg.id)
        displayMessages.push(optMsg)
      }
    }
  }

  // 3. Append streaming assistant message only if no assistant response has arrived for this turn
  if (streamingMsg) {
    const hasAssistantInReal = realMessages.some(
      (m) =>
        (m.role === 'ASSISTANT' || m.role === 'assistant') &&
        new Date(m.created_at).getTime() >= new Date(streamingMsg.created_at).getTime() - 1000
    )
    if (!hasAssistantInReal && !seenIds.has(streamingMsg.id)) {
      seenIds.add(streamingMsg.id)
      displayMessages.push(streamingMsg)
    }
  }

  const isBusy =
    isStreaming || sendMutation.isPending || isCreatingConv || isSubmitting || speech.isTranscribing

  // ── Handlers ─────────────────────────────────────────────────────────────
  const executeSend = async (targetConvId, text) => {
    if (isSubmitting) return
    setIsSubmitting(true)

    const reqConvId = targetConvId
    const now = new Date().toISOString()

    const optUserMsg = {
      id: `opt-u-${Date.now()}`,
      role: 'USER',
      content: text,
      created_at: now,
      _optimistic: true,
    }
    setOptimisticMessages([optUserMsg])
    setInputText('')

    const controller = new AbortController()
    abortControllerRef.current = controller
    setIsStreaming(true)

    const tempStreamingMsg = {
      id: `streaming-asst-${Date.now()}`,
      role: 'ASSISTANT',
      content: '',
      created_at: now,
      _isStreaming: true,
      metadata: {},
    }
    setStreamingMsg(tempStreamingMsg)

    let streamStarted = false
    let currentContent = ''

    try {
      await streamChatMessage({
        conversationId: reqConvId,
        message: text,
        signal: controller.signal,
        onStart: () => {
          if (activeConvIdRef.current !== reqConvId) return
          streamStarted = true
        },
        onToken: (token) => {
          if (activeConvIdRef.current !== reqConvId) return
          streamStarted = true
          currentContent += token
          setStreamingMsg((prev) => (prev ? { ...prev, content: currentContent } : prev))
        },
        onMetadata: (meta) => {
          if (activeConvIdRef.current !== reqConvId) return
          setStreamingMsg((prev) => (prev ? { ...prev, metadata: meta } : prev))
        },
        onComplete: () => {
          if (activeConvIdRef.current !== reqConvId) return
          queryClient.invalidateQueries({ queryKey: AI_KEYS.conversation(reqConvId) })
          queryClient.invalidateQueries({ queryKey: ['ai-conversations'] })
          setStreamingMsg(null)
          setOptimisticMessages([])
          setIsStreaming(false)
          setIsSubmitting(false)
          abortControllerRef.current = null
        },
        onError: (err) => {
          if (activeConvIdRef.current !== reqConvId) return
          console.warn('Stream interrupted or unsupported, falling back to standard API:', err)
          // Fallback mutation is handled in catch block below to prevent duplicate execution
        },
      })
    } catch (err) {
      if (activeConvIdRef.current !== reqConvId) return
      if (err.name === 'AbortError') {
        setStreamingMsg(null)
        setOptimisticMessages([])
        setIsStreaming(false)
        setIsSubmitting(false)
        return
      }
      if (!streamStarted) {
        setStreamingMsg(null)
        setIsStreaming(false)
        sendMutation.mutate(
          { message: text },
          {
            onSuccess: () => {
              queryClient.invalidateQueries({ queryKey: AI_KEYS.conversation(reqConvId) })
              queryClient.invalidateQueries({ queryKey: ['ai-conversations'] })
            },
            onSettled: () => {
              setOptimisticMessages([])
              setIsSubmitting(false)
            },
          }
        )
      } else {
        queryClient.invalidateQueries({ queryKey: AI_KEYS.conversation(reqConvId) })
        setStreamingMsg(null)
        setOptimisticMessages([])
        setIsStreaming(false)
        setIsSubmitting(false)
      }
    }
  }

  const handleSend = async () => {
    if (speech.isListening) {
      speech.stopListening()
    }
    const text = inputText.trim()
    if (!text || isBusy) return

    // Welcome Screen behavior (no active conversationId yet): create thread first
    if (!conversationId) {
      setIsCreatingConv(true)
      createMutation.mutate(
        { title: null },
        {
          onSuccess: (data) => {
            setIsCreatingConv(false)
            navigate(`/ai-advisor/chat/${data.id}`)
            // Execute send under the new conversation ID
            setTimeout(() => {
              executeSend(data.id, text)
            }, 100)
          },
          onError: () => {
            setIsCreatingConv(false)
            setIsSubmitting(false)
          },
        }
      )
      return
    }

    executeSend(conversationId, text)
  }

  const executeSendRef = useRef(executeSend)
  useEffect(() => {
    executeSendRef.current = executeSend
  })

  // Handle initial send if state passed from navigation or prompt click
  useEffect(() => {
    if (location.state?.autoSendText && conversationId && !isSubmitting) {
      const text = location.state.autoSendText
      // Clear location state to prevent re-sending on re-render
      navigate(location.pathname, { replace: true, state: {} })
      Promise.resolve().then(() => {
        executeSendRef.current(conversationId, text)
      })
    }
  }, [conversationId, location.state, location.pathname, navigate, isSubmitting])

  const handleStopStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsStreaming(false)
    setStreamingMsg(null)
    setOptimisticMessages([])
    setIsSubmitting(false)
    if (conversationId) {
      queryClient.invalidateQueries({ queryKey: AI_KEYS.conversation(conversationId) })
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handlePromptClick = (promptText) => {
    if (!conversationId) {
      // On welcome screen, clicking a prompt directly starts a conversation and sends it
      setInputText(promptText)
      setIsCreatingConv(true)
      createMutation.mutate(
        { title: null },
        {
          onSuccess: (data) => {
            setIsCreatingConv(false)
            navigate(`/ai-advisor/chat/${data.id}`)
            setTimeout(() => {
              executeSend(data.id, promptText)
            }, 100)
          },
          onError: () => {
            setIsCreatingConv(false)
          },
        }
      )
    } else {
      setInputText(promptText)
    }
  }

  const handleCopy = (content) => {
    navigator.clipboard?.writeText(content).catch(() => {})
  }

  // ── Welcome screen (no conversation loaded yet) ───────────────────────────
  if (!conversationId) {
    return (
      <div className="flex flex-col h-full w-full bg-background overflow-hidden relative select-none">
        <div className="flex-1 overflow-y-auto p-4 md:p-6 scrollbar-none">
          <div className="flex flex-col items-center justify-center min-h-[70%] text-center max-w-2xl mx-auto gap-6 my-auto py-10">
            <div className="h-16 w-16 rounded-3xl bg-gradient-primary flex items-center justify-center text-white shadow-floating">
              <LucideIcons.Sparkles className="h-8 w-8 animate-pulse" />
            </div>
            <div className="flex flex-col gap-2">
              <Badge
                variant="secondary"
                className="mx-auto text-[10px] font-black uppercase tracking-widest bg-primary/10 text-primary border-primary/20 py-0.5 px-3 rounded-full"
              >
                AI Financial Workspace
              </Badge>
              <h3 className="text-2xl md:text-3xl font-black text-text-primary tracking-tight">
                {advisorConfig.welcome.greeting}
              </h3>
              <p className="text-xs md:text-sm font-semibold text-text-muted leading-relaxed max-w-lg">
                {advisorConfig.welcome.description}
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full pt-4">
              {advisorConfig.suggestedPrompts.map((prompt, idx) => {
                const Icon = LucideIcons[prompt.icon] || LucideIcons.HelpCircle
                return (
                  <motion.button
                    key={idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    onClick={() => handlePromptClick(prompt.text)}
                    className="clay-surface bg-card p-4 border border-white/60 dark:border-white/5 shadow-card hover:border-primary/30 transition-all text-left flex items-start gap-3 group cursor-pointer"
                  >
                    <div className="p-2 rounded-xl bg-primary/10 text-primary shrink-0">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex flex-col gap-0.5">
                      <span className="text-[9px] font-black text-text-muted uppercase tracking-wider">
                        {prompt.category}
                      </span>
                      <span className="text-xs font-bold text-text-primary group-hover:text-primary transition-colors">
                        {prompt.text}
                      </span>
                    </div>
                  </motion.button>
                )
              })}
            </div>
          </div>
        </div>

        {/* Welcome Input Area */}
        <div className="p-4 border-t border-border/80 bg-card/80 backdrop-blur-md shrink-0">
          <div className="max-w-3xl mx-auto flex flex-col gap-2">
            {speech.error && (
              <div className="flex items-center justify-between text-[11px] font-bold text-danger bg-danger/10 border border-danger/20 rounded-xl px-3 py-1.5">
                <span className="flex items-center gap-1.5">
                  <LucideIcons.AlertCircle className="h-3.5 w-3.5 shrink-0" />
                  {speech.error}
                </span>
                <button onClick={speech.clearError} className="hover:opacity-80 p-0.5">
                  <LucideIcons.X className="h-3.5 w-3.5" />
                </button>
              </div>
            )}

            {/* Speech Recording / Transcribing Banners */}
            {speech.isRecording && (
              <div className="flex items-center justify-between text-[11px] font-bold text-danger bg-danger/10 border border-danger/20 rounded-xl px-3 py-1.5 animate-pulse">
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-danger animate-ping" />
                  Listening... Speak into your microphone. Click mic or Done when finished.
                </span>
                <button
                  type="button"
                  onClick={() => speech.stopListening()}
                  className="text-[10px] font-black uppercase tracking-wider bg-danger text-white px-2 py-0.5 rounded-lg hover:bg-danger/90 transition-colors"
                >
                  Done
                </button>
              </div>
            )}
            {speech.isTranscribing && (
              <div className="flex items-center gap-1.5 text-[11px] font-bold text-primary bg-primary/10 border border-primary/20 rounded-xl px-3 py-1.5">
                <LucideIcons.Loader2 className="h-3.5 w-3.5 animate-spin shrink-0 text-primary" />
                <span>Converting speech to text...</span>
              </div>
            )}

            <div className="relative clay-surface bg-card border border-border rounded-2xl p-2.5 shadow-sm focus-within:border-primary/40 transition-colors flex items-end gap-2">
              <textarea
                rows={2}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask DhanSarthi AI anything about your finances…"
                disabled={isBusy}
                className="w-full bg-transparent text-xs md:text-sm font-semibold text-text-primary placeholder:text-text-muted resize-none focus:outline-none px-2 py-1 scrollbar-none disabled:opacity-50"
              />

              <div className="flex items-center gap-1.5 shrink-0">
                {inputText && (
                  <button
                    onClick={() => setInputText('')}
                    className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-muted"
                    title="Clear text"
                  >
                    <LucideIcons.X className="h-4 w-4" />
                  </button>
                )}

                {/* Speech-to-text mic button */}
                <button
                  type="button"
                  onClick={() => {
                    if (speech.isRecording) {
                      speech.stopListening()
                    } else if (!speech.isTranscribing) {
                      speech.startListening(inputText)
                    }
                  }}
                  disabled={!speech.isSupported || isBusy}
                  className={cn(
                    'p-2 rounded-xl transition-all duration-200 cursor-pointer flex items-center justify-center',
                    speech.isRecording &&
                      'bg-danger/20 text-danger border border-danger/40 animate-pulse shadow-sm',
                    speech.isTranscribing &&
                      'bg-primary/20 text-primary border border-primary/40 shadow-sm',
                    !speech.isRecording &&
                      !speech.isTranscribing &&
                      'text-text-muted hover:text-text-primary hover:bg-muted/80 border border-transparent',
                    (!speech.isSupported || (isBusy && !speech.isRecording)) &&
                      'opacity-40 cursor-not-allowed'
                  )}
                  title={
                    !speech.isSupported
                      ? 'Voice input is not supported in this browser'
                      : speech.isTranscribing
                        ? 'Transcribing audio...'
                        : speech.isRecording
                          ? 'Recording... Click to stop & transcribe'
                          : 'Speak (Voice Input)'
                  }
                >
                  {speech.isTranscribing ? (
                    <LucideIcons.Loader2 className="h-4 w-4 text-primary animate-spin" />
                  ) : speech.isRecording ? (
                    <LucideIcons.MicOff className="h-4 w-4 text-danger animate-pulse" />
                  ) : (
                    <LucideIcons.Mic className="h-4 w-4" />
                  )}
                </button>

                <Button
                  variant="gradient"
                  size="sm"
                  onClick={handleSend}
                  disabled={!inputText.trim() || isBusy}
                  className="rounded-xl px-3 py-2 font-black text-xs shadow-button"
                  iconLeft={
                    isBusy ? (
                      <LucideIcons.Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <LucideIcons.Send className="h-3.5 w-3.5" />
                    )
                  }
                >
                  {isCreatingConv ? 'Starting…' : 'Send'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // ── Chat view (active conversation loaded) ──────────────────────────────
  return (
    <div className="flex flex-col h-full w-full bg-background overflow-hidden relative select-none">
      {/* Scrollable Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 scrollbar-none">
        {/* Loading history skeleton */}
        {isLoadingHistory && (
          <div className="flex flex-col gap-4 max-w-3xl mx-auto w-full pt-6">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className={cn(
                  'flex items-start gap-3',
                  i % 2 === 0 ? 'flex-row-reverse' : 'flex-row'
                )}
              >
                <div className="h-8 w-8 rounded-xl bg-muted animate-pulse shrink-0" />
                <div
                  className={cn('flex flex-col gap-2', i % 2 === 0 ? 'items-end' : 'items-start')}
                >
                  <div className="h-3 w-20 rounded bg-muted animate-pulse" />
                  <div className="h-16 w-64 rounded-2xl bg-muted animate-pulse" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty state for new conversation */}
        {!isLoadingHistory && displayMessages.length === 0 && (
          <div className="flex flex-col items-center justify-center min-h-[60%] text-center max-w-2xl mx-auto gap-4 py-10">
            <div className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
              <LucideIcons.MessageSquare className="h-7 w-7" />
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-sm font-black text-text-primary uppercase tracking-wider">
                Ready to Advise
              </span>
              <p className="text-xs font-bold text-text-muted max-w-xs">
                Ask DhanSarthi AI anything about your finances below.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2 pt-2">
              {advisorConfig.suggestedPrompts.slice(0, 3).map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handlePromptClick(p.text)}
                  className="text-[10px] font-bold px-3 py-1.5 rounded-xl bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 transition-colors cursor-pointer"
                >
                  {p.text}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages List */}
        {!isLoadingHistory && displayMessages.length > 0 && (
          <div className="flex flex-col gap-5 max-w-3xl mx-auto w-full">
            {displayMessages.map((msg) => {
              const isUser = msg.role === 'USER' || msg.role === 'user'
              const timeStr = msg.created_at
                ? typeof msg.created_at === 'string' && msg.created_at.includes('T')
                  ? new Date(msg.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })
                  : msg.created_at
                : ''
              const meta = msg.message_metadata || msg.metadata || {}
              const citations = meta.citations ?? []
              const sources = meta.source_ids ?? []

              return (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn(
                    'flex items-start gap-3 w-full',
                    isUser ? 'flex-row-reverse' : 'flex-row'
                  )}
                >
                  {/* Avatar */}
                  <div
                    className={cn(
                      'h-8 w-8 rounded-xl flex items-center justify-center shrink-0 text-white font-black text-xs shadow-xs',
                      isUser ? 'bg-accent' : 'bg-gradient-primary'
                    )}
                  >
                    {isUser ? (
                      <LucideIcons.User className="h-4 w-4" />
                    ) : (
                      <LucideIcons.Bot className="h-4 w-4" />
                    )}
                  </div>

                  {/* Message Content */}
                  <div
                    className={cn(
                      'flex flex-col gap-1.5 max-w-[85%] text-left',
                      isUser ? 'items-end' : 'items-start'
                    )}
                  >
                    <div className="flex items-center gap-2 px-1">
                      <span className="text-[10px] font-black text-text-muted uppercase tracking-wider">
                        {isUser ? 'You' : 'DhanSarthi AI'}
                      </span>
                      {timeStr && (
                        <span className="text-[9px] font-bold text-text-muted">{timeStr}</span>
                      )}
                      {msg._optimistic && (
                        <span className="text-[9px] font-bold text-text-muted italic">
                          sending…
                        </span>
                      )}
                    </div>

                    <div
                      className={cn(
                        'p-4 rounded-2xl text-xs md:text-sm font-medium leading-relaxed shadow-xs whitespace-pre-wrap',
                        isUser
                          ? 'bg-primary text-white rounded-tr-none'
                          : 'clay-surface bg-card border border-white/60 dark:border-white/5 text-text-primary rounded-tl-none'
                      )}
                    >
                      {msg.content ||
                        (msg._isStreaming ? (
                          <span className="inline-flex items-center gap-1.5 text-text-muted italic font-semibold">
                            <LucideIcons.Sparkles className="h-3.5 w-3.5 animate-spin text-primary" />
                            Thinking…
                          </span>
                        ) : null)}
                      {msg._isStreaming && msg.content ? (
                        <span className="inline-block w-1.5 h-3.5 ml-0.5 bg-primary animate-pulse align-middle" />
                      ) : null}
                    </div>

                    {/* Assistant Action Toolbar */}
                    {!isUser && !msg._optimistic && (
                      <div className="flex items-center gap-1 pt-1 text-text-muted flex-wrap">
                        <button
                          className="p-1 rounded hover:bg-muted text-text-muted hover:text-text-primary"
                          title="Copy text"
                          onClick={() => handleCopy(msg.content)}
                        >
                          <LucideIcons.Copy className="h-3.5 w-3.5" />
                        </button>
                        <button
                          className="p-1 rounded hover:bg-muted text-text-muted hover:text-success"
                          title="Helpful"
                        >
                          <LucideIcons.ThumbsUp className="h-3.5 w-3.5" />
                        </button>
                        <button
                          className="p-1 rounded hover:bg-muted text-text-muted hover:text-danger"
                          title="Not helpful"
                        >
                          <LucideIcons.ThumbsDown className="h-3.5 w-3.5" />
                        </button>
                        <button
                          className="p-1 rounded hover:bg-muted text-text-muted hover:text-accent"
                          title="Bookmark"
                        >
                          <LucideIcons.Bookmark className="h-3.5 w-3.5" />
                        </button>
                        {meta.used_user_financial_data && (
                          <span className="inline-flex items-center gap-1 text-[9px] font-bold text-emerald-600 bg-emerald-500/10 border border-emerald-500/20 rounded px-1.5 py-0.5">
                            <LucideIcons.CheckCircle2 className="h-3 w-3" />
                            <span>Based on your financial data</span>
                          </span>
                        )}
                        {meta.signals && meta.signals.length > 0 && (
                          <div className="flex items-center gap-1 flex-wrap">
                            {meta.signals.slice(0, 2).map((sig, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center gap-1 text-[9px] font-bold text-amber-600 bg-amber-500/10 border border-amber-500/20 rounded px-1.5 py-0.5"
                                title={sig.evidence}
                              >
                                <LucideIcons.AlertTriangle className="h-2.5 w-2.5" />
                                <span>{sig.title}</span>
                              </span>
                            ))}
                          </div>
                        )}
                        {(meta.calculation_performed ||
                          (meta.calculation_details && meta.calculation_details.length > 0) ||
                          (meta.health_score?.breakdown &&
                            meta.health_score.breakdown.length > 0)) && (
                          <button
                            onClick={() =>
                              setExpandedCalcMsgId(expandedCalcMsgId === msg.id ? null : msg.id)
                            }
                            className="inline-flex items-center gap-1 text-[9px] font-bold text-primary bg-primary/10 border border-primary/20 rounded px-1.5 py-0.5 hover:bg-primary/20 transition-colors"
                          >
                            <LucideIcons.Calculator className="h-3 w-3" />
                            <span>How this was calculated</span>
                            <LucideIcons.ChevronDown
                              className={cn(
                                'h-2.5 w-2.5 transition-transform',
                                expandedCalcMsgId === msg.id && 'rotate-180'
                              )}
                            />
                          </button>
                        )}
                        {citations.length > 0 ? (
                          <div className="flex items-center gap-1.5 flex-wrap ml-1">
                            {citations.slice(0, 3).map((cit, idx) => (
                              <a
                                key={idx}
                                href={cit.source_url || '#'}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-[9px] font-bold text-accent bg-accent/10 border border-accent/20 rounded px-1.5 py-0.5 hover:bg-accent/20 transition-colors"
                                title={cit.title}
                              >
                                <LucideIcons.ShieldCheck className="h-3 w-3" />
                                <span>
                                  {cit.authority || 'OFFICIAL'}: {cit.title}
                                </span>
                                {cit.source_url && (
                                  <LucideIcons.ExternalLink className="h-2.5 w-2.5 opacity-70" />
                                )}
                              </a>
                            ))}
                          </div>
                        ) : sources.length > 0 ? (
                          <span className="ml-1 text-[9px] font-bold text-text-muted border border-border/40 rounded px-1.5 py-0.5">
                            {sources.length} source{sources.length > 1 ? 's' : ''}
                          </span>
                        ) : null}
                      </div>
                    )}

                    {/* How Was This Calculated Accordion */}
                    {!isUser &&
                      expandedCalcMsgId === msg.id &&
                      (meta.calculation_details || meta.health_score?.breakdown) && (
                        <div className="w-full mt-2 p-3 bg-muted/30 border border-border/60 rounded-xl flex flex-col gap-2 text-xs">
                          <div className="flex items-center justify-between font-bold text-text-primary border-b border-border/40 pb-1.5">
                            <span className="flex items-center gap-1.5">
                              <LucideIcons.Calculator className="h-3.5 w-3.5 text-primary" />
                              Deterministic Calculation Breakdown
                            </span>
                            {meta.health_score?.overall_score != null && (
                              <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded-full font-black">
                                Score: {meta.health_score.overall_score}/100 (
                                {meta.health_score.status})
                              </span>
                            )}
                          </div>
                          <div className="flex flex-col gap-2 pt-1">
                            {meta.calculation_details && meta.calculation_details.length > 0
                              ? meta.calculation_details.map((item, idx) => (
                                  <div
                                    key={idx}
                                    className="flex flex-col gap-0.5 bg-card/60 p-2 rounded-lg border border-border/30"
                                  >
                                    <div className="flex justify-between items-center font-bold text-[11px] text-text-primary">
                                      <span>{item.title || item.dimension || item.type}</span>
                                      {item.source && (
                                        <span className="text-text-muted text-[10px]">
                                          Source: {item.source}
                                        </span>
                                      )}
                                    </div>
                                    {item.formula && (
                                      <div className="text-[10px] font-mono text-primary/90 bg-primary/5 px-1.5 py-0.5 rounded">
                                        Formula: {item.formula}
                                      </div>
                                    )}
                                    {item.inputs && (
                                      <div className="text-[10px] text-text-muted font-mono bg-muted/20 p-1 rounded">
                                        Inputs: {JSON.stringify(item.inputs)}
                                      </div>
                                    )}
                                    {item.explanation && (
                                      <div className="text-[10px] text-text-muted">
                                        {item.explanation}
                                      </div>
                                    )}
                                  </div>
                                ))
                              : meta.health_score?.breakdown
                                ? meta.health_score.breakdown.map((item, idx) => (
                                    <div
                                      key={idx}
                                      className="flex flex-col gap-0.5 bg-card/60 p-2 rounded-lg border border-border/30"
                                    >
                                      <div className="flex justify-between items-center font-bold text-[11px] text-text-primary">
                                        <span>{item.dimension}</span>
                                        <span className="text-text-muted">
                                          Weight: {item.weight_percent}% | Score:{' '}
                                          {item.score ?? 'N/A'}
                                        </span>
                                      </div>
                                      <div className="text-[10px] font-mono text-primary/90 bg-primary/5 px-1.5 py-0.5 rounded">
                                        Formula: {item.formula}
                                      </div>
                                      <div className="text-[10px] text-text-muted">
                                        {item.explanation}
                                      </div>
                                    </div>
                                  ))
                                : null}
                          </div>
                        </div>
                      )}
                  </div>
                </motion.div>
              )
            })}

            {/* Typing / Loading Indicator */}
            {sendMutation.isPending && (
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-xl bg-gradient-primary flex items-center justify-center text-white shrink-0">
                  <LucideIcons.Bot className="h-4 w-4" />
                </div>
                <div className="clay-surface bg-card p-3 rounded-2xl border border-white/60 flex items-center gap-1.5">
                  <span
                    className="h-2 w-2 rounded-full bg-primary animate-bounce"
                    style={{ animationDelay: '0ms' }}
                  />
                  <span
                    className="h-2 w-2 rounded-full bg-primary animate-bounce"
                    style={{ animationDelay: '150ms' }}
                  />
                  <span
                    className="h-2 w-2 rounded-full bg-primary animate-bounce"
                    style={{ animationDelay: '300ms' }}
                  />
                </div>
              </div>
            )}

            {/* Error state */}
            {sendMutation.isError && (
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-danger/10 border border-danger/20 text-danger text-xs font-bold max-w-3xl mx-auto w-full">
                <LucideIcons.AlertCircle className="h-4 w-4 shrink-0" />
                <span>
                  {sendMutation.error?.message || 'Failed to send message. Please try again.'}
                </span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-border/80 bg-card/80 backdrop-blur-md shrink-0">
        <div className="max-w-3xl mx-auto flex flex-col gap-2">
          {speech.error && (
            <div className="flex items-center justify-between text-[11px] font-bold text-danger bg-danger/10 border border-danger/20 rounded-xl px-3 py-1.5">
              <span className="flex items-center gap-1.5">
                <LucideIcons.AlertCircle className="h-3.5 w-3.5 shrink-0" />
                {speech.error}
              </span>
              <button onClick={speech.clearError} className="hover:opacity-80 p-0.5">
                <LucideIcons.X className="h-3.5 w-3.5" />
              </button>
            </div>
          )}

          {/* Speech Recording / Transcribing Banners */}
          {speech.isRecording && (
            <div className="flex items-center justify-between text-[11px] font-bold text-danger bg-danger/10 border border-danger/20 rounded-xl px-3 py-1.5 animate-pulse">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-danger animate-ping" />
                Listening... Speak into your microphone. Click mic or Done when finished.
              </span>
              <button
                type="button"
                onClick={() => speech.stopListening()}
                className="text-[10px] font-black uppercase tracking-wider bg-danger text-white px-2 py-0.5 rounded-lg hover:bg-danger/90 transition-colors"
              >
                Done
              </button>
            </div>
          )}
          {speech.isTranscribing && (
            <div className="flex items-center gap-1.5 text-[11px] font-bold text-primary bg-primary/10 border border-primary/20 rounded-xl px-3 py-1.5">
              <LucideIcons.Loader2 className="h-3.5 w-3.5 animate-spin shrink-0 text-primary" />
              <span>Converting speech to text...</span>
            </div>
          )}

          {/* Quick suggestions strip */}
          <div className="flex items-center gap-2 overflow-x-auto scrollbar-none pb-1">
            {advisorConfig.suggestedPrompts.slice(0, 3).map((p, idx) => (
              <button
                key={idx}
                onClick={() => handlePromptClick(p.text)}
                className="text-[10px] font-bold px-2.5 py-1 rounded-lg bg-muted/40 border border-border/60 text-text-muted hover:text-text-primary hover:border-primary/20 shrink-0 cursor-pointer transition-colors"
              >
                + {p.text}
              </button>
            ))}
          </div>

          {/* Textarea Input Container */}
          <div className="relative clay-surface bg-card border border-border rounded-2xl p-2.5 shadow-sm focus-within:border-primary/40 transition-colors flex items-end gap-2">
            <textarea
              rows={2}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask DhanSarthi AI anything about your finances…"
              disabled={isBusy}
              className="w-full bg-transparent text-xs md:text-sm font-semibold text-text-primary placeholder:text-text-muted resize-none focus:outline-none px-2 py-1 scrollbar-none disabled:opacity-50"
            />

            {/* Input Actions Toolbar */}
            <div className="flex items-center gap-1.5 shrink-0">
              {inputText && (
                <button
                  onClick={() => setInputText('')}
                  className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-muted"
                  title="Clear text"
                >
                  <LucideIcons.X className="h-4 w-4" />
                </button>
              )}

              {/* Speech-to-text mic button */}
              <button
                type="button"
                onClick={() => {
                  if (speech.isRecording) {
                    speech.stopListening()
                  } else if (!speech.isTranscribing) {
                    speech.startListening(inputText)
                  }
                }}
                disabled={!speech.isSupported || isBusy}
                className={cn(
                  'p-2 rounded-xl transition-all duration-200 cursor-pointer flex items-center justify-center',
                  speech.isRecording &&
                    'bg-danger/20 text-danger border border-danger/40 animate-pulse shadow-sm',
                  speech.isTranscribing &&
                    'bg-primary/20 text-primary border border-primary/40 shadow-sm',
                  !speech.isRecording &&
                    !speech.isTranscribing &&
                    'text-text-muted hover:text-text-primary hover:bg-muted/80 border border-transparent',
                  (!speech.isSupported || (isBusy && !speech.isRecording)) &&
                    'opacity-40 cursor-not-allowed'
                )}
                title={
                  !speech.isSupported
                    ? 'Voice input is not supported in this browser'
                    : speech.isTranscribing
                      ? 'Transcribing audio...'
                      : speech.isRecording
                        ? 'Recording... Click to stop & transcribe'
                        : 'Speak (Voice Input)'
                }
              >
                {speech.isTranscribing ? (
                  <LucideIcons.Loader2 className="h-4 w-4 text-primary animate-spin" />
                ) : speech.isRecording ? (
                  <LucideIcons.MicOff className="h-4 w-4 text-danger animate-pulse" />
                ) : (
                  <LucideIcons.Mic className="h-4 w-4" />
                )}
              </button>

              {isStreaming ? (
                <Button
                  variant="danger"
                  size="sm"
                  onClick={handleStopStream}
                  className="rounded-xl px-3 py-2 font-black text-xs shadow-button"
                  iconLeft={<LucideIcons.Square className="h-3.5 w-3.5 fill-current" />}
                >
                  Stop
                </Button>
              ) : (
                <Button
                  variant="gradient"
                  size="sm"
                  onClick={handleSend}
                  disabled={!inputText.trim() || isBusy}
                  className="rounded-xl px-3 py-2 font-black text-xs shadow-button"
                  iconLeft={
                    isBusy ? (
                      <LucideIcons.Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <LucideIcons.Send className="h-3.5 w-3.5" />
                    )
                  }
                >
                  {isBusy ? 'Processing…' : 'Send'}
                </Button>
              )}
            </div>
          </div>

          {/* Footer hints */}
          <div className="flex justify-between items-center px-1 text-[9px] font-bold text-text-muted">
            <span>Press Shift + Enter for line break</span>
            <span>{inputText.length} chars</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatWorkspace
