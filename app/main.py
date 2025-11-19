from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = TriageAgent()


class ResumeRequest(BaseModel):
    thread_id: str
    additional_details: str


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


@app.post("/triage/resume")
async def resume_ticket_triage(request: ResumeRequest):
    if not request.thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")
    
    if not request.additional_details.strip():
        raise HTTPException(status_code=400, detail="additional_details cannot be empty")
    
    try:
        logger.info(f"Resuming workflow for thread: {request.thread_id}")
        
        return StreamingResponse(
            agent.resume_with_details(request.thread_id, request.additional_details),
            media_type="application/x-ndjson"
        )
    
    except Exception as e:
        logger.error(f"Error resuming workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)