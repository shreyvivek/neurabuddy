import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { GraduationCap, Send, Loader2, Lightbulb, CheckCircle2 } from 'lucide-react'
import { api } from '../api/client'
import FormattedContent from './FormattedContent'
import './Teaching.css'

const DIFFICULTY_LEVELS = [
  { value: 'undergrad', label: 'Undergraduate' },
  { value: 'med', label: 'Medical School' },
  { value: 'advanced', label: 'Advanced' },
]

function Teaching() {
  const [topic, setTopic] = useState('')
  const [difficulty, setDifficulty] = useState('undergrad')
  const [session, setSession] = useState(null)
  const [qaPairs, setQaPairs] = useState([]) // [{ question, answer }, ...] for Q-A-Q-A display
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [concepts, setConcepts] = useState([])
  const userId = localStorage.getItem('userId') || `user_${Date.now()}`

  useEffect(() => {
    if (!localStorage.getItem('userId')) {
      localStorage.setItem('userId', userId)
    }
  }, [userId])

  const startSession = async () => {
    if (!topic.trim()) return

    setLoading(true)
    try {
      const response = await api.teach({
        topic: topic.trim(),
        user_id: userId,
        difficulty_level: difficulty,
        previous_responses: [],
      })

      setSession({
        topic: topic.trim(),
        difficulty,
        currentQuestion: response.question,
        explanation: response.explanation,
        hint: response.hint,
        isComplete: response.is_complete,
        nextStep: response.next_step,
      })
      setConcepts(response.concepts_covered || [])
      setQaPairs([])
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to start session')
    } finally {
      setLoading(false)
    }
  }

  const submitAnswer = async () => {
    if (!currentAnswer.trim() || !session || loading) return

    const userResponse = currentAnswer.trim()
    const currentQ = session.currentQuestion
    setCurrentAnswer('')
    setLoading(true)

    const updatedResponses = [...qaPairs.map(p => p.answer), userResponse]

    try {
      const response = await api.teach({
        topic: session.topic,
        user_id: userId,
        difficulty_level: session.difficulty,
        previous_responses: updatedResponses,
      })

      // Add this Q-A pair to history for Q-A-Q-A display
      setQaPairs(prev => [...prev, { question: currentQ, answer: userResponse }])

      setSession({
        ...session,
        currentQuestion: response.question,
        explanation: response.explanation,
        hint: response.hint,
        isComplete: response.is_complete,
        nextStep: response.next_step,
      })
      setConcepts(response.concepts_covered || [])
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to process answer')
    } finally {
      setLoading(false)
    }
  }

  const resetSession = () => {
    setSession(null)
    setQaPairs([])
    setCurrentAnswer('')
    setConcepts([])
  }

  return (
    <div className="teaching-container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="teaching-header"
      >
        <GraduationCap className="header-icon" />
        <div>
          <h2>Socratic Learning</h2>
          <p>Learn through guided questions and discovery</p>
        </div>
      </motion.div>

      {!session ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="session-setup"
        >
          <div className="setup-card">
            <h3>Start a Learning Session</h3>
            <p className="setup-description">
              Enter a topic you'd like to learn about. Our Socratic tutor will guide you
              through the concepts with thoughtful questions.
            </p>

            <div className="setup-form">
              <div className="form-group">
                <label>Topic</label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g., hippocampus, cranial nerves, blood-brain barrier"
                  className="topic-input"
                  onKeyPress={(e) => e.key === 'Enter' && startSession()}
                />
              </div>

              <div className="form-group">
                <label>Difficulty Level</label>
                <select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                  className="difficulty-select"
                >
                  {DIFFICULTY_LEVELS.map(level => (
                    <option key={level.value} value={level.value}>
                      {level.label}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={startSession}
                disabled={!topic.trim() || loading}
                className="start-button"
              >
                {loading ? (
                  <>
                    <Loader2 className="spinner" />
                    Starting...
                  </>
                ) : (
                  <>
                    <GraduationCap size={20} />
                    Start Learning
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>
      ) : (
        <div className="session-content">
          <div className="session-info">
            <div className="info-card">
              <h3>{session.topic}</h3>
              <span className="difficulty-badge">{DIFFICULTY_LEVELS.find(d => d.value === session.difficulty)?.label}</span>
            </div>
            {concepts.length > 0 && (
              <div className="concepts-card">
                <h4>Concepts Covered</h4>
                <div className="concepts-list">
                  {concepts.map((concept, idx) => (
                    <span key={idx} className="concept-tag">
                      <CheckCircle2 size={14} />
                      {concept}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="teaching-messages">
            {/* Q-A-Q-A flow: alternate question then answer for each pair */}
            {qaPairs.map((pair, idx) => (
              <React.Fragment key={idx}>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="message question"
                >
                  <div className="message-header">
                    <GraduationCap size={18} />
                    <span>Question</span>
                  </div>
                  <div className="message-content"><FormattedContent content={pair.question} /></div>
                </motion.div>
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="message user-response"
                >
                  <div className="message-header">
                    <span>Your Answer</span>
                  </div>
                  <div className="message-content">{pair.answer}</div>
                </motion.div>
              </React.Fragment>
            ))}

            {/* Optional explanation before current question (e.g. feedback on last answer) */}
            {session.explanation && !session.isComplete && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="message explanation"
              >
                <div className="message-header">
                  <Lightbulb size={18} />
                  <span>Explanation</span>
                </div>
                <div className="message-content"><FormattedContent content={session.explanation} /></div>
              </motion.div>
            )}

            {/* Current question (awaiting answer) */}
            {session.currentQuestion && !session.isComplete && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="message question"
              >
                <div className="message-header">
                  <GraduationCap size={18} />
                  <span>Question</span>
                </div>
                <div className="message-content"><FormattedContent content={session.currentQuestion} /></div>
                {session.hint && (
                  <details className="hint-details">
                    <summary>Need a hint?</summary>
                    <div className="hint-content"><FormattedContent content={session.hint} /></div>
                  </details>
                )}
              </motion.div>
            )}

            {session.isComplete && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="message completion"
              >
                <CheckCircle2 className="completion-icon" />
                <div>
                  <h4>Great job!</h4>
                  {session.nextStep && <p>{session.nextStep}</p>}
                </div>
              </motion.div>
            )}

            {loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="message loading"
              >
                <Loader2 className="spinner" />
                <span>Processing...</span>
              </motion.div>
            )}
          </div>

          {!session.isComplete && (
            <div className="answer-input">
              <div className="input-wrapper">
                <input
                  type="text"
                  value={currentAnswer}
                  onChange={(e) => setCurrentAnswer(e.target.value)}
                  placeholder="Type your answer..."
                  className="answer-field"
                  onKeyPress={(e) => e.key === 'Enter' && submitAnswer()}
                  disabled={loading}
                />
                <button
                  onClick={submitAnswer}
                  disabled={!currentAnswer.trim() || loading}
                  className="submit-button"
                >
                  {loading ? (
                    <Loader2 className="spinner" />
                  ) : (
                    <Send size={20} />
                  )}
                </button>
              </div>
            </div>
          )}

          <div className="session-actions">
            <button onClick={resetSession} className="reset-button">
              Start New Session
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default Teaching

