import React from 'react'
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Brain, MessageSquare, GraduationCap, FileText, BarChart3, Layers, Stethoscope, BookOpen } from 'lucide-react'
import Query from './components/Query'
import Teaching from './components/Teaching'
import Quiz from './components/Quiz'
import Upload from './components/Upload'
import Progress from './components/Progress'
import FlashCards from './components/FlashCards'
import ClinicalCase from './components/ClinicalCase'
import StudyNotes from './components/StudyNotes'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        <aside className="sidebar">
          <div className="sidebar-header">
            <motion.div
              className="logo"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4 }}
            >
              <Brain className="logo-icon" />
              <span>NeuraBuddy</span>
            </motion.div>
          </div>
          <nav className="sidebar-nav">
            <div className="nav-group">
              <div className="nav-group-label">Learn</div>
              <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <MessageSquare size={20} strokeWidth={1.75} />
                <span>Chat</span>
              </NavLink>
              <NavLink to="/teach" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <GraduationCap size={20} strokeWidth={1.75} />
                <span>Socratic</span>
              </NavLink>
            </div>
            <div className="nav-group">
              <div className="nav-group-label">Practice</div>
              <NavLink to="/quiz" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <FileText size={20} strokeWidth={1.75} />
                <span>Quiz</span>
              </NavLink>
              <NavLink to="/flashcards" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <Layers size={20} strokeWidth={1.75} />
                <span>Flash Cards</span>
              </NavLink>
              <NavLink to="/clinical" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <Stethoscope size={20} strokeWidth={1.75} />
                <span>Clinical</span>
              </NavLink>
              <NavLink to="/notes" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <BookOpen size={20} strokeWidth={1.75} />
                <span>Notes</span>
              </NavLink>
            </div>
            <div className="nav-group">
              <div className="nav-group-label">Data</div>
              <NavLink to="/upload" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <FileText size={20} strokeWidth={1.75} />
                <span>Upload</span>
              </NavLink>
              <NavLink to="/progress" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <BarChart3 size={20} strokeWidth={1.75} />
                <span>Progress</span>
              </NavLink>
            </div>
          </nav>
        </aside>

        <div className="main-wrapper">
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Query />} />
            <Route path="/teach" element={<Teaching />} />
            <Route path="/quiz" element={<Quiz />} />
            <Route path="/flashcards" element={<FlashCards />} />
            <Route path="/clinical" element={<ClinicalCase />} />
            <Route path="/notes" element={<StudyNotes />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/progress" element={<Progress />} />
          </Routes>
        </main>
        </div>
      </div>
    </Router>
  )
}

export default App

