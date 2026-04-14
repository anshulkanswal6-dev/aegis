from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
from agent import GenAIAgent
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import traceback

from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Mount Runtime API (additive — no existing routes changed) ---
from automations_api import router as automations_router, startup_worker, shutdown_worker
from integrations.telegram.router import router as telegram_router
from integrations.telegram.poller import _poller
from worker import get_worker
from scheduler import get_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Unified Startup Orchestration
    print("\n" + "="*50)
    print("🚀 AEGIS PLATFORM BOOTING...")
    print("="*50)
    
    await startup_worker()
    
    # Verify subsystems
    w = get_worker()
    s = get_scheduler()
    print(f"✅ API Server: Online")
    print(f"✅ Worker Engine: {'Active' if w.is_running else 'Inactive'}")
    print(f"✅ Scheduler: {'Running' if s.running else 'Stopped'}")
    print(f"✅ Telegram Poller: {'Connected' if _poller.running else 'Idle'}")
    print("="*50 + "\n")
    
    yield
    await shutdown_worker()

app = FastAPI(lifespan=lifespan)
app.include_router(automations_router)
app.include_router(telegram_router, prefix="/api")

# Enable CORS for frontend (production safe)
client_origin = os.getenv("CLIENT_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[client_origin] if client_origin != "*" else ["*"],
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

# --- Global Error Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"VALIDATION ERROR: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"CRITICAL ERROR: {str(exc)}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()},
    )

@app.get("/health")
async def health_check():
    """Consolidated health check for all runtime systems."""
    worker = get_worker()
    scheduler = get_scheduler()
    return {
        "status": "healthy",
        "api": "active",
        "worker": "active" if worker.is_running else "inactive",
        "scheduler": "running" if scheduler.running else "stopped",
        "telegram": "connected" if _poller.running else "disconnected",
        "env": os.getenv("STORE_BACKEND", "default")
    }

# --- Request Models (Synced with agentService.ts) ---

class ChatRequest(BaseModel):
    user_message: str
    session_id: Optional[str] = None
    project_name: Optional[str] = None # Added for context
    wallet_address: Optional[str] = None # Added for Supabase identity
    known_fields: Dict[str, Any] = Field(default_factory=dict)
    planning_model_id: str = os.getenv("DEFAULT_PLANNING_MODEL", "gemini_flash")
    codegen_model_id: str = os.getenv("DEFAULT_CODEGEN_MODEL", "gemini_flash")

class ContinueRequest(BaseModel):
    session_id: str
    wallet_address: Optional[str] = None # Added for Supabase identity
    project_name: Optional[str] = None # Added for context
    fields: Dict[str, Any] = Field(default_factory=dict)
    planning_model_id: str = os.getenv("DEFAULT_PLANNING_MODEL", "gemini_flash")


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
        wallet_address=req.wallet_address,
        known_fields=req.known_fields,
        planning_model_id=req.planning_model_id,
        codegen_model_id=req.codegen_model_id,
        project_name=req.project_name
    )

@app.post("/continue")
async def continue_chat(req: ContinueRequest):
    return agent.continue_chat(
        session_id=req.session_id, 
        fields=req.fields,
        wallet_address=req.wallet_address,
        planning_model_id=req.planning_model_id,
        project_name=req.project_name
    )

@app.post("/approve")
async def approve(req: ApproveRequest):
    return agent.approve_plan(session_id=req.session_id, approved=req.approved, feedback=req.feedback)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
