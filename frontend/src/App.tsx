import { useState, useRef, useEffect } from 'react'
import './App.css'

function App() {
  const [query, setQuery] = useState('')
  const [streamData, setStreamData] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const streamEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    streamEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [streamData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!query.trim()) return

    setStreamData([])
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
          setStreamData(prev => [...prev, line])
        })
      }
    } catch (error) {
      console.error('Error:', error)
      setStreamData(prev => [...prev, JSON.stringify({ type: 'error', message: String(error) })])
    } finally {
      setIsLoading(false)
    }
  }

  const clearStream = () => {
    setStreamData([])
    setQuery('')
  }

  return (
    <div className="app-container">
      <h1>Ticket Triage Agent</h1>
      
      <form onSubmit={handleSubmit} className="query-form">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your ticket description..."
          rows={4}
          disabled={isLoading}
        />
        <div className="button-group">
          <button type="submit" disabled={isLoading || !query.trim()}>
            {isLoading ? 'Processing...' : 'Submit Query'}
          </button>
          <button type="button" onClick={clearStream} disabled={isLoading}>
            Clear
          </button>
        </div>
      </form>

      <div className="stream-container">
        <h2>Stream Output ({streamData.length} events)</h2>
        <div className="stream-output">
          {streamData.length === 0 ? (
            <div className="empty-state">No data yet. Submit a query to see streaming results.</div>
          ) : (
            streamData.map((data, index) => (
              <div key={index} className="stream-item">
                <span className="stream-index">{index + 1}</span>
                <pre>{data}</pre>
              </div>
            ))
          )}
          <div ref={streamEndRef} />
        </div>
      </div>
    </div>
  )
}

export default App
