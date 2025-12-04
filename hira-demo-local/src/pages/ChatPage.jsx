import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Info, Plus, MessageSquare, Trash2, Menu } from 'lucide-react'
import { chatAPI } from '../services/api'
import { parseMarkdown } from '../utils/markdown'
import '../styles/ChatPage.css'

function ChatPage() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  // Load conversations from localStorage or use default
  const loadConversations = () => {
    try {
      const saved = localStorage.getItem('hira-conversations')
      if (saved) {
        const parsed = JSON.parse(saved)
        // Convert timestamp strings back to Date objects
        return parsed.map(conv => ({
          ...conv,
          timestamp: new Date(conv.timestamp),
          messages: conv.messages.map(msg => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }))
        }))
      }
    } catch (err) {
      console.error('Error loading conversations:', err)
    }
    // Return default conversation if nothing saved
    return [
      {
        id: 'default',
        title: 'New Conversation',
        timestamp: new Date(),
        messages: [
          {
            role: 'assistant',
            content: "Hello! I'm HiRA, your Human Rights Assistant. I'm here to help you apply human rights-based approaches to your work. Ask me anything about the frameworks, policies, and guidelines in my knowledge base.",
            timestamp: new Date(),
          }
        ]
      }
    ]
  }

  const [conversations, setConversations] = useState(loadConversations)
  const [activeConversationId, setActiveConversationId] = useState(() => {
    const saved = localStorage.getItem('hira-active-conversation-id')
    return saved || 'default'
  })
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  // Save conversations to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem('hira-conversations', JSON.stringify(conversations))
    } catch (err) {
      console.error('Error saving conversations:', err)
    }
  }, [conversations])

  // Save active conversation ID
  useEffect(() => {
    localStorage.setItem('hira-active-conversation-id', activeConversationId)
  }, [activeConversationId])

  const activeConversation = conversations.find(c => c.id === activeConversationId)
  const messages = activeConversation?.messages || []

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const createNewConversation = () => {
    const newId = `conv-${Date.now()}`
    const newConv = {
      id: newId,
      title: 'New Conversation',
      timestamp: new Date(),
      messages: [
        {
          role: 'assistant',
          content: "Hello! I'm HiRA, your Human Rights Assistant. How can I help you today?",
          timestamp: new Date(),
        }
      ]
    }
    setConversations(prev => [newConv, ...prev])
    setActiveConversationId(newId)
  }

  const deleteConversation = (convId, e) => {
    e.stopPropagation()
    if (conversations.length === 1) {
      alert("You must have at least one conversation")
      return
    }
    if (confirm("Delete this conversation?")) {
      setConversations(prev => prev.filter(c => c.id !== convId))
      if (activeConversationId === convId) {
        setActiveConversationId(conversations.find(c => c.id !== convId)?.id || 'default')
      }
    }
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')

    // Add user message to active conversation
    const newUserMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
    }

    setConversations(prev => prev.map(conv =>
      conv.id === activeConversationId
        ? { ...conv, messages: [...conv.messages, newUserMessage], timestamp: new Date() }
        : conv
    ))
    setLoading(true)

    try {
      // Call API
      const response = await chatAPI.sendMessage(userMessage, activeConversationId)

      // Add assistant response
      const assistantMessage = {
        role: 'assistant',
        content: response.message,
        sources: response.sources,
        timestamp: new Date(response.timestamp),
      }

      setConversations(prev => prev.map(conv =>
        conv.id === activeConversationId
          ? {
              ...conv,
              messages: [...conv.messages, assistantMessage],
              title: conv.title === 'New Conversation' ? userMessage.substring(0, 30) + '...' : conv.title
            }
          : conv
      ))

    } catch (error) {
      console.error('Error sending message:', error)

      const errorMessage = {
        role: 'assistant',
        content: "I'm sorry, I encountered an error processing your message. Please make sure the backend server is running and try again.",
        timestamp: new Date(),
        error: true,
      }

      setConversations(prev => prev.map(conv =>
        conv.id === activeConversationId
          ? { ...conv, messages: [...conv.messages, errorMessage] }
          : conv
      ))
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-page">
      {/* Sidebar */}
      <div className={`chat-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
        <button className="new-chat-button" onClick={createNewConversation}>
          <Plus size={20} />
          <span>New Chat</span>
        </button>

        <div className="conversations-list">
          {conversations.map(conv => (
            <div
              key={conv.id}
              className={`conversation-item ${conv.id === activeConversationId ? 'active' : ''}`}
              onClick={() => setActiveConversationId(conv.id)}
            >
              <MessageSquare size={16} />
              <div className="conversation-info">
                <div className="conversation-title">{conv.title}</div>
                <div className="conversation-preview">
                  {conv.messages[conv.messages.length - 1]?.content.substring(0, 50)}...
                </div>
              </div>
              <button
                className="conversation-delete"
                onClick={(e) => deleteConversation(conv.id, e)}
                title="Delete conversation"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat */}
      <div className="chat-main">
        <div className="chat-header">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            title={sidebarCollapsed ? 'Show sidebar' : 'Hide sidebar'}
          >
            <Menu size={20} />
          </button>

          <div className="chat-disclaimer">
            <Info size={16} />
            <span>
              HiRA is an AI assistant trained on human rights frameworks. While helpful for guidance,
              it should not replace professional legal, compliance, or expert advice.
            </span>
          </div>
        </div>

        <div className="messages-container">
          {messages.map((message, index) => (
            <div key={index} className={`message message-${message.role}`}>
              <div className="message-content">
                <div className="message-role">{message.role === 'assistant' ? 'HiRA' : 'You'}</div>
                <div
                  className="message-text"
                  dangerouslySetInnerHTML={{ __html: parseMarkdown(message.content) }}
                />
              </div>
            </div>
          ))}

          {loading && (
            <div className="message message-assistant">
              <div className="message-content">
                <div className="message-role">HiRA</div>
                <div className="message-text">
                  <Loader2 size={20} className="spinner" />
                  <span>Thinking...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask HiRA about human rights approaches, policies, frameworks..."
            className="chat-input"
            rows={1}
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="send-button"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatPage
