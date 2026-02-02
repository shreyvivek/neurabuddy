import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Layers, ChevronLeft, ChevronRight, Loader2, RotateCcw, Send, CheckCircle2, XCircle, Trophy, TrendingUp } from 'lucide-react'
import { api } from '../api/client'
import { useApp } from '../context/AppContext'
import FormattedContent from './FormattedContent'
import './FlashCards.css'

const DIFFICULTY_LEVELS = [
  { value: 'undergrad', label: 'Undergraduate' },
  { value: 'med', label: 'Medical School' },
  { value: 'advanced', label: 'Advanced' },
]

function FlashCards() {
  const { flashCardsData, setFlashCardsData } = useApp()
  const [topic, setTopic] = useState(flashCardsData?.topic ?? '')
  const [numCards, setNumCards] = useState(10)
  const [difficulty, setDifficulty] = useState('undergrad')
  const [cards, setCards] = useState(flashCardsData?.cards ?? [])
  const [currentIndex, setCurrentIndex] = useState(flashCardsData?.currentIndex ?? 0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Interactive mode state
  const [userAnswer, setUserAnswer] = useState('')
  const [showAnswer, setShowAnswer] = useState(false)
  const [evaluation, setEvaluation] = useState(null)
  const [evaluating, setEvaluating] = useState(false)
  const [cardResults, setCardResults] = useState([])
  const [totalScore, setTotalScore] = useState(0)
  const [sessionComplete, setSessionComplete] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)

  useEffect(() => {
    if (cards.length > 0 && !sessionComplete) {
      setFlashCardsData({ cards, topic, currentIndex })
    }
  }, [cards.length, topic, currentIndex, sessionComplete])

  const generate = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.generateFlashCards({
        topic: topic.trim() || undefined,
        num_cards: numCards,
        difficulty_level: difficulty
      })
      const newCards = res.flash_cards || []
      setCards(newCards)
      setCurrentIndex(0)
      setUserAnswer('')
      setShowAnswer(false)
      setEvaluation(null)
      setCardResults([])
      setTotalScore(0)
      setSessionComplete(false)
      setAnalysis(null)
      setFlashCardsData({ cards: newCards, topic: res.topic || topic, currentIndex: 0 })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate flash cards')
      setCards([])
    } finally {
      setLoading(false)
    }
  }

  const submitAnswer = async () => {
    if (!userAnswer.trim() || evaluating) return
    
    setEvaluating(true)
    try {
      const currentCard = cards[currentIndex]
      const result = await api.evaluateFlashCardAnswer({
        user_answer: userAnswer.trim(),
        correct_answer: currentCard.back,
        question: currentCard.front
      })
      
      setEvaluation(result)
      setShowAnswer(true)
      setTotalScore(prev => prev + result.score)
      
      // Store result for analysis
      setCardResults(prev => [...prev, {
        question: currentCard.front,
        user_answer: userAnswer.trim(),
        correct_answer: currentCard.back,
        score: result.score,
        feedback: result.feedback
      }])
    } catch (err) {
      setError('Failed to evaluate answer')
    } finally {
      setEvaluating(false)
    }
  }

  const nextCard = () => {
    if (currentIndex < cards.length - 1) {
      goToCard(currentIndex + 1)
    } else {
      // Session complete - analyze performance
      setSessionComplete(true)
      analyzeSession()
    }
  }

  const prevCard = () => {
    if (currentIndex > 0) {
      goToCard(currentIndex - 1)
    }
  }

  const goToCard = (idx) => {
    setCurrentIndex(idx)
    const prevResult = cardResults[idx]
    if (prevResult) {
      setUserAnswer(prevResult.user_answer)
      setShowAnswer(true)
      setEvaluation({
        score: prevResult.score,
        feedback: prevResult.feedback,
        is_correct: prevResult.score >= 1.0,
        is_partial: prevResult.score > 0 && prevResult.score < 1.0
      })
    } else {
      setUserAnswer('')
      setShowAnswer(false)
      setEvaluation(null)
    }
  }

  const startOver = () => {
    startNewSession()
  }

  const analyzeSession = async () => {
    setAnalyzing(true)
    try {
      const result = await api.analyzeFlashCardSession({
        topic: topic || 'neuroanatomy',
        total_score: totalScore,
        max_score: cards.length,
        card_results: cardResults
      })
      setAnalysis(result)
    } catch (err) {
      setError('Failed to analyze session')
    } finally {
      setAnalyzing(false)
    }
  }

  const startNewSession = (recommendedTopic = null) => {
    if (recommendedTopic) {
      setTopic(recommendedTopic)
    }
    setCards([])
    setCurrentIndex(0)
    setUserAnswer('')
    setShowAnswer(false)
    setEvaluation(null)
    setCardResults([])
    setTotalScore(0)
    setSessionComplete(false)
    setAnalysis(null)
    setFlashCardsData(null)
  }

  const currentCard = cards[currentIndex]
  const progressPct = cards.length > 0 ? ((currentIndex + 1) / cards.length) * 100 : 0

  return (
    <div className="flashcards-container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flashcards-header"
      >
        <Layers className="header-icon" />
        <div>
          <h2>Interactive Flash Cards</h2>
          <p>Test yourself and get AI-powered feedback</p>
        </div>
      </motion.div>

      {!cards.length && !sessionComplete && (
        <div className="flashcards-setup">
          <div className="setup-row">
            <div className="form-group">
              <label>Topic (optional)</label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="e.g., cranial nerves, hippocampus"
                className="form-input"
              />
            </div>
            <div className="form-group">
              <label>Number of Cards</label>
              <input
                type="number"
                min={3}
                max={30}
                value={numCards}
                onChange={(e) => setNumCards(parseInt(e.target.value) || 10)}
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
          <button onClick={generate} disabled={loading} className="generate-btn">
            {loading ? <><Loader2 className="spinner" /> Generating...</> : <>Start Flash Cards</>}
          </button>
        </div>
      )}

      {error && <div className="error-msg">{error}</div>}

      {sessionComplete && analysis && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="session-complete"
        >
          <div className="completion-header">
            <Trophy className="trophy-icon" />
            <h3>Session Complete!</h3>
          </div>
          
          <div className="score-summary">
            <div className="final-score">
              <span className="score-label">Final Score</span>
              <span className="score-value">{totalScore.toFixed(1)} / {cards.length}</span>
              <span className="score-percentage">{((totalScore / cards.length) * 100).toFixed(0)}%</span>
            </div>
          </div>

          <div className="analysis-section">
            <h4><TrendingUp size={20} /> Performance Analysis</h4>
            <div className="analysis-content">
              <FormattedContent content={analysis.performance_summary} />
            </div>
          </div>

          {analysis.strengths && analysis.strengths.length > 0 && (
            <div className="analysis-section strengths">
              <h4><CheckCircle2 size={18} /> Strengths</h4>
              <ul>
                {analysis.strengths.map((s, i) => (
                  <li key={i}><FormattedContent content={s} /></li>
                ))}
              </ul>
            </div>
          )}

          {analysis.areas_to_improve && analysis.areas_to_improve.length > 0 && (
            <div className="analysis-section improvements">
              <h4><XCircle size={18} /> Areas to Improve</h4>
              <ul>
                {analysis.areas_to_improve.map((a, i) => (
                  <li key={i}><FormattedContent content={a} /></li>
                ))}
              </ul>
            </div>
          )}

          {analysis.recommended_topics && analysis.recommended_topics.length > 0 && (
            <div className="analysis-section recommendations">
              <h4>📚 Recommended Next Topics</h4>
              <div className="topic-chips">
                {analysis.recommended_topics.map((t, i) => (
                  <button
                    key={i}
                    onClick={() => startNewSession(t)}
                    className="topic-chip"
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>
          )}

          <button onClick={() => startNewSession()} className="new-session-btn">
            Start New Session
          </button>
        </motion.div>
      )}

      <AnimatePresence>
        {cards.length > 0 && !sessionComplete && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flashcards-viewer"
          >
            <div className="progress-bar-container">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progressPct}%` }} />
              </div>
              <div className="progress-nav">
                <div className="progress-text">
                  Card {currentIndex + 1} / {cards.length} • Score: {totalScore.toFixed(1)} / {currentIndex + (showAnswer ? 1 : 0)}
                </div>
                <div className="card-nav-buttons">
                  <button
                    onClick={startOver}
                    className="nav-btn start-over-btn"
                    title="Start over from the beginning"
                  >
                    <RotateCcw size={18} />
                    Start Over
                  </button>
                  <button
                    onClick={prevCard}
                    disabled={currentIndex === 0}
                    className="nav-btn prev-btn"
                    title="Previous card"
                  >
                    <ChevronLeft size={20} />
                    Previous
                  </button>
                </div>
              </div>
            </div>

            <motion.div
              key={currentIndex}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="interactive-card"
            >
              <div className="card-question">
                <p className="question-label">Question</p>
                <div className="question-text">
                  <FormattedContent content={currentCard?.front} />
                </div>
              </div>

              {!showAnswer && (
                <div className="answer-input-section">
                  <label>Your Answer</label>
                  <textarea
                    value={userAnswer}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    placeholder="Type your answer here..."
                    className="answer-input"
                    rows={4}
                    disabled={evaluating}
                  />
                  <button
                    onClick={submitAnswer}
                    disabled={!userAnswer.trim() || evaluating}
                    className="submit-answer-btn"
                  >
                    {evaluating ? (
                      <><Loader2 className="spinner" /> Evaluating...</>
                    ) : (
                      <><Send size={18} /> Submit Answer</>
                    )}
                  </button>
                </div>
              )}

              {showAnswer && evaluation && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="answer-reveal"
                >
                  <div className={`score-badge ${evaluation.is_correct ? 'correct' : evaluation.is_partial ? 'partial' : 'incorrect'}`}>
                    {evaluation.is_correct && <CheckCircle2 size={20} />}
                    {!evaluation.is_correct && <XCircle size={20} />}
                    <span>{evaluation.score.toFixed(1)} / 1.0</span>
                  </div>

                  <div className="feedback-box">
                    <FormattedContent content={evaluation.feedback} />
                  </div>

                  <div className="answer-comparison">
                    <div className="user-answer-display">
                      <strong>Your Answer:</strong>
                      <div className="answer-content"><FormattedContent content={userAnswer} /></div>
                    </div>
                    <div className="correct-answer-display">
                      <strong>Correct Answer:</strong>
                      <div className="answer-content"><FormattedContent content={currentCard?.back} /></div>
                    </div>
                  </div>

                  <button onClick={nextCard} className="next-card-btn">
                    {currentIndex < cards.length - 1 ? (
                      <>Next Card <ChevronRight size={20} /></>
                    ) : (
                      <>Complete Session <Trophy size={20} /></>
                    )}
                  </button>
                </motion.div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {analyzing && (
        <div className="analyzing-overlay">
          <Loader2 className="spinner large" />
          <p>Analyzing your performance...</p>
        </div>
      )}
    </div>
  )
}

export default FlashCards
