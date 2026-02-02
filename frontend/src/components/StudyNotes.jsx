import React, { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { FileText, Loader2, Download } from 'lucide-react'
import { api } from '../api/client'
import FormattedContent from './FormattedContent'
import './StudyNotes.css'

const DIFFICULTY_LEVELS = [
  { value: 'undergrad', label: 'Undergraduate' },
  { value: 'med', label: 'Medical School' },
  { value: 'advanced', label: 'Advanced' },
]

function StudyNotes() {
  const [topic, setTopic] = useState('')
  const [difficulty, setDifficulty] = useState('undergrad')
  const [includeSummary, setIncludeSummary] = useState(true)
  const [notes, setNotes] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const printRef = useRef(null)

  const generate = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic')
      return
    }
    setLoading(true)
    setError(null)
    setNotes(null)
    try {
      const res = await api.generateStudyNotes({
        topic: topic.trim(),
        difficulty_level: difficulty,
        include_summary: includeSummary
      })
      setNotes(res)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate study notes')
    } finally {
      setLoading(false)
    }
  }

  const downloadPdf = () => {
    window.print()
  }

  return (
    <div className="studynotes-container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="studynotes-header"
      >
        <FileText className="header-icon" />
        <div>
          <h2>Study Notes</h2>
          <p>Generate structured study notes from your knowledge base</p>
        </div>
      </motion.div>

      <div className="studynotes-setup">
        <div className="setup-fields">
          <div className="form-group wide">
            <label>Topic *</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., cranial nerves, blood supply of the brain"
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
          <div className="form-group checkbox">
            <label>
              <input
                type="checkbox"
                checked={includeSummary}
                onChange={(e) => setIncludeSummary(e.target.checked)}
              />
              Include summary
            </label>
          </div>
        </div>
        <button onClick={generate} disabled={loading || !topic.trim()} className="generate-btn">
          {loading ? <><Loader2 className="spinner" /> Generating...</> : <>Generate Study Notes</>}
        </button>
      </div>

      {error && <div className="error-msg">{error}</div>}

      {notes && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="notes-content"
          ref={printRef}
        >
          <div className="notes-actions">
            <h3>Study Notes: {notes.topic}</h3>
            <button onClick={downloadPdf} className="download-pdf-btn" title="Save as PDF">
              <Download size={20} />
              Download PDF
            </button>
          </div>
          <div className="notes-text markdown-content">
            <FormattedContent content={notes.notes} />
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default StudyNotes
