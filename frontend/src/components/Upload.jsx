import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Upload as UploadIcon, FileText, CheckCircle2, Loader2, X, AlertCircle } from 'lucide-react'
import { api } from '../api/client'
import './Upload.css'

function Upload() {
  const [file, setFile] = useState(null)
  const [source, setSource] = useState('uploaded_file')
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (selectedFile) => {
    const validTypes = ['.pdf', '.pptx', '.ppt', '.html', '.htm', '.txt']
    const fileExtension = '.' + selectedFile.name.split('.').pop().toLowerCase()
    
    if (!validTypes.includes(fileExtension)) {
      setError('Please upload a PDF, PPTX, HTML, or text file')
      setFile(null)
      return
    }

    setFile(selectedFile)
    setError(null)
    setResult(null)
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setError(null)
    setResult(null)

    try {
      const response = await api.uploadFile(file, source)
      setResult(response)
      setFile(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload file. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const reset = () => {
    setFile(null)
    setResult(null)
    setError(null)
  }

  return (
    <div className="upload-container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="upload-header"
      >
        <UploadIcon className="header-icon" />
        <div>
          <h2>Upload Documents</h2>
          <p>Add PDF, PPTX, HTML, or text files to the knowledge base</p>
        </div>
      </motion.div>

      <div className="upload-content">
        {!result ? (
          <>
            <div
              className={`upload-area ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                type="file"
                id="file-input"
                accept=".pdf,.pptx,.ppt,.html,.htm,.txt"
                onChange={handleFileSelect}
                className="file-input"
                disabled={uploading}
              />
              
              {!file ? (
                <label htmlFor="file-input" className="upload-label">
                  <UploadIcon className="upload-icon" />
                  <div>
                    <p className="upload-text">
                      <strong>Click to upload</strong> or drag and drop
                    </p>
                    <p className="upload-hint">
                      PDF, PPTX, HTML, or TXT files
                    </p>
                  </div>
                </label>
              ) : (
                <div className="file-preview">
                  <FileText className="file-icon" />
                  <div className="file-info">
                    <p className="file-name">{file.name}</p>
                    <p className="file-size">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  {!uploading && (
                    <button
                      onClick={() => setFile(null)}
                      className="remove-file"
                    >
                      <X size={20} />
                    </button>
                  )}
                </div>
              )}
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="error-message"
              >
                <AlertCircle size={20} />
                <span>{error}</span>
              </motion.div>
            )}

            {file && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="upload-form"
              >
                <div className="form-group">
                  <label>Source Name</label>
                  <input
                    type="text"
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    placeholder="e.g., Neuroscience Online, StatPearls"
                    className="source-input"
                    disabled={uploading}
                  />
                </div>

                <button
                  onClick={handleUpload}
                  disabled={uploading || !file}
                  className="upload-button"
                >
                  {uploading ? (
                    <>
                      <Loader2 className="spinner" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <UploadIcon size={20} />
                      Upload Document
                    </>
                  )}
                </button>
              </motion.div>
            )}
          </>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="success-card"
          >
            <CheckCircle2 className="success-icon" />
            <h3>Upload Successful!</h3>
            <div className="success-details">
              <div className="detail-item">
                <span className="detail-label">Chunks Created:</span>
                <span className="detail-value">{result.chunks_created}</span>
              </div>
              {result.document_id && (
                <div className="detail-item">
                  <span className="detail-label">Document ID:</span>
                  <span className="detail-value">{result.document_id}</span>
                </div>
              )}
            </div>
            <p className="success-message">{result.message}</p>
            <button onClick={reset} className="upload-another-button">
              Upload Another File
            </button>
          </motion.div>
        )}
      </div>

      <div className="upload-info">
        <h4>Supported Formats</h4>
        <ul>
          <li><strong>PDF</strong> - Portable Document Format files</li>
          <li><strong>PPTX</strong> - PowerPoint presentations</li>
          <li><strong>HTML</strong> - Web pages and HTML documents</li>
          <li><strong>TXT</strong> - Plain text files</li>
        </ul>
        <p className="info-note">
          Documents will be processed and added to the knowledge base for use in queries, 
          teaching sessions, and quizzes.
        </p>
      </div>
    </div>
  )
}

export default Upload

