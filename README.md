# 🎫 Ticket Triage Agent

An AI-powered support ticket classification and routing system built with LangGraph, FastAPI, and React. The agent intelligently analyzes support tickets, searches a knowledge base for similar issues, and provides structured classification with recommended next actions.

## ✨ Features

- 🤖 **AI-Powered Classification**: Uses OpenAI GPT models for intelligent ticket analysis
- 🔍 **Knowledge Base Search**: Semantic search across known issues with similarity scoring
- ⏸️ **Human-in-the-Loop**: Interrupts workflow to ask for clarification when needed
- 📊 **Real-time Streaming**: Live streaming of the triage process
- 🎨 **Modern UI**: Clean, responsive interface with two-column layout
- 🔄 **Stateful Workflows**: Resume interrupted workflows with additional context

## 🏗️ Architecture

### Agent Design

The system uses **LangGraph** to orchestrate a multi-step agentic workflow:

```
User Query → Search KB → Analyze → [Interrupt?] → Classify → Result
                ↓                       ↓
         Similarity Search      Need More Info?
                ↓                       ↓
         Top 3 Matches            Ask User → Resume
```

#### **How the LLM is Used:**

1. **Analysis Node**: 
   - LLM evaluates if the ticket has sufficient information
   - Generates specific questions for vague tickets
   - Decision: Proceed or interrupt for more details

2. **Classification Node**:
   - LLM analyzes ticket + KB results + additional context
   - Extracts structured fields (summary, category, severity, issue_type, next_action)
   - Uses tool calling to ensure structured output

#### **Knowledge Base Search:**

- **Vector Similarity**: Uses OpenAI embeddings for semantic search
- **Cosine Similarity**: Compares ticket with known issues
- **Top-K Retrieval**: Returns top 3 most similar issues
- **Threshold-based Decision**: Similarity > 0.5 = known_issue

#### **State Management:**

- **LangGraph Checkpointer**: Stores workflow state with thread_id
- **Memory Persistence**: Enables resume from interruption
- **State Updates**: Additional user details merged into existing state

### Classification Output

Each ticket receives:
- **Summary**: 1-2 line concise description
- **Category**: Billing, Login, Performance, Bug, Question/How-To
- **Severity**: Low, Medium, High, Critical
- **Issue Type**: known_issue or new_issue
- **Next Action**: Specific recommendation (escalate, attach KB article, ask for logs)

## 📋 Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher
- **npm**: 9.x or higher
- **OpenAI API Key**: Required for LLM and embeddings

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Rohitw3code/ticket-triage-agent.git
cd ticket-triage-agent
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
PORT=8000
MAX_DESCRIPTION_LENGTH=5000
KB_PATH=kb/knowledge_base.json
```

#### Start the Backend Server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 3. Frontend Setup

#### Navigate to Frontend Directory

```bash
cd frontend
```

#### Install Dependencies

```bash
npm install
```

#### Start Development Server

```bash
npm run dev
```

The UI will be available at `http://localhost:5173`

## 🔌 API Usage

### Endpoint: `/triage/stream` (POST)

Start a new ticket triage workflow with streaming response.

**Request:**

```bash
curl -X POST http://localhost:8000/triage/stream \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Getting error 500 when trying to checkout on mobile app"
  }'
```

**Response:** (NDJSON stream)

```json
{"type": "status", "message": "🤖 I'm working on it... Please wait a moment while I embed the knowledge base", "thread_id": "abc-123"}
{"type": "node_start", "node": "search_kb", "message": "Executing node: search_kb"}
{"type": "kb_search_complete", "data": "Found related known issues:\n- ID: ISSUE-101 | Checkout error 500 on mobile | Similarity: 0.89\n  Recommended action: Escalate to payments team; link incident INC-2023-09-10"}
{"type": "node_complete", "node": "search_kb"}
{"type": "node_start", "node": "analyze", "message": "Executing node: analyze"}
{"type": "node_complete", "node": "analyze"}
{"type": "node_start", "node": "classify", "message": "Executing node: classify"}
{"type": "classification_complete", "data": {"summary": "User experiencing 500 error on mobile checkout, matches known issue ISSUE-101", "category": "Bug", "severity": "High", "issue_type": "known_issue", "next_action": "Escalate to payments team per ISSUE-101"}}
{"type": "node_complete", "node": "classify"}
{"type": "status", "message": "Triage complete"}
```

### Endpoint: `/triage/resume` (POST)

Resume an interrupted workflow with additional details.

**Request:**

```bash
curl -X POST http://localhost:8000/triage/resume \
  -H "Content-Type: application/json" \
  -d '{
    "thread_id": "abc-123",
    "additional_details": "The error happens specifically on iOS Safari, started yesterday after the app update"
  }'
```

### Endpoint: `/health` (GET)

Health check endpoint.

```bash
curl http://localhost:8000/health
```

## 🧪 Testing

Run the test suite:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest tests/ --cov=agent --cov=app
```

## 📂 Project Structure

```
ticket-triage-agent/
├── agent/
│   ├── graph.py           # LangGraph workflow definition
│   ├── orchestrator.py    # Agent orchestration & streaming
│   ├── tools.py           # LangChain tools (search_kb, classify)
│   ├── models.py          # Pydantic models
│   └── prompts.py         # Prompt templates
├── app/
│   ├── main.py            # FastAPI application
│   └── config.py          # Configuration management
├── kb/
│   ├── knowledge_base.json # Known issues database (15 entries)
│   └── search.py          # Vector search implementation
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Main React component
│   │   ├── App.css        # Styling
│   │   └── main.tsx       # Entry point
│   ├── package.json
│   └── vite.config.ts
├── tests/
│   └── test_triage.py     # Unit tests
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (create this)
└── README.md              # This file
```

## 🎨 UI Features

- **Two-Column Layout**: Input on left, streaming results on right
- **Knowledge Base Display**: All 15 known issues visible with color-coded categories
- **Real-time Streaming**: See agent progress live
- **Interrupt Handling**: UI switches to response form when agent needs clarification
- **Mobile Responsive**: Stacks columns on smaller screens

## 🏭 Production Considerations

### Security

- **API Key Management**: 
  - Use environment variables for sensitive data
  - Consider AWS Secrets Manager or HashiCorp Vault in production
  - Rotate API keys regularly

- **Input Validation**:
  - Max description length enforced (5000 chars)
  - Sanitize user inputs to prevent injection attacks
  - Add rate limiting per user/IP

- **CORS Configuration**:
  - Current setup allows all origins (`allow_origins=["*"]`)
  - In production, restrict to specific domains
  - Example: `allow_origins=["https://yourdomain.com"]`

### Scalability

- **Async Processing**:
  - Already uses FastAPI async endpoints
  - Consider Celery for long-running tasks
  - Implement job queue for high traffic

- **Database**:
  - Current KB is in-memory JSON (15 entries)
  - For production, use vector database:
    - **Pinecone**: Managed vector search
    - **Weaviate**: Self-hosted option
    - **pgvector**: PostgreSQL extension
  - Add proper indexing for fast lookups

- **Caching**:
  - Cache KB embeddings (currently recomputed on every search)
  - Use Redis for session state instead of in-memory
  - Cache frequent query patterns

- **Load Balancing**:
  - Deploy multiple backend instances
  - Use NGINX or AWS ALB for load distribution
  - Implement health checks for auto-scaling

### Monitoring & Observability

- **Logging**:
  - Structured logging with correlation IDs
  - Log aggregation (ELK Stack, CloudWatch)
  - Track: latency, error rates, token usage

- **Metrics**:
  - Monitor API response times
  - Track OpenAI API costs per request
  - Alert on high error rates or latency

- **Tracing**:
  - LangSmith for LLM call tracing
  - OpenTelemetry for distributed tracing
  - Track full workflow execution paths

### Cost Optimization

- **LLM Costs**:
  - Current model: `gpt-4o-mini` (cost-effective)
  - Consider caching common queries
  - Implement response streaming to reduce user perception of latency
  - Monitor token usage per request

- **Embeddings**:
  - Cache KB embeddings on startup
  - Use smaller embedding models if accuracy permits
  - Batch embedding requests

### Error Handling

- **Graceful Degradation**:
  - Fallback to rule-based classification if LLM fails
  - Retry logic with exponential backoff for API calls
  - Circuit breaker pattern for external services

- **User Experience**:
  - Clear error messages for users
  - Automatic retry on transient failures
  - Fallback UI states

### Data Privacy

- **PII Handling**:
  - Identify and mask sensitive data in tickets
  - GDPR compliance for EU users
  - Data retention policies

- **Audit Trail**:
  - Log all triage decisions
  - Track who accessed what data
  - Enable compliance reporting

### Deployment

- **Containerization**:
  ```dockerfile
  # Example Dockerfile
  FROM python:3.10-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY . .
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

- **CI/CD**:
  - Automated testing on every commit
  - Staging environment for validation
  - Blue-green deployment for zero downtime

- **Infrastructure**:
  - Container orchestration (Kubernetes, ECS)
  - Auto-scaling based on load
  - Multi-region deployment for HA

## 🔧 Trade-offs & Time Constraints

### What Was Implemented

✅ **Core Functionality**:
- LangGraph-based agentic workflow
- Real-time streaming with interrupts
- Human-in-the-loop for clarification
- Knowledge base search with embeddings
- Structured classification output
- Modern React UI with two-column layout

✅ **Developer Experience**:
- Clear code structure and separation of concerns
- Type hints and Pydantic models
- Hot reload for development
- Comprehensive error handling

### What Could Be Improved (Given More Time)

❌ **Performance**:
- KB embeddings are computed on every search (should cache on startup)
- No connection pooling for OpenAI API
- No request batching

❌ **Persistence**:
- Thread state is in-memory (lost on restart)
- Should use Redis or database for production
- No conversation history storage

❌ **Testing**:
- Limited unit test coverage
- No integration tests
- No E2E tests for UI

❌ **Features**:
- No user authentication
- No ticket history or dashboard
- No analytics or reporting
- No webhook notifications for completion

❌ **Knowledge Base**:
- Static JSON file with 15 entries
- No admin UI to add/edit issues
- No versioning or rollback
- Manual similarity threshold (0.5)

❌ **UI/UX**:
- No loading states for individual components
- No retry mechanism in UI
- No export/share functionality
- Limited error state handling

### Design Decisions

1. **LangGraph over LangChain**: 
   - Enables stateful, interruptible workflows
   - Better for human-in-the-loop scenarios
   - More complex but more powerful

2. **Streaming over Batch**:
   - Better UX with real-time feedback
   - Users see progress immediately
   - More complex error handling

3. **In-Memory KB**:
   - Faster for small datasets (15 entries)
   - No database setup required
   - Not scalable beyond demo

4. **React over Server-Side Rendering**:
   - Better for interactive streaming UI
   - Client-side state management
   - Easier to develop and debug

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [OpenAI](https://openai.com)
- UI framework: [React](https://react.dev) + [Vite](https://vitejs.dev)
- Backend: [FastAPI](https://fastapi.tiangolo.com)

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ by Rohit**
