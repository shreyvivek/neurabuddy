import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Stethoscope, Send, Lightbulb, Activity, AlertCircle, CheckCircle2, XCircle, Loader2, Trophy, Play } from 'lucide-react'
import { api } from '../api/client'
import FormattedContent from './FormattedContent'
import './ClinicalCase.css'

const DIFFICULTY_LEVELS = [
  { value: 'undergrad', label: 'Undergraduate' },
  { value: 'med', label: 'Medical School' },
  { value: 'advanced', label: 'Advanced/Resident' },
]

function ClinicalCase() {
  const [topic, setTopic] = useState('')
  const [difficulty, setDifficulty] = useState('med')
  const [session, setSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState(null)
  const [availableHints, setAvailableHints] = useState(3)
  const [showingHint, setShowingHint] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const startSession = async () => {
    if (!topic.trim() && difficulty === 'med') {
      // Allow starting without topic
    }
    setStarting(true)
    setError(null)
    try {
      const res = await api.startClinicalSession({
        topic: topic.trim() || undefined,
        difficulty_level: difficulty
      })
      
      setSession(res)
      setAvailableHints(res.available_hints || 3)
      setMessages([
        {
          id: 1,
          type: 'system',
          content: res.scenario_context,
          timestamp: new Date()
        },
        {
          id: 2,
          type: 'presentation',
          content: res.initial_presentation,
          patient: res.patient_name,
          timestamp: new Date()
        }
      ])
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start clinical session')
    } finally {
      setStarting(false)
    }
  }

  const sendMessage = async (requestHint = false) => {
    if ((!input.trim() && !requestHint) || loading) return
    
    const userMessage = input.trim()
    if (!requestHint) {
      setMessages(prev => [...prev, {
        id: Date.now(),
        type: 'student',
        content: userMessage,
        timestamp: new Date()
      }])
      setInput('')
    }
    
    setLoading(true)
    setShowingHint(requestHint)
    
    try {
      const res = await api.interactClinicalSession({
        session_id: session.session_id,
        user_message: userMessage || '(requested hint)',
        request_hint: requestHint
      })
      
      const aiMessage = {
        id: Date.now() + 1,
        type: requestHint ? 'hint' : 'response',
        content: res.ai_response,
        timestamp: new Date(),
        ...res
      }
      
      setMessages(prev => [...prev, aiMessage])
      setAvailableHints(res.available_hints)
      setSession(prev => prev ? { ...prev, stage: res.stage } : prev)
      
      // Update session stage
      if (res.session_complete && res.completion_data) {
        setMessages(prev => [...prev, {
          id: Date.now() + 2,
          type: 'completion',
          content: res.completion_data,
          timestamp: new Date()
        }])
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process message')
    } finally {
      setLoading(false)
      setShowingHint(false)
    }
  }

  const resetSession = () => {
    setSession(null)
    setMessages([])
    setInput('')
    setAvailableHints(3)
    setError(null)
  }

  const getStageLabel = (stage) => {
    const labels = {
      'initial': 'Initial Assessment',
      'gathering_info': 'Information Gathering',
      'diagnosis': 'Clinical Decision',
      'complete': 'Case Complete'
    }
    return labels[stage] || stage
  }

  return (
    <div className="clinical-container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="clinical-header"
      >
        <Stethoscope className="header-icon" />
        <div>
          <h2>Clinical Simulation</h2>
          <p>Experience real-world clinical scenarios in an immersive OR environment</p>
        </div>
      </motion.div>

      {!session ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="clinical-setup"
        >
          <div className="setup-card">
            <h3>Start Clinical Simulation</h3>
            <p className="setup-description">
              You will be placed in a realistic clinical scenario. Ask questions, gather information,
              and make decisions as if you're in the OR.
            </p>
            <div className="setup-fields">
              <div className="form-group">
                <label>Topic (optional)</label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g., stroke, cranial nerve palsy, spinal trauma"
                  className="form-input"
                />
              </div>
              <div className="form-group">
                <label>Difficulty</label>
                <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className="form-select">
                  {DIFFICULTY_LEVELS.map(l => (
                    <option key={l.value} value={l.value}>{l.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <button onClick={startSession} disabled={starting} className="start-simulation-btn">
              {starting ? <><Loader2 className="spinner" /> Preparing OR...</> : <><Play size={20} /> Enter OR</>}
            </button>
          </div>
          {error && <div className="error-msg">{error}</div>}
        </motion.div>
      ) : (
        <div className="or-environment">
          <div className="or-header">
            <div className="patient-info">
              <Activity className="activity-icon pulse" />
              <div>
                <span className="patient-label">Patient</span>
                <span className="patient-name">{session.patient_name}</span>
              </div>
            </div>
            <div className="stage-indicator">
              <span className="stage-label">Stage</span>
              <span className="stage-value">{getStageLabel(session.stage)}</span>
            </div>
            <div className="hints-available">
              <Lightbulb size={18} />
              <span>{availableHints} hints left</span>
            </div>
          </div>

          <div className="clinical-conversation">
            <AnimatePresence>
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`clinical-message ${msg.type}`}
                >
                  {msg.type === 'system' && (
                    <div className="system-message">
                      <AlertCircle size={18} />
                      <FormattedContent content={msg.content} />
                    </div>
                  )}

                  {msg.type === 'presentation' && (
                    <div className="presentation-card">
                      <div className="presentation-header">
                        <Activity className="pulse" size={24} />
                        <h3>Patient Presentation</h3>
                      </div>
                      <div className="presentation-content">
                        <FormattedContent content={msg.content} />
                      </div>
                    </div>
                  )}

                  {msg.type === 'student' && (
                    <div className="student-message">
                      <div className="message-bubble">
                        <FormattedContent content={msg.content} />
                      </div>
                    </div>
                  )}

                  {msg.type === 'response' && (
                    <div className="ai-message">
                      <div className="message-bubble">
                        <FormattedContent content={msg.content} />
                        {msg.guidance && (
                          <div className="guidance-box">
                            <strong>Consider:</strong>
                            <FormattedContent content={msg.guidance} />
                          </div>
                        )}
                        {msg.is_correct_path === true && (
                          <div className="feedback-indicator correct">
                            <CheckCircle2 size={16} />
                            <span>Good clinical reasoning</span>
                          </div>
                        )}
                        {msg.is_correct_path === false && (
                          <div className="feedback-indicator incorrect">
                            <XCircle size={16} />
                            <span>Reconsider your approach</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {msg.type === 'hint' && (
                    <div className="hint-message">
                      <Lightbulb size={18} />
                      <div className="hint-content">
                        <FormattedContent content={msg.hint_given} />
                      </div>
                    </div>
                  )}

                  {msg.type === 'completion' && (
                    <motion.div
                      initial={{ scale: 0.9, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="completion-card"
                    >
                      <div className="completion-header">
                        <Trophy className="trophy-icon" />
                        <h3>Case Complete!</h3>
                      </div>
                      
                      <div className="performance-score">
                        <span className="score-label">Clinical Reasoning</span>
                        <span className="score-value">
                          {(msg.content.clinical_reasoning_score * 100).toFixed(0)}%
                        </span>
                      </div>

                      <div className="completion-section">
                        <h4>Performance Summary</h4>
                        <FormattedContent content={msg.content.performance_summary} />
                      </div>

                      {msg.content.correct_decisions && msg.content.correct_decisions.length > 0 && (
                        <div className="completion-section correct">
                          <h4><CheckCircle2 size={18} /> Correct Decisions</h4>
                          <ul>
                            {msg.content.correct_decisions.map((d, i) => (
                              <li key={i}><FormattedContent content={d} /></li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {msg.content.missed_points && msg.content.missed_points.length > 0 && (
                        <div className="completion-section missed">
                          <h4><AlertCircle size={18} /> Learning Opportunities</h4>
                          <ul>
                            {msg.content.missed_points.map((p, i) => (
                              <li key={i}><FormattedContent content={p} /></li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {msg.content.learning_points && msg.content.learning_points.length > 0 && (
                        <div className="completion-section learning">
                          <h4>Key Learning Points</h4>
                          <ul>
                            {msg.content.learning_points.map((p, i) => (
                              <li key={i}><FormattedContent content={p} /></li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {msg.content.recommended_topics && msg.content.recommended_topics.length > 0 && (
                        <div className="completion-section recommendations">
                          <h4>📚 Recommended Cases to Try Next</h4>
                          <div className="topic-chips">
                            {msg.content.recommended_topics.map((t, i) => (
                              <button
                                key={i}
                                onClick={() => {
                                  setTopic(t)
                                  resetSession()
                                }}
                                className="topic-chip"
                              >
                                {t}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      <button onClick={resetSession} className="new-case-btn">
                        Start New Case
                      </button>
                    </motion.div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="loading-indicator"
              >
                <Loader2 className="spinner" />
                <span>{showingHint ? 'Getting hint...' : 'Analyzing...'}</span>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="or-controls">
            <button
              onClick={() => sendMessage(true)}
              disabled={loading || availableHints === 0}
              className="hint-btn"
              title={availableHints === 0 ? 'No hints remaining' : 'Get a hint'}
            >
              <Lightbulb size={18} />
              <span>Hint ({availableHints})</span>
            </button>

            <form onSubmit={(e) => { e.preventDefault(); sendMessage(false); }} className="input-form">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask questions, request information, or make clinical decisions..."
                className="clinical-input"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="send-btn"
              >
                <Send size={20} />
              </button>
            </form>
          </div>

          {error && <div className="error-msg">{error}</div>}
        </div>
      )}
    </div>
  )
}

export default ClinicalCase
