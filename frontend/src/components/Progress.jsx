import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { BarChart3, TrendingUp, BookOpen, Target, Loader2, AlertCircle } from 'lucide-react'
import { api } from '../api/client'
import './Progress.css'

function Progress() {
  const [progress, setProgress] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const userId = localStorage.getItem('userId') || `user_${Date.now()}`

  useEffect(() => {
    if (!localStorage.getItem('userId')) {
      localStorage.setItem('userId', userId)
    }
  }, [userId])

  useEffect(() => {
    loadProgress()
  }, [])

  const loadProgress = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await api.getProgress(userId)
      setProgress(response.progress)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load progress')
    } finally {
      setLoading(false)
    }
  }

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'undergrad':
        return 'var(--info)'
      case 'med':
        return 'var(--warning)'
      case 'advanced':
        return 'var(--error)'
      default:
        return 'var(--text-secondary)'
    }
  }

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'var(--success)'
    if (score >= 0.6) return 'var(--warning)'
    return 'var(--error)'
  }

  if (loading) {
    return (
      <div className="progress-container">
        <div className="loading-state">
          <Loader2 className="spinner" />
          <p>Loading your progress...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="progress-container">
        <div className="error-state">
          <AlertCircle className="error-icon" />
          <p>{error}</p>
          <button onClick={loadProgress} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!progress || progress.topics_studied.length === 0) {
    return (
      <div className="progress-container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="progress-header"
        >
          <BarChart3 className="header-icon" />
          <div>
            <h2>Learning Progress</h2>
            <p>Track your learning journey</p>
          </div>
        </motion.div>

        <div className="empty-progress">
          <BookOpen className="empty-icon" />
          <h3>No Progress Yet</h3>
          <p>Start learning by taking quizzes or asking questions to see your progress here.</p>
        </div>
      </div>
    )
  }

  const avgScore = progress.topics_studied.length > 0
    ? Object.values(progress.quiz_scores).reduce((a, b) => a + b, 0) / progress.topics_studied.length
    : 0

  return (
    <div className="progress-container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="progress-header"
      >
        <BarChart3 className="header-icon" />
        <div>
          <h2>Learning Progress</h2>
          <p>Track your learning journey</p>
        </div>
      </motion.div>

      <div className="progress-stats">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="stat-card primary"
        >
          <div className="stat-icon">
            <TrendingUp />
          </div>
          <div className="stat-content">
            <p className="stat-label">Average Score</p>
            <p className="stat-value" style={{ color: getScoreColor(avgScore) }}>
              {Math.round(avgScore * 100)}%
            </p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="stat-card"
        >
          <div className="stat-icon">
            <BookOpen />
          </div>
          <div className="stat-content">
            <p className="stat-label">Topics Studied</p>
            <p className="stat-value">{progress.topics_studied.length}</p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="stat-card"
        >
          <div className="stat-icon">
            <Target />
          </div>
          <div className="stat-content">
            <p className="stat-label">Last Active</p>
            <p className="stat-value">
              {new Date(progress.last_active).toLocaleDateString()}
            </p>
          </div>
        </motion.div>
      </div>

      <div className="topics-section">
        <h3>Topics Studied</h3>
        {progress.topics_studied.length > 0 ? (
          <div className="topics-list">
            {progress.topics_studied.map((topic, idx) => {
              const score = progress.quiz_scores[topic] || 0
              const difficulty = progress.difficulty_progression[topic] || 'undergrad'
              
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  className="topic-card"
                >
                  <div className="topic-header">
                    <h4 className="topic-name">{topic}</h4>
                    <span
                      className="difficulty-badge"
                      style={{ background: getDifficultyColor(difficulty) + '20', color: getDifficultyColor(difficulty) }}
                    >
                      {difficulty}
                    </span>
                  </div>
                  <div className="topic-stats">
                    <div className="score-section">
                      <span className="score-label">Quiz Score</span>
                      <div className="score-bar-container">
                        <div
                          className="score-bar"
                          style={{
                            width: `${score * 100}%`,
                            background: getScoreColor(score)
                          }}
                        />
                      </div>
                      <span className="score-value" style={{ color: getScoreColor(score) }}>
                        {Math.round(score * 100)}%
                      </span>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        ) : (
          <p className="no-topics">No topics studied yet.</p>
        )}
      </div>

      {progress.misconceptions_identified && progress.misconceptions_identified.length > 0 && (
        <div className="misconceptions-section">
          <h3>Areas to Review</h3>
          <div className="misconceptions-list">
            {progress.misconceptions_identified.map((misconception, idx) => (
              <div key={idx} className="misconception-item">
                {misconception}
              </div>
            ))}
          </div>
        </div>
      )}

      {progress.strengths && progress.strengths.length > 0 && (
        <div className="strengths-section">
          <h3>Strengths</h3>
          <div className="strengths-list">
            {progress.strengths.map((strength, idx) => (
              <div key={idx} className="strength-item">
                {strength}
              </div>
            ))}
          </div>
        </div>
      )}

      {progress.areas_for_improvement && progress.areas_for_improvement.length > 0 && (
        <div className="improvement-section">
          <h3>Areas for Improvement</h3>
          <div className="improvement-list">
            {progress.areas_for_improvement.map((area, idx) => (
              <div key={idx} className="improvement-item">
                {area}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Progress

