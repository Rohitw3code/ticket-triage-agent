# 🎫 Ticket Triage Agent

An AI-powered support ticket classification and routing system built with LangGraph, FastAPI, and React. The agent intelligently analyzes support tickets, searches a knowledge base for similar issues, and provides structured classification with recommended next actions.

## ✨ Features

- 🤖 **AI-Powered Classification**: Uses OpenAI GPT models for intelligent ticket analysis
- 🔍 **Knowledge Base Search**: Semantic search across known issues with similarity scoring
- ⏸️ **Human-in-the-Loop**: Interrupts workflow to ask for clarification when needed
- 📊 **Real-time Streaming**: Live streaming of the triage process
- 🎨 **Modern UI**: Clean, responsive interface with two-column layout
- 🔄 **Stateful Workflows**: Resume interrupted workflows with additional context

## 📸 Screenshots

### Main Interface
![Ticket Triage Agent - Main Interface](https://raw.githubusercontent.com/Rohitw3code/ticket-triage-agent/refs/heads/main/ss.png)

*Two-column interface with query input and knowledge base on the left, real-time streaming triage results on the right.*

### Interrupt Flow
![Ticket Triage Agent - Human in the Loop](https://raw.githubusercontent.com/Rohitw3code/ticket-triage-agent/refs/heads/main/sss2.png)

*Agent interrupts to ask for clarification when the query is too vague, then resumes classification after receiving additional details.*

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

The application supports multiple environments (dev, prod, test). Copy the appropriate example file:

**For Development:**
```bash
cp .env.dev .env
```

**For Production:**
```bash
cp .env.prod .env
```

**For Testing:**
```bash
cp .env.test .env
```

Then edit `.env` and add your OpenAI API key:

```env
ENVIRONMENT=dev
DEBUG=true
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.3
OPENAI_TIMEOUT=60

# Retry Configuration
MAX_RETRIES=2
RETRY_DELAY=1.0
RETRY_BACKOFF=2.0

PORT=8000
MAX_DESCRIPTION_LENGTH=5000
LOG_LEVEL=DEBUG
KB_PATH=kb/knowledge_base.json
```

**Environment Variables:**
- `ENVIRONMENT`: Environment name (dev/prod/test)
- `DEBUG`: Enable debug mode
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: Model to use (default: gpt-4o-mini)
- `OPENAI_TEMPERATURE`: Temperature for LLM (0-1)
- `OPENAI_TIMEOUT`: Request timeout in seconds
- `MAX_RETRIES`: Maximum retry attempts for failed LLM calls
- `RETRY_DELAY`: Initial delay between retries (seconds)
- `RETRY_BACKOFF`: Exponential backoff multiplier
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `CORS_ORIGINS`: Allowed CORS origins (list)

#### Start the Backend Server

**Development Mode:**
```bash
ENVIRONMENT=dev python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production Mode:**
```bash
ENVIRONMENT=prod python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Testing Mode:**
```bash
ENVIRONMENT=test python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

The API will be available at `http://localhost:8000` (or port 8001 for testing)

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

## 🧪 Running Tests

### Quick Test Run

```bash
# Run fast tests (excludes slow LLM-dependent tests)
pytest tests/test_triage.py -v -m "not slow"
```

Or use the test runner script:

```bash
chmod +x run_tests.sh
./run_tests.sh
```

### All Tests

```bash
# Run all tests including slow ones (requires valid OPENAI_API_KEY)
pytest tests/test_triage.py -v
```

### Test Coverage

The test suite includes:
- ✅ Health check endpoint validation
- ✅ Request validation (empty, whitespace, length limits)
- ✅ Edge cases (special characters, unicode, line breaks)
- ✅ Resume endpoint validation
- ✅ Environment configuration verification
- ⏱️ Full streaming workflow (marked as slow)
- ⏱️ Classification structure validation (marked as slow)

**Test Types:**
- **Fast tests**: Unit tests for request/response validation, no LLM calls
- **Slow tests**: Integration tests that exercise full workflow with LLM

**Current Status:**
```bash
$ pytest tests/test_triage.py -v -m "not slow"
# 15 tests collected / 4 deselected
# 8 passed ✅
```

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

✅ **Production-Ready Features**:
- **Retry Logic**: Automatic retry with exponential backoff for LLM calls
- **Error Handling**: Graceful degradation with fallback classifications
- **Multi-Environment**: Separate configs for dev/prod/test
- **Logging**: Environment-specific log levels
- **Timeouts**: Configurable request timeouts
- **CORS**: Environment-specific CORS policies

## ⚙️ Multi-Environment Configuration

The application supports three environments with different configurations:

### Development Environment
- **Debug Mode**: Enabled
- **Log Level**: DEBUG (verbose logging)
- **Max Retries**: 2 (faster feedback)
- **CORS**: Allow all origins
- **Use Case**: Local development and testing

### Production Environment
- **Debug Mode**: Disabled
- **Log Level**: WARNING (only important messages)
- **Max Retries**: 5 (more resilient)
- **CORS**: Restricted to specific domains
- **Use Case**: Live deployment

### Testing Environment
- **Debug Mode**: Enabled
- **Log Level**: DEBUG
- **Max Retries**: 1 (fast test execution)
- **CORS**: Allow all origins
- **Use Case**: Automated tests and CI/CD

### Switching Environments

Set the `ENVIRONMENT` variable:

```bash
# Development
export ENVIRONMENT=dev
python -m uvicorn app.main:app --reload

# Production
export ENVIRONMENT=prod
python -m uvicorn app.main:app --workers 4

# Testing
export ENVIRONMENT=test
pytest tests/
```

Or use environment-specific .env files:
```bash
cp .env.dev .env    # For development
cp .env.prod .env   # For production
cp .env.test .env   # For testing
```

## 🛡️ Error Handling & Retry Logic

The application includes robust error handling for LLM calls:

### Retry Mechanism

- **Exponential Backoff**: Automatically retries failed LLM calls with increasing delays
- **Configurable Retries**: Set `MAX_RETRIES`, `RETRY_DELAY`, and `RETRY_BACKOFF` in environment
- **Smart Error Detection**: Different handling for rate limits, timeouts, and connection errors

### Fallback Behavior

When all retries fail, the system:
1. Logs detailed error information
2. Returns a fallback classification with "Manual review required"
3. Continues workflow instead of crashing
4. Provides user-friendly error messages

### Example Error Scenarios

**Rate Limit Exceeded:**
```
⚠️ Rate limit hit, waiting 2.0s before retry 1/3
⚠️ Rate limit hit, waiting 4.0s before retry 2/3
✅ Success on retry 3
```

**Network Timeout:**
```
⚠️ Request timed out. Retrying in 1.0s...
⚠️ Request timed out. Retrying in 2.0s...
✅ Success on retry 2
```

**All Retries Failed:**
```
❌ LLM call failed after 3 retries
✅ Returning fallback classification for manual review
```

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
- Basic unit and integration tests included
- No E2E tests for UI workflows
- Limited coverage for edge cases

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

## 🐳 Docker Deployment

### Quick Start with Docker Compose

The project includes Docker configurations for both backend and frontend services.

**Start all services:**

```bash
docker-compose up --build
```

**Services:**
- Backend API: `http://localhost:8000`
- Frontend UI: `http://localhost:5173`

**Stop services:**

```bash
docker-compose down
```

### Backend Dockerfile

Multi-stage build for optimized image size:

```dockerfile
# Builder stage - installs dependencies
FROM python:3.10-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage - slim runtime
FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run backend:**

```bash
docker build -t ticket-triage-backend .
docker run -p 8000:8000 -e OPENAI_API_KEY=$OPENAI_API_KEY ticket-triage-backend
```

### Frontend Dockerfile

Two-stage build with nginx for production:

```dockerfile
# Build stage
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Build and run frontend:**

```bash
cd frontend
docker build -t ticket-triage-frontend .
docker run -p 5173:80 ticket-triage-frontend
```

### Production Deployment Strategies

#### 1. **Container Orchestration**

**Kubernetes:**
```yaml
# Example deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ticket-triage-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ticket-triage-backend
  template:
    metadata:
      labels:
        app: ticket-triage-backend
    spec:
      containers:
      - name: backend
        image: ticket-triage-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "prod"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "256Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**Horizontal Pod Autoscaling:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ticket-triage-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ticket-triage-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**AWS ECS/Fargate:**
```json
{
  "family": "ticket-triage",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-registry/ticket-triage-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "prod"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ticket-triage",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "backend"
        }
      }
    }
  ]
}
```

#### 2. **Persistent State Management**

**Redis for Thread State (Recommended):**

```python
# Add to requirements.txt
# redis==5.0.0

# Update agent/graph.py
from langgraph.checkpoint.redis import RedisSaver
import redis

# Replace MemorySaver with RedisSaver
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)
memory = RedisSaver(redis_client)
```

**Docker Compose with Redis:**

```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    
  backend:
    build: .
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379

volumes:
  redis-data:
```

#### 3. **Scaling Considerations**

**Load Balancing:**
- Use nginx or AWS ALB for distributing requests
- Enable sticky sessions for interrupt/resume flows (thread_id routing)
- Configure health checks on `/health` endpoint

**Caching:**
```python
# Add caching for KB embeddings
from functools import lru_cache

@lru_cache(maxsize=1)
def get_kb_embeddings():
    # Cache embeddings to avoid recomputation
    return compute_embeddings(knowledge_base)
```

**Rate Limiting:**
```python
# Add to app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/triage/stream")
@limiter.limit("10/minute")  # Limit to 10 requests per minute
async def triage_stream_endpoint(request: Request, ticket: TicketRequest):
    ...
```

#### 4. **Monitoring & Observability**

**Health Checks:**
```python
# Enhanced health check in app/main.py
@app.get("/health")
async def health_check():
    checks = {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "kb_loaded": len(load_knowledge_base()) > 0,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check Redis connection if enabled
    if settings.REDIS_HOST:
        try:
            redis_client.ping()
            checks["redis"] = "connected"
        except Exception:
            checks["redis"] = "disconnected"
            checks["status"] = "degraded"
    
    return checks
```

**Logging:**
```python
# Add structured logging
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName
        }
        return json.dumps(log_obj)

# Configure logger
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("ticket_triage")
logger.addHandler(handler)
logger.setLevel(settings.LOG_LEVEL)
```

**Metrics (Prometheus):**
```python
# Add to requirements.txt: prometheus-client
from prometheus_client import Counter, Histogram, generate_latest

triage_requests = Counter('triage_requests_total', 'Total triage requests')
triage_duration = Histogram('triage_duration_seconds', 'Triage processing time')
kb_matches = Counter('kb_matches_total', 'KB matches found', ['issue_type'])

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### 5. **Security Hardening**

```python
# app/main.py security enhancements

# 1. Add security headers
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if settings.ENVIRONMENT == "prod":
    app.add_middleware(HTTPSRedirectMiddleware)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS.split(",")
    )

# 2. Input validation
from pydantic import Field, validator

class TicketRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=5000)
    
    @validator('description')
    def sanitize_description(cls, v):
        # Remove potential XSS
        import html
        return html.escape(v.strip())

# 3. API Key validation
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/triage/stream")
async def triage_stream(
    ticket: TicketRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Validate API key
    if credentials.credentials != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    ...
```

#### 6. **CI/CD Pipeline Example**

**GitHub Actions (.github/workflows/deploy.yml):**

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/
        env:
          ENVIRONMENT: test
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build backend
        run: docker build -t ticket-triage-backend:${{ github.sha }} .
      - name: Build frontend
        run: |
          cd frontend
          docker build -t ticket-triage-frontend:${{ github.sha }} .
      - name: Push to registry
        run: |
          docker push your-registry/ticket-triage-backend:${{ github.sha }}
          docker push your-registry/ticket-triage-frontend:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster ticket-triage-cluster \
            --service ticket-triage-service \
            --force-new-deployment
```

#### 7. **Environment Variables for Production**

```bash
# .env.production
ENVIRONMENT=prod
OPENAI_API_KEY=sk-...
MAX_RETRIES=5
RETRY_DELAY=2
PORT=8000
LOG_LEVEL=WARNING

# State management
REDIS_HOST=redis.production.internal
REDIS_PORT=6379

# Security
ALLOWED_HOSTS=api.yourdomain.com
API_KEY=your-secret-api-key
CORS_ORIGINS=https://app.yourdomain.com

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
```

### Testing Your Deployment

```bash
# Run tests before deploying
pytest tests/ -v

# Test Docker build
docker-compose up --build

# Test production image
docker run -e ENVIRONMENT=prod ticket-triage-backend:latest

# Load test (optional)
# Install: pip install locust
locust -f tests/load_test.py --host=http://localhost:8000
```

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
