"""
Simple FastAPI application that serves as the evolvable core.

This is the main application that AI agents can modify and extend
based on evolution requests. It starts as a simple "Hello World"
but is designed to be enhanced by agents over time.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Seed Application",
    description="A self-evolving application powered by AI agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    version: str
    
class InfoResponse(BaseModel):
    """Application information response model."""
    name: str
    description: str
    version: str
    features: List[str]
    last_evolution: Optional[str] = None

class EvolutionLogEntry(BaseModel):
    """Evolution log entry model."""
    timestamp: datetime
    issue_number: int
    description: str
    agent_summary: str
    status: str

# In-memory storage (would be replaced by database in evolution)
evolution_log: List[EvolutionLogEntry] = []
app_features: List[str] = ["Health Check", "API Documentation", "Evolution Tracking"]

@app.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    """
    Root endpoint that returns a welcome message.
    
    Returns:
        Dict[str, str]: Welcome message and basic information
    """
    return {
        "message": "Welcome to the AI Seed Application!",
        "description": "This application evolves through AI agent contributions",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint for monitoring and deployment verification.
    
    Returns:
        HealthResponse: Current health status and metadata
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0"
    )

@app.get("/info", response_model=InfoResponse)
async def get_info() -> InfoResponse:
    """
    Get application information including current features and evolution status.
    
    Returns:
        InfoResponse: Application metadata and feature list
    """
    last_evolution = None
    if evolution_log:
        last_evolution = evolution_log[-1].timestamp.isoformat()
    
    return InfoResponse(
        name="AI Seed Application",
        description="A self-evolving application powered by AI agents",
        version="1.0.0",
        features=app_features,
        last_evolution=last_evolution
    )

@app.get("/evolution-log", response_model=List[EvolutionLogEntry])
async def get_evolution_log() -> List[EvolutionLogEntry]:
    """
    Get the log of all evolution events processed by AI agents.
    
    Returns:
        List[EvolutionLogEntry]: History of evolution events
    """
    return evolution_log

@app.post("/evolution-log", response_model=Dict[str, str])
async def add_evolution_entry(entry: EvolutionLogEntry) -> Dict[str, str]:
    """
    Add a new evolution entry to the log (typically called by AI agents).
    
    Args:
        entry: Evolution log entry to add
        
    Returns:
        Dict[str, str]: Confirmation message
    """
    evolution_log.append(entry)
    logger.info(f"Added evolution entry for issue #{entry.issue_number}")
    
    return {
        "message": "Evolution entry added successfully",
        "issue_number": str(entry.issue_number)
    }

@app.get("/features", response_model=List[str])
async def get_features() -> List[str]:
    """
    Get the current list of application features.
    
    Returns:
        List[str]: List of current features
    """
    return app_features

@app.post("/features", response_model=Dict[str, str])
async def add_feature(feature: Dict[str, str]) -> Dict[str, str]:
    """
    Add a new feature to the application (typically called by AI agents).
    
    Args:
        feature: Feature information with 'name' key
        
    Returns:
        Dict[str, str]: Confirmation message
    """
    feature_name = feature.get("name")
    if not feature_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feature name is required"
        )
    
    if feature_name not in app_features:
        app_features.append(feature_name)
        logger.info(f"Added new feature: {feature_name}")
        
        return {
            "message": "Feature added successfully",
            "feature": feature_name
        }
    else:
        return {
            "message": "Feature already exists",
            "feature": feature_name
        }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException) -> JSONResponse:
    """
    Global HTTP exception handler.
    
    Args:
        request: The request that caused the exception
        exc: The HTTP exception
        
    Returns:
        JSONResponse: Formatted error response
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions.
    
    Args:
        request: The request that caused the exception
        exc: The exception
        
    Returns:
        JSONResponse: Formatted error response
    """
    logger.error(f"Unhandled exception: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

def main() -> None:
    """
    Main function to run the application.
    
    This function is called when the script is run directly.
    It starts the uvicorn server with appropriate configuration.
    """
    logger.info("Starting AI Seed Application...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
