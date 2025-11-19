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
  thread_id?: string
  question?: string
}

function App() {
  const [query, setQuery] = useState('')
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isInterrupted, setIsInterrupted] = useState(false)
  const [interruptQuestion, setInterruptQuestion] = useState('')
  const [threadId, setThreadId] = useState('')
  const [additionalDetails, setAdditionalDetails] = useState('')
  const streamEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    streamEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [streamEvents])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!query.trim()) return

    setStreamEvents([])
    setIsLoading(true)
    setIsInterrupted(false)
    setThreadId('')
    setInterruptQuestion('')
    setAdditionalDetails('')

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
            
            // Handle interrupt event
            if (event.type === 'interrupt') {
              setIsInterrupted(true)
              setInterruptQuestion(event.question || '')
              setThreadId(event.thread_id || '')
            }
            
            // Store thread_id from status events
            if (event.type === 'status' && event.thread_id) {
              setThreadId(event.thread_id)
            }
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

  const handleResume = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!additionalDetails.trim() || !threadId) return

    setIsLoading(true)
    setIsInterrupted(false)

    try {
      const response = await fetch('http://localhost:8000/triage/resume', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          thread_id: threadId,
          additional_details: additionalDetails 
        }),
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
      
      setAdditionalDetails('')
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
    setIsInterrupted(false)
    setThreadId('')
    setInterruptQuestion('')
    setAdditionalDetails('')
  }

  const renderEvent = (event: StreamEvent, index: number) => {
    switch (event.type) {
      case 'status':
        // Show a special card for the initial working message
        if (event.message?.includes('working on it') || event.message?.includes('embedding')) {
          return (
            <div key={index} className="event-card working-card">
              <div className="event-icon">🤖</div>
              <div className="event-content">
                <div className="event-type">Agent Working</div>
                <div className="event-message">{event.message}</div>
              </div>
            </div>
          )
        }
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

      case 'interrupt':
        return (
          <div key={index} className="event-card interrupt-card">
            <div className="event-icon">⏸️</div>
            <div className="event-content">
              <div className="event-type">Agent Interrupted</div>
              <div className="interrupt-message">
                <strong>Question from Agent:</strong>
                <p>{event.question}</p>
              </div>
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
      <header className="header">
        <h1>🎫 Ticket Triage Agent</h1>
        <p className="subtitle">AI-powered ticket classification and routing</p>
      </header>

      <div className="main-layout">
        {/* Left Side - Input */}
        <div className="left-panel">
          <div className="panel-header">
            <h2>📝 Your Query</h2>
          </div>
          
          {!isInterrupted ? (
            <form onSubmit={handleSubmit} className="query-form">
              <label htmlFor="query-input">Describe your issue:</label>
              <textarea
                id="query-input"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., 'Getting error 500 on mobile checkout'"
                rows={6}
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
          ) : (
            <form onSubmit={handleResume} className="query-form interrupt-form">
              <div className="interrupt-header">
                <span className="interrupt-icon">⏸️</span>
                <div>
                  <h3>Agent Needs More Information</h3>
                  <p className="interrupt-question">{interruptQuestion}</p>
                </div>
              </div>
              <label htmlFor="details-input">Your response:</label>
              <textarea
                id="details-input"
                value={additionalDetails}
                onChange={(e) => setAdditionalDetails(e.target.value)}
                placeholder="Provide additional details here..."
                rows={6}
                disabled={isLoading}
                autoFocus
              />
              <div className="button-group">
                <button type="submit" className="btn-primary" disabled={isLoading || !additionalDetails.trim()}>
                  {isLoading ? '⏳ Resuming...' : '▶️ Resume with Details'}
                </button>
                <button type="button" className="btn-secondary" onClick={clearStream} disabled={isLoading}>
                  🗑️ Cancel
                </button>
              </div>
            </form>
          )}

          {/* Knowledge Base Display */}
          <div className="kb-display">
            <div className="kb-header">
              <h3>📚 Knowledge Base</h3>
              <span className="kb-count">15 known issues</span>
            </div>
            <div className="kb-list">
              <KnowledgeBaseItem id="ISSUE-101" title="Checkout error 500 on mobile" category="Bug" />
              <KnowledgeBaseItem id="ISSUE-102" title="Login fails with incorrect password error" category="Login" />
              <KnowledgeBaseItem id="ISSUE-103" title="Slow page load times on dashboard" category="Performance" />
              <KnowledgeBaseItem id="ISSUE-104" title="Unable to update billing information" category="Billing" />
              <KnowledgeBaseItem id="ISSUE-105" title="App crashes on iOS 17" category="Bug" />
              <KnowledgeBaseItem id="ISSUE-106" title="How to export data to CSV" category="Question/How-To" />
              <KnowledgeBaseItem id="ISSUE-107" title="Two-factor authentication setup problems" category="Login" />
              <KnowledgeBaseItem id="ISSUE-108" title="Invoice not received after payment" category="Billing" />
              <KnowledgeBaseItem id="ISSUE-109" title="Search results returning irrelevant items" category="Bug" />
              <KnowledgeBaseItem id="ISSUE-110" title="Cannot upload files larger than 10MB" category="Bug" />
              <KnowledgeBaseItem id="ISSUE-111" title="Email notifications not being received" category="Bug" />
              <KnowledgeBaseItem id="ISSUE-112" title="How to integrate with third-party API" category="Question/How-To" />
              <KnowledgeBaseItem id="ISSUE-113" title="Subscription renewal failed" category="Billing" />
              <KnowledgeBaseItem id="ISSUE-114" title="Database timeout errors during peak hours" category="Performance" />
              <KnowledgeBaseItem id="ISSUE-115" title="Password reset link expired" category="Login" />
            </div>
          </div>
        </div>

        {/* Right Side - Stream Output */}
        <div className="right-panel">
          <div className="panel-header">
            <h2>🔄 Live Stream</h2>
            {streamEvents.length > 0 && (
              <span className="event-count">{streamEvents.length} events</span>
            )}
          </div>

          <div className="stream-container">
            {streamEvents.length === 0 && !isLoading ? (
              <div className="empty-state">
                <div className="empty-icon">�</div>
                <h3>Ready to Process</h3>
                <p>Submit a ticket description to see the AI triage process in real-time</p>
              </div>
            ) : (
              <div className="stream-output">
                {streamEvents.map((event, index) => renderEvent(event, index))}
                <div ref={streamEndRef} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// Knowledge Base Item Component
function KnowledgeBaseItem({ id, title, category }: { id: string; title: string; category: string }) {
  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case 'Bug': return 'kb-cat-bug';
      case 'Login': return 'kb-cat-login';
      case 'Performance': return 'kb-cat-performance';
      case 'Billing': return 'kb-cat-billing';
      case 'Question/How-To': return 'kb-cat-question';
      default: return 'kb-cat-default';
    }
  }

  return (
    <div className="kb-item">
      <span className="kb-id">{id}</span>
      <span className="kb-title">{title}</span>
      <span className={`kb-category ${getCategoryColor(category)}`}>{category}</span>
    </div>
  )
}

export default App
