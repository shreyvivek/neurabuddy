import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'

const STORAGE_KEYS = {
  chatMessages: 'neurabuddy_chat_messages',
  teachingSession: 'neurabuddy_teaching_session',
  quizState: 'neurabuddy_quiz_state',
  flashCards: 'neurabuddy_flash_cards',
}

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [chatMessages, setChatMessagesState] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.chatMessages)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })

  const [teachingSession, setTeachingSessionState] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.teachingSession)
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })

  const [quizState, setQuizStateState] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.quizState)
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })

  const [flashCardsData, setFlashCardsDataState] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEYS.flashCards)
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })

  const setChatMessages = useCallback((updater) => {
    setChatMessagesState(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      try {
        localStorage.setItem(STORAGE_KEYS.chatMessages, JSON.stringify(next))
      } catch (e) {}
      return next
    })
  }, [])

  const setTeachingSession = useCallback((updater) => {
    setTeachingSessionState(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      try {
        localStorage.setItem(STORAGE_KEYS.teachingSession, JSON.stringify(next ?? null))
      } catch (e) {}
      return next
    })
  }, [])

  const setQuizState = useCallback((updater) => {
    setQuizStateState(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      try {
        localStorage.setItem(STORAGE_KEYS.quizState, JSON.stringify(next ?? null))
      } catch (e) {}
      return next
    })
  }, [])

  const setFlashCardsData = useCallback((updater) => {
    setFlashCardsDataState(prev => {
      const next = typeof updater === 'function' ? updater(prev) : updater
      try {
        localStorage.setItem(STORAGE_KEYS.flashCards, JSON.stringify(next ?? null))
      } catch (e) {}
      return next
    })
  }, [])

  const clearChat = useCallback(() => {
    setChatMessages([])
  }, [setChatMessages])

  return (
    <AppContext.Provider value={{
      chatMessages,
      setChatMessages,
      clearChat,
      teachingSession,
      setTeachingSession,
      quizState,
      setQuizState,
      flashCardsData,
      setFlashCardsData,
    }}>
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}
