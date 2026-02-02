import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2, Brain, ChevronDown, AlertCircle, CheckCircle2, Paperclip, X, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import FormattedContent from './FormattedContent'
import './Query.css'

const DIFFICULTY_LEVELS = [
  { value: 'undergrad', label: 'Undergraduate' },
  { value: 'med', label: 'Medical School' },
  { value: 'advanced', label: 'Advanced' },
]

const SYSTEM_FILTERS = [
  { value: null, label: 'All Systems' },
  { value: 'limbic', label: 'Limbic' },
  { value: 'brainstem', label: 'Brainstem' },
  { value: 'cortical', label: 'Cortical' },
  { value: 'cerebellar', label: 'Cerebellar' },
  { value: 'spinal', label: 'Spinal' },
  { value: 'vascular', label: 'Vascular' },
  { value: 'cranial_nerve', label: 'Cranial Nerve' },
]

function Query() {
  const { chatMessages, setChatMessages } = useApp()
  const messages = chatMessages
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [difficulty, setDifficulty] = useState('undergrad')
  const [systemFilter, setSystemFilter] = useState(null)
  const [clinicalOnly, setClinicalOnly] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('checking')
  const [attachedFiles, setAttachedFiles] = useState([])
  const fileInputRef = useRef(null)
  const messagesEndRef = useRef(null)
  const userId = localStorage.getItem('userId') || `user_${Date.now()}`

  useEffect(() => {
    if (!localStorage.getItem('userId')) {
      localStorage.setItem('userId', userId)
    }
  }, [userId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    // Check backend connection on mount
    const checkConnection = async () => {
      try {
        await api.health()
        setConnectionStatus('connected')
      } catch (error) {
        setConnectionStatus('disconnected')
      }
    }
    checkConnection()
  }, [])

  const handleFileAttach = (e) => {
    const files = Array.from(e.target.files || [])
    const valid = files.filter(f => /\.(pdf|pptx|ppt|html|htm|txt)$/i.test(f.name))
    setAttachedFiles(prev => [...prev, ...valid])
    e.target.value = ''
  }

  const removeFile = (idx) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== idx))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if ((!input.trim() && attachedFiles.length === 0) || loading) return

    const queryText = input.trim() || `Summarize and explain the content of the attached document${attachedFiles.length > 1 ? 's' : ''}.`
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: queryText + (attachedFiles.length ? ` [${attachedFiles.map(f => f.name).join(', ')}]` : ''),
      timestamp: new Date(),
    }

    setChatMessages(prev => [...prev, userMessage])
    setInput('')
    const filesToSend = [...attachedFiles]
    setAttachedFiles([])
    setLoading(true)

    try {
      let response
      if (filesToSend.length > 0) {
        response = await api.queryWithFiles(queryText, filesToSend, {
          userId,
          difficultyLevel: difficulty,
          systemFilter: systemFilter || undefined,
          clinicalOnly: clinicalOnly
        })
      } else {
        response = await api.query({
          query: queryText,
          user_id: userId,
          difficulty_level: difficulty,
          system_filter: systemFilter,
          clinical_only: clinicalOnly,
        })
      }

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: response.answer,
        sources: response.sources,
        confidence: response.confidence,
        intent: response.intent,
        timestamp: new Date(),
      }

      setChatMessages(prev => [...prev, botMessage])
    } catch (error) {
      let errorContent = 'Failed to get response. Please try again.'
      
      if (error.response) {
        // Server responded with error status
        errorContent = error.response.data?.detail || error.response.data?.message || errorContent
      } else if (error.message) {
        // Network or other error
        errorContent = error.message
      }
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: errorContent,
        timestamp: new Date(),
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="query-container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="query-header"
      >
        <div className="header-content">
          <Brain className="header-icon" />
          <div>
            <h2>Ask Questions</h2>
            <p>Get answers about neuroanatomy from our knowledge base</p>
          </div>
        </div>
        <div className="header-actions">
          {messages.length > 0 && (
            <button
              type="button"
              onClick={() => setChatMessages([])}
              className="clear-chat-btn"
              title="Clear conversation"
            >
              <Trash2 size={16} />
              <span>Clear</span>
            </button>
          )}
          {connectionStatus === 'disconnected' && (
            <div className="connection-status error">
              <AlertCircle size={16} />
              <span>Backend disconnected</span>
            </div>
          )}
          {connectionStatus === 'connected' && (
            <div className="connection-status success">
              <CheckCircle2 size={16} />
              <span>Connected</span>
            </div>
          )}
          <button
            className="filter-toggle"
            onClick={() => setShowFilters(!showFilters)}
          >
            <span>Filters</span>
            <ChevronDown className={showFilters ? 'rotated' : ''} />
          </button>
        </div>
      </motion.div>

      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="filters-panel"
          >
            <div className="filter-group">
              <label>Difficulty Level</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="filter-select"
              >
                {DIFFICULTY_LEVELS.map(level => (
                  <option key={level.value} value={level.value}>
                    {level.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="filter-group">
              <label>System Filter</label>
              <select
                value={systemFilter || ''}
                onChange={(e) => setSystemFilter(e.target.value || null)}
                className="filter-select"
              >
                {SYSTEM_FILTERS.map(filter => (
                  <option key={filter.value || 'all'} value={filter.value || ''}>
                    {filter.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="filter-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={clinicalOnly}
                  onChange={(e) => setClinicalOnly(e.target.checked)}
                />
                Clinical Focus Only
              </label>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="messages-container">
        {messages.length === 0 && (
          <div className="empty-state">
            <Brain size={48} className="empty-icon" />
            <h3>Start a conversation</h3>
            <p>Ask any question about neuroanatomy and get detailed, educational answers.</p>
            <div className="example-questions">
              <p className="examples-label">Example questions:</p>
              <button
                className="example-btn"
                onClick={() => setInput("What is the function of the hippocampus?")}
              >
                What is the function of the hippocampus?
              </button>
              <button
                className="example-btn"
                onClick={() => setInput("Explain the blood supply to the brain")}
              >
                Explain the blood supply to the brain
              </button>
              <button
                className="example-btn"
                onClick={() => setInput("Describe the cranial nerves")}
              >
                Describe the cranial nerves
              </button>
            </div>
          </div>
        )}

        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className={`message ${message.type}`}
            >
              <div className="message-content">
                {message.type === 'bot' && (
                  <div className="message-meta">
                    <span className="confidence">
                      Confidence: {Math.round(message.confidence * 100)}%
                    </span>
                    {message.sources && message.sources.length > 0 && (
                      <span className="sources">
                        {message.sources.length} source{message.sources.length !== 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                )}
                <div className="message-text">
                  <FormattedContent content={message.content} />
                </div>
                {message.sources && message.sources.length > 0 && (
                  <details className="sources-details" open>
                    <summary>Sources ({message.sources.length})</summary>
                    <div className="sources-list">
                      {message.sources.map((source, idx) => (
                        <div key={idx} className="source-item">
                          <div className="source-preview">
                            {source.preview || source.content?.substring?.(0, 250) || '—'}
                          </div>
                          <div className="source-meta">
                            {source.source && <span>Document: {source.source}</span>}
                            {source.structure_name && source.structure_name !== 'Unknown' && (
                              <span>Structure: {source.structure_name}</span>
                            )}
                            {typeof source.score === 'number' && (
                              <span>Relevance: {Math.round(source.score * 100)}%</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="message bot loading"
          >
            <Loader2 className="spinner" />
            <span>Thinking...</span>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        {attachedFiles.length > 0 && (
          <div className="attached-files">
            {attachedFiles.map((f, idx) => (
              <span key={idx} className="attached-file">
                {f.name}
                <button type="button" onClick={() => removeFile(idx)} className="remove-file-btn">
                  <X size={14} />
                </button>
              </span>
            ))}
          </div>
        )}
        <div className="input-wrapper">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.pptx,.ppt,.html,.htm,.txt"
            onChange={handleFileAttach}
            style={{ display: 'none' }}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="attach-button"
            title="Attach PDF, PPTX, or document"
          >
            <Paperclip size={20} />
          </button>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question or attach PDF/PPTX to analyze..."
            className="message-input"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={(!input.trim() && attachedFiles.length === 0) || loading}
            className="send-button"
          >
            {loading ? (
              <Loader2 className="spinner" />
            ) : (
              <Send size={20} />
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

export default Query

