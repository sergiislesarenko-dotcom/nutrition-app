import { useState } from 'react'
import { useAiChat } from '../../hooks/useAiChat'
import ChatMessage from './ChatMessage'
import StreamingIndicator from './StreamingIndicator'

export default function ChatWindow() {
  const [input, setInput] = useState('')
  const { answer, isStreaming, error, sendMessage } = useAiChat()

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim() || isStreaming) return
    sendMessage(input.trim())
    setInput('')
  }

  return (
    <div className="bg-white rounded-xl shadow flex flex-col h-[500px]">
      <div className="px-5 py-4 border-b">
        <h2 className="text-lg font-semibold">AI Nutrition Coach</h2>
      </div>
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
        {answer && <ChatMessage text={answer} />}
        {isStreaming && <StreamingIndicator />}
        {error && <p className="text-red-500 text-sm">{error}</p>}
        {!answer && !isStreaming && (
          <p className="text-gray-400 text-sm">Ask anything about your nutrition goals…</p>
        )}
      </div>
      <form onSubmit={handleSubmit} className="px-5 py-4 border-t flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask the AI coach…"
          disabled={isStreaming}
          className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
        <button type="submit" disabled={isStreaming || !input.trim()}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm">
          Send
        </button>
      </form>
    </div>
  )
}
