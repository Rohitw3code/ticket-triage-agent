import { useState, useRef, useEffect } from 'react'
import './App.css'

interface StreamEvent {
  type: string
  message?: string
  node?: string
  data?: any
  content?: string
  tool?: string
  args?: any
}

function App() {
  const [query, setQuery] = useState('')
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const streamEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    streamEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [streamEvents])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!query.trim()) return

    setStreamEvents([])
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/triage/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ description: query }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No reader available')
      }

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n').filter(line => line.trim())
        
        lines.forEach(line => {
          try {
            const event = JSON.parse(line) as StreamEvent
            setStreamEvents(prev => [...prev, event])
          } catch (e) {
            console.error('Failed to parse event:', line)
          }
        })
      }
    } catch (error) {
      console.error('Error:', error)
      setStreamEvents(prev => [...prev, { type: 'error', message: String(error) }])
    } finally {
      setIsLoading(false)
    }
  }

  const clearStream = () => {
    setStreamEvents([])
    setQuery('')
  }

  const renderEvent = (event: StreamEvent, index: number) => {
    switch (event.type) {
      case 'status':
        return (
          <div key={index} className="event-card status-card">
            <div className="event-icon">ℹ️</div>
            <div className="event-content">
              <div className="event-type">Status</div>
              <div className="event-message">{event.message}</div>
            </div>
          </div>
        )

      case 'node_start':
        return (
          <div key={index} className="event-card node-start-card">
            <div className="event-icon">▶️</div>
            <div className="event-content">
              <div className="event-type">Node Started</div>
              <div className="event-message">
                <strong>{event.node}</strong>
              </div>
            </div>
          </div>
        )

      case 'node_complete':
        return (
          <div key={index} className="event-card node-complete-card">
            <div className="event-icon">✅</div>
            <div className="event-content">
              <div className="event-type">Node Complete</div>
              <div className="event-message">
                <strong>{event.node}</strong>
              </div>
            </div>
          </div>
        )

      case 'kb_search_complete':
        return (
          <div key={index} className="event-card kb-card">
            <div className="event-icon">🔍</div>
            <div className="event-content">
              <div className="event-type">Knowledge Base Results</div>
              <pre className="event-data">{event.data}</pre>
            </div>
          </div>
        )

      case 'classification_complete':
        return (
          <div key={index} className="event-card classification-card">
            <div className="event-icon">📋</div>
            <div className="event-content">
              <div className="event-type">Classification</div>
              <div className="classification-grid">
                <div className="classification-item">
                  <span className="label">Summary:</span>
                  <span className="value">{event.data?.summary}</span>
                </div>
                <div className="classification-item">
                  <span className="label">Category:</span>
                  <span className="badge badge-category">{event.data?.category}</span>
                </div>
                <div className="classification-item">
                  <span className="label">Severity:</span>
                  <span className={`badge badge-severity badge-${event.data?.severity?.toLowerCase()}`}>
                    {event.data?.severity}
                  </span>
                </div>
                <div className="classification-item">
                  <span className="label">Issue Type:</span>
                  <span className="badge">{event.data?.issue_type}</span>
                </div>
                <div className="classification-item full-width">
                  <span className="label">Next Action:</span>
                  <span className="value">{event.data?.next_action}</span>
                </div>
              </div>
            </div>
          </div>
        )

      case 'tool_call':
        return (
          <div key={index} className="event-card tool-card">
            <div className="event-icon">🔧</div>
            <div className="event-content">
              <div className="event-type">Tool Call</div>
              <div className="tool-info">
                <div className="tool-name">{event.tool}</div>
                <details className="tool-args">
                  <summary>Arguments</summary>
                  <pre>{JSON.stringify(event.args, null, 2)}</pre>
                </details>
              </div>
            </div>
          </div>
        )

      case 'message':
        return (
          <div key={index} className="event-card message-card">
            <div className="event-icon">💬</div>
            <div className="event-content">
              <div className="event-type">Message</div>
              <pre className="event-data">{event.content}</pre>
            </div>
          </div>
        )

      case 'error':
        return (
          <div key={index} className="event-card error-card">
            <div className="event-icon">❌</div>
            <div className="event-content">
              <div className="event-type">Error</div>
              <div className="event-message">{event.message}</div>
            </div>
          </div>
        )

      default:
        return (
          <div key={index} className="event-card default-card">
            <div className="event-icon">📄</div>
            <div className="event-content">
              <div className="event-type">{event.type}</div>
              <pre className="event-data">{JSON.stringify(event, null, 2)}</pre>
            </div>
          </div>
        )
    }
  }

  return (
    <div className="app-container">
      <div className="content-wrapper">
        <header className="header">
          <h1>🎫 Ticket Triage Agent</h1>
          <p className="subtitle">AI-powered ticket classification and routing</p>
        </header>
        
        <form onSubmit={handleSubmit} className="query-form">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Describe your issue here... (e.g., 'Getting error 500 on mobile checkout')"
            rows={4}
            disabled={isLoading}
          />
          <div className="button-group">
            <button type="submit" className="btn-primary" disabled={isLoading || !query.trim()}>
              {isLoading ? '⏳ Processing...' : '🚀 Submit Query'}
            </button>
            <button type="button" className="btn-secondary" onClick={clearStream} disabled={isLoading}>
              🗑️ Clear
            </button>
          </div>
        </form>

        {streamEvents.length > 0 && (
          <div className="results-container">
            <div className="results-header">
              <h2>Results</h2>
              <span className="event-count">{streamEvents.length} events</span>
            </div>
            <div className="stream-output">
              {streamEvents.map((event, index) => renderEvent(event, index))}
              <div ref={streamEndRef} />
            </div>
          </div>
        )}

        {streamEvents.length === 0 && !isLoading && (
          <div className="empty-state">
            <div className="empty-icon">📝</div>
            <h3>No results yet</h3>
            <p>Submit a ticket description above to see the AI triage process in action</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
