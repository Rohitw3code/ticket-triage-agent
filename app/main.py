from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import get_settings
from agent.orchestrator import TriageAgent
from agent.models import TriageRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title="Ticket Triage Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = TriageAgent()


@app.get("/")
def root():
    return {
        "name": "Ticket Triage Agent",
        "status": "running"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/triage/stream")
async def triage_ticket_stream(request: TriageRequest):
    if not request.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    
    if len(request.description) > settings.MAX_DESCRIPTION_LENGTH:
        raise HTTPException(status_code=400, detail="Description too long")
    
    try:
        logger.info(f"Processing ticket stream: {request.description[:50]}...")
        
        return StreamingResponse(
            agent.triage_stream(request.description),
            media_type="application/x-ndjson"
        )
    
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)