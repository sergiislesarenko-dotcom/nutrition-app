type ChatMessageProps = {
  text: string
}

export default function ChatMessage({ text }: ChatMessageProps) {
  return (
    <div className="bg-blue-50 rounded-lg px-4 py-3 text-sm text-gray-800 whitespace-pre-wrap">
      {text}
    </div>
  )
}
