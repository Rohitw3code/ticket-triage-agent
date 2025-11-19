from fastapi import FastAPI, HTTPException
import logging

from app.config import get_settings
from agent.orchestrator import TriageAgent
from agent.models import TriageRequest, TriageResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title="Ticket Triage Agent")

# Initialize agent once
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


@app.post("/triage", response_model=TriageResponse)
async def triage_ticket(request: TriageRequest):
    # Validate input
    if not request.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    
    if len(request.description) > settings.MAX_DESCRIPTION_LENGTH:
        raise HTTPException(status_code=400, detail="Description too long")
    
    try:
        logger.info(f"Processing ticket: {request.description[:50]}...")
        response = await agent.triage(request.description)
        logger.info(f"Triage complete: {response.category} - {response.severity}")
        return response
    
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)