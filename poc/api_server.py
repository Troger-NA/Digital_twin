from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
import json
from pathlib import Path
import datetime
import time
from collections import defaultdict
from typing import Optional

# Import the graph from graph.py
from graph import graph

# Initialize FastAPI
app = FastAPI(
    title="Nico Chatbot API",
    description="API for Nico's digital twin with temporal and factual memory",
    version="1.0.0"
)

# Configure CORS for production deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "Reemplazar vercel front",   # Vercel frontend
        "https://*.railway.app"   # Railway backend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Security configuration
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "your-secret-token-here")
REQUIRE_TOKEN = os.getenv("REQUIRE_TOKEN", "true").lower() == "true"

# Validate security configuration
if REQUIRE_TOKEN and SECRET_TOKEN == "your-secret-token-here":
    print("ERROR: You must set a real SECRET_TOKEN environment variable!")
    print("Example: export SECRET_TOKEN='your-actual-secret-token-here'")
    exit(1)

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))  # requests per minute
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))     # seconds

# Store for rate limiting by IP
request_counts = defaultdict(list)

# Security dependencies
security = HTTPBearer(auto_error=False)

def clean_old_requests():
    """Remove requests older than the rate limit window"""
    current_time = time.time()
    for ip in list(request_counts.keys()):
        request_counts[ip] = [req_time for req_time in request_counts[ip] 
                             if current_time - req_time < RATE_LIMIT_WINDOW]

def check_rate_limit(ip: str) -> bool:
    """Check if IP has exceeded rate limit"""
    clean_old_requests()
    current_time = time.time()
    
    if len(request_counts[ip]) >= RATE_LIMIT_REQUESTS:
        return False
    
    request_counts[ip].append(current_time)
    return True

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    return request.headers.get('X-Forwarded-For', request.client.host)

def require_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), 
                request: Request = None) -> bool:
    """Dependency to require authentication and check rate limiting"""
    if not REQUIRE_TOKEN:
        return True
    
    # Check rate limiting
    client_ip = get_client_ip(request)
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds"
        )
    
    # Check token
    if not credentials:
        raise HTTPException(status_code=401, detail="Secret token required")
    
    if credentials.credentials != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid secret token")
    
    return True

# Pydantic models for data validation
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class HealthResponse(BaseModel):
    api: str
    message: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

def log_message(message_data: dict):
    """Log message data to JSON file"""
    timestamp = datetime.datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "session_id": message_data.get("session_id", "default"),
        "user_message": message_data.get("message", ""),
        "assistant_response": message_data.get("response", ""),
        "processing_time_ms": message_data.get("processing_time", 0),
        "graph_state": message_data.get("graph_state", {}),
        "error": message_data.get("error", None)
    }
    
    # Create log file with date
    log_file = LOGS_DIR / f"chat_log_{datetime.datetime.now().strftime('%Y-%m-%d')}.json"
    
    # Load existing logs or create new list
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []
    
    # Add new log entry
    logs.append(log_entry)
    
    # Save updated logs
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)
    
    # Also log to console for debugging
    print(f"[LOG] {timestamp} - User: {log_entry['user_message'][:50]}... - Response: {log_entry['assistant_response'][:50]}...")

@app.get("/")
async def root():
    """Basic health check endpoint"""
    return {"message": "Nico Chatbot API is running", "status": "healthy"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return {
        "api": "healthy",
        "message": "Nico Chatbot API is running"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, 
    auth: bool = Depends(require_auth),
    http_request: Request = None
):
    """Main chat endpoint - processes user messages"""
    start_time = datetime.datetime.now()
    message_data = {
        "session_id": http_request.headers.get('X-Session-ID', 'default') if http_request else 'default',
        "message": "",
        "response": "",
        "processing_time": 0,
        "graph_state": {},
        "error": None
    }
    
    try:
        if not request.message:
            message_data["error"] = "Message is required"
            log_message(message_data)
            raise HTTPException(status_code=400, detail="Message is required")

        message_data["message"] = request.message

        # Initialize the state with the user message
        initial_state = {"messages": [{"role": "user", "content": request.message}]}
        
        # Run the graph and get the final result
        result = graph.invoke(initial_state)
        
        # Store graph state for logging
        message_data["graph_state"] = {
            "detector": result.get("detector", {}),
            "factual": result.get("factual", ""),
            "temporal": result.get("temporal", ""),
            "personality": result.get("personality", ""),
            "response": result.get("response", "")
        }
        
        # Extract the response
        response = result.get("response", "No response generated")
        message_data["response"] = response
        
        # Calculate processing time
        end_time = datetime.datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000
        message_data["processing_time"] = round(processing_time, 2)
        
        # Log the successful interaction
        log_message(message_data)
        
        return ChatResponse(response=response)

    except HTTPException:
        raise
    except Exception as e:
        # Calculate processing time even for errors
        end_time = datetime.datetime.now()
        processing_time = (end_time - start_time).total_seconds() * 1000
        message_data["processing_time"] = round(processing_time, 2)
        message_data["error"] = str(e)
        
        # Log the error
        log_message(message_data)
        
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/logs")
async def get_logs(auth: bool = Depends(require_auth)):
    """Get recent logs (last 50 entries)"""
    try:
        log_file = LOGS_DIR / f"chat_log_{datetime.datetime.now().strftime('%Y-%m-%d')}.json"
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            # Return last 50 entries
            return {"logs": logs[-50:]}
        else:
            return {"logs": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Starting Nico Chatbot API server...")
    print(f"Security enabled: {REQUIRE_TOKEN}")
    print(f"Rate limit: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds")
    port = int(os.environ.get('PORT', 5000))
    uvicorn.run(app, host="0.0.0.0", port=port) 