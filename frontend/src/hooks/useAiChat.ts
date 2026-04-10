import { useState } from 'react'
import { createChatStream } from '../services/ai.service'

export function useAiChat() {
  const [answer, setAnswer] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function sendMessage(message: string) {
    setAnswer('')
    setError(null)
    setIsStreaming(true)

    const source = createChatStream(message)

    source.onmessage = (e) => {
      if (e.data === '[DONE]') {
        source.close()
        setIsStreaming(false)
        return
      }
      setAnswer((prev) => prev + e.data)
    }

    source.onerror = () => {
      source.close()
      setIsStreaming(false)
      setError('Connection error. Please try again.')
    }
  }

  return { answer, isStreaming, error, sendMessage }
}
