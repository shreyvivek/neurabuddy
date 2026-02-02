import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { FileText, CheckCircle2, XCircle, Loader2, Play, Trophy, ArrowRight } from 'lucide-react'
import { api } from '../api/client'
import FormattedContent from './FormattedContent'
import './Quiz.css'

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

function Quiz() {
  const [quiz, setQuiz] = useState(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [selectedAnswer, setSelectedAnswer] = useState('')
  const [answers, setAnswers] = useState({})
  const [feedback, setFeedback] = useState(null)
  const [loading, setLoading] = useState(false)
  const [starting, setStarting] = useState(false)
  
  // Quiz setup
  const [topic, setTopic] = useState('')
  const [difficulty, setDifficulty] = useState('undergrad')
  const [systemFilter, setSystemFilter] = useState(null)
  const [numQuestions, setNumQuestions] = useState(5)
  
  const userId = localStorage.getItem('userId') || `user_${Date.now()}`

  useEffect(() => {
    if (!localStorage.getItem('userId')) {
      localStorage.setItem('userId', userId)
    }
  }, [userId])

  const startQuiz = async () => {
    setStarting(true)
    try {
      const response = await api.startQuiz({
        user_id: userId,
        topic: topic.trim() || null,
        difficulty_level: difficulty,
        system_filter: systemFilter,
        num_questions: numQuestions,
      })

      setQuiz(response)
      setCurrentQuestionIndex(0)
      setSelectedAnswer('')
      setAnswers({})
      setFeedback(null)
    } catch (error) {
      const detail = error.response?.data?.detail
      const msg = Array.isArray(detail)
        ? detail.map(d => d.msg || JSON.stringify(d)).join('; ')
        : (typeof detail === 'string' ? detail : detail?.msg) || error.message || 'Failed to start quiz'
      alert(msg)
    } finally {
      setStarting(false)
    }
  }

  const submitAnswer = async () => {
    if (!selectedAnswer.trim() || !quiz || loading) return

    setLoading(true)
    const questionId = quiz.questions[currentQuestionIndex].question_id

    try {
      const response = await api.submitAnswer({
        quiz_id: quiz.quiz_id,
        question_id: questionId,
        answer: selectedAnswer.trim(),
        user_id: userId,
      })

      setAnswers(prev => ({
        ...prev,
        [questionId]: {
          answer: selectedAnswer.trim(),
          feedback: response.feedback,
        },
      }))

      setFeedback(response.feedback)
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to submit answer')
    } finally {
      setLoading(false)
    }
  }

  const nextQuestion = () => {
    if (currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1)
      const nextQuestionId = quiz.questions[currentQuestionIndex + 1].question_id
      setSelectedAnswer(answers[nextQuestionId]?.answer || '')
      setFeedback(answers[nextQuestionId]?.feedback || null)
    }
  }

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1)
      const prevQuestionId = quiz.questions[currentQuestionIndex - 1].question_id
      setSelectedAnswer(answers[prevQuestionId]?.answer || '')
      setFeedback(answers[prevQuestionId]?.feedback || null)
    }
  }

  const resetQuiz = () => {
    setQuiz(null)
    setCurrentQuestionIndex(0)
    setSelectedAnswer('')
    setAnswers({})
    setFeedback(null)
  }

  if (!quiz) {
    return (
      <div className="quiz-container">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="quiz-header"
        >
          <FileText className="header-icon" />
          <div>
            <h2>Quiz Mode</h2>
            <p>Test your knowledge with interactive quizzes</p>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="quiz-setup"
        >
          <div className="setup-card">
            <h3>Create a Quiz</h3>
            <p className="setup-description">
              Customize your quiz by selecting a topic, difficulty level, and number of questions.
            </p>

            <div className="setup-form">
              <div className="form-group">
                <label>Topic (optional)</label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g., hippocampus, cranial nerves"
                  className="form-input"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Difficulty Level</label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="form-select"
                  >
                    {DIFFICULTY_LEVELS.map(level => (
                      <option key={level.value} value={level.value}>
                        {level.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Number of Questions</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(parseInt(e.target.value) || 5)}
                    className="form-input"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>System Filter</label>
                <select
                  value={systemFilter || ''}
                  onChange={(e) => setSystemFilter(e.target.value || null)}
                  className="form-select"
                >
                  {SYSTEM_FILTERS.map(filter => (
                    <option key={filter.value || 'all'} value={filter.value || ''}>
                      {filter.label}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={startQuiz}
                disabled={starting}
                className="start-quiz-button"
              >
                {starting ? (
                  <>
                    <Loader2 className="spinner" />
                    Generating quiz… (may take 1–2 min)
                  </>
                ) : (
                  <>
                    <Play size={20} />
                    Start Quiz
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    )
  }

  const currentQuestion = quiz.questions[currentQuestionIndex]
  const hasAnswered = answers[currentQuestion.question_id]
  const isLastQuestion = currentQuestionIndex === quiz.questions.length - 1
  const allAnswered = Object.keys(answers).length === quiz.questions.length

  // Calculate score
  const correctCount = Object.values(answers).filter(a => a.feedback?.is_correct).length
  const score = quiz.questions.length > 0 ? (correctCount / quiz.questions.length) * 100 : 0

  return (
    <div className="quiz-container">
      <div className="quiz-header">
        <div>
          <h2>{quiz.topic || 'Quiz'}</h2>
          <p>{DIFFICULTY_LEVELS.find(d => d.value === quiz.difficulty_level)?.label} Level</p>
        </div>
        <div className="quiz-stats">
          <div className="stat">
            <span className="stat-label">Score</span>
            <span className="stat-value">{Math.round(score)}%</span>
          </div>
          <div className="stat">
            <span className="stat-label">Progress</span>
            <span className="stat-value">{Object.keys(answers).length}/{quiz.questions.length}</span>
          </div>
        </div>
      </div>

      <div className="quiz-progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${((currentQuestionIndex + 1) / quiz.questions.length) * 100}%` }}
        />
      </div>

      <div className="quiz-content">
        <div className="question-section">
          <div className="question-header">
            <span className="question-number">
              Question {currentQuestionIndex + 1} of {quiz.questions.length}
            </span>
            <span className="question-type">{currentQuestion.question_type.toUpperCase()}</span>
          </div>

          <div className="question-card">
            <div className="question-text"><FormattedContent content={currentQuestion.question} /></div>
            
            {currentQuestion.question_type === 'mcq' && currentQuestion.options && (
              <div className="options-list">
                {currentQuestion.options.map((option, idx) => (
                  <button
                    key={idx}
                    onClick={() => !hasAnswered && setSelectedAnswer(option)}
                    disabled={hasAnswered}
                    className={`option-button ${
                      hasAnswered && option === currentQuestion.correct_answer
                        ? 'correct'
                        : hasAnswered && option === selectedAnswer && !hasAnswered?.feedback?.is_correct
                        ? 'incorrect'
                        : selectedAnswer === option
                        ? 'selected'
                        : ''
                    }`}
                  >
                    <span className="option-letter">{String.fromCharCode(65 + idx)}</span>
                    <span className="option-text">{option}</span>
                    {hasAnswered && option === currentQuestion.correct_answer && (
                      <CheckCircle2 className="option-icon" />
                    )}
                    {hasAnswered && option === selectedAnswer && !hasAnswered?.feedback?.is_correct && (
                      <XCircle className="option-icon incorrect-icon" />
                    )}
                  </button>
                ))}
              </div>
            )}

            {currentQuestion.question_type !== 'mcq' && (
              <div className="answer-input-section">
                <textarea
                  value={selectedAnswer}
                  onChange={(e) => !hasAnswered && setSelectedAnswer(e.target.value)}
                  placeholder="Type your answer here..."
                  className="answer-textarea"
                  disabled={hasAnswered}
                  rows={4}
                />
              </div>
            )}

            {!hasAnswered && (
              <button
                onClick={submitAnswer}
                disabled={!selectedAnswer.trim() || loading}
                className="submit-answer-button"
              >
                {loading ? (
                  <>
                    <Loader2 className="spinner" />
                    Submitting...
                  </>
                ) : (
                  <>
                    Submit Answer
                    <ArrowRight size={18} />
                  </>
                )}
              </button>
            )}
          </div>

          <AnimatePresence>
            {feedback && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={`feedback-card ${feedback.is_correct ? 'correct' : 'incorrect'}`}
              >
                <div className="feedback-header">
                  {feedback.is_correct ? (
                    <>
                      <CheckCircle2 className="feedback-icon" />
                      <span>Correct!</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="feedback-icon" />
                      <span>Incorrect</span>
                    </>
                  )}
                </div>
                <div className="feedback-content">
                  <div className="feedback-text"><FormattedContent content={feedback.feedback} /></div>
                  {feedback.explanation && (
                    <div className="feedback-explanation">
                      <strong>Explanation:</strong> <FormattedContent content={feedback.explanation} />
                    </div>
                  )}
                  {!feedback.is_correct && (
                    <div className="correct-answer">
                      <strong>Correct Answer:</strong> <FormattedContent content={feedback.correct_answer} />
                    </div>
                  )}
                  {feedback.related_anatomy && (
                    <div className="related-anatomy">
                      <strong>Related Anatomy:</strong> <FormattedContent content={feedback.related_anatomy} />
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="quiz-navigation">
          <button
            onClick={previousQuestion}
            disabled={currentQuestionIndex === 0}
            className="nav-button"
          >
            Previous
          </button>
          <div className="question-dots">
            {quiz.questions.map((q, idx) => (
              <button
                key={q.question_id}
                onClick={() => {
                  setCurrentQuestionIndex(idx)
                  setSelectedAnswer(answers[q.question_id]?.answer || '')
                  setFeedback(answers[q.question_id]?.feedback || null)
                }}
                className={`question-dot ${
                  idx === currentQuestionIndex ? 'active' : ''
                } ${
                  answers[q.question_id]?.feedback?.is_correct
                    ? 'answered-correct'
                    : answers[q.question_id]
                    ? 'answered-incorrect'
                    : ''
                }`}
              />
            ))}
          </div>
          {isLastQuestion ? (
            <button
              onClick={resetQuiz}
              className="nav-button primary"
            >
              <Trophy size={18} />
              Finish Quiz
            </button>
          ) : (
            <button
              onClick={nextQuestion}
              disabled={!hasAnswered}
              className="nav-button"
            >
              Next
            </button>
          )}
        </div>

        {allAnswered && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="quiz-completion"
          >
            <Trophy className="completion-icon" />
            <h3>Quiz Complete!</h3>
            <p className="final-score">
              You scored {correctCount} out of {quiz.questions.length} ({Math.round(score)}%)
            </p>
            <button onClick={resetQuiz} className="new-quiz-button">
              Start New Quiz
            </button>
          </motion.div>
        )}
      </div>
    </div>
  )
}

export default Quiz

