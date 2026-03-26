from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
from agent import GenAIAgent
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import traceback

app = FastAPI()

# --- Mount Runtime API (additive — no existing routes changed) ---
from automations_api import router as automations_router, startup_worker, shutdown_worker
app.include_router(automations_router)
app.add_event_handler("startup", startup_worker)
app.add_event_handler("shutdown", shutdown_worker)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agent
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
catalogue_path = os.path.join(BASE_DIR, "catalogue.json")
action_catalogue_path = os.path.join(BASE_DIR, "action_catalogue.json")
agent = GenAIAgent(catalogue_path, action_catalogue_path)

# --- Global Error Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"CRITICAL ERROR: {str(exc)}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()},
    )

# --- Request Models (Synced with agentService.ts) ---

class ChatRequest(BaseModel):
    user_message: str
    session_id: Optional[str] = None
    known_fields: Dict[str, Any] = Field(default_factory=dict)
    planning_model_id: str = "gemini_flash"
    codegen_model_id: str = "gemini_flash"

class ContinueRequest(BaseModel):
    session_id: str
    fields: Dict[str, Any] = Field(default_factory=dict)
    planning_model_id: str = "gemini_flash"

class ApproveRequest(BaseModel):
    session_id: str
    approved: bool
    feedback: Optional[str] = None

# --- Endpoints ---

@app.get("/models")
async def get_models():
    return agent.list_available_models()

@app.post("/chat")
async def chat(req: ChatRequest):
    return agent.chat(
        user_message=req.user_message,
        session_id=req.session_id,
        known_fields=req.known_fields,
        planning_model_id=req.planning_model_id,
        codegen_model_id=req.codegen_model_id
    )

@app.post("/continue")
async def continue_chat(req: ContinueRequest):
    return agent.continue_chat(
        session_id=req.session_id, 
        fields=req.fields,
        planning_model_id=req.planning_model_id
    )

@app.post("/approve")
async def approve(req: ApproveRequest):
    return agent.approve_plan(session_id=req.session_id, approved=req.approved, feedback=req.feedback)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
