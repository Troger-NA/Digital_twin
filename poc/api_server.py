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

# Importar el grafo desde graph.py
from graph import graph

# Instancio FastAPI
app = FastAPI(
    title="Nico Chatbot API",
    description="API para el gemelo digital de Nico con memoria temporal y factual",
    version="1.0.0"
)

# Configurar CORS para permitir peticiones desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Desarrollo local
        "https://*.vercel.app",   # Vercel REEMPLAZAR
        "https://*.railway.app"   # Railway REEMPLAZAR
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear directorio de logs si no existe
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Configuración de seguridad
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "SECRET_TOKEN_WZ2l5TwbNE5GDndCOatlZTmkM1SILjwCZbN-kPPZtgg")
REQUIRE_TOKEN = os.getenv("REQUIRE_TOKEN", "true").lower() == "true"

# Configuración de rate limiting (límite de peticiones)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))  # peticiones por minuto
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))     # segundos

# Almacén para el rate limiting por IP
request_counts = defaultdict(list)

# Dependencias de seguridad
security = HTTPBearer(auto_error=False)

def clean_old_requests():
    """Eliminar peticiones más antiguas que la ventana de tiempo del rate limit"""
    current_time = time.time()
    for ip in list(request_counts.keys()):
        request_counts[ip] = [req_time for req_time in request_counts[ip] 
                             if current_time - req_time < RATE_LIMIT_WINDOW]

def check_rate_limit(ip: str) -> bool:
    """Verificar si la IP ha excedido el límite de peticiones"""
    clean_old_requests()
    current_time = time.time()
    
    if len(request_counts[ip]) >= RATE_LIMIT_REQUESTS:
        return False
    
    request_counts[ip].append(current_time)
    return True

def get_client_ip(request: Request) -> str:
    """Obtener la dirección IP del cliente"""
    return request.headers.get('X-Forwarded-For', request.client.host)

def require_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), 
                request: Request = None) -> bool:
    """Dependencia para requerir autenticación y verificar rate limiting"""
    if not REQUIRE_TOKEN:
        return True
    
    # Verificar rate limiting
    client_ip = get_client_ip(request)
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429, 
            detail=f"Límite de peticiones excedido. Máximo {RATE_LIMIT_REQUESTS} peticiones por {RATE_LIMIT_WINDOW} segundos"
        )
    
    # Verificar token
    if not credentials:
        raise HTTPException(status_code=401, detail="Token secreto requerido")
    
    if credentials.credentials != SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Token secreto inválido")
    
    return True

# Modelos Pydantic para validación de datos
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

@app.get("/")
async def root():
    """Endpoint de verificación de salud básico"""
    return {"message": "Nico Chatbot API está ejecutándose", "status": "healthy"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Verificación de salud detallada"""
    return {
        "api": "healthy",
        "message": "Nico Chatbot API está ejecutándose"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, 
    auth: bool = Depends(require_auth)
):
    """Endpoint principal del chat - procesa mensajes del usuario"""
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="El mensaje es requerido")

        # Inicializar el estado con el mensaje del usuario
        initial_state = {"messages": [{"role": "user", "content": request.message}]}
        
        # Ejecutar el grafo y obtener el resultado final
        result = graph.invoke(initial_state)
        
        # Extraer la respuesta
        response = result.get("response", "No se generó respuesta")
        
        # Logging simple en consola
        print(f"[CHAT] Usuario: {request.message[:50]}... | Respuesta: {response[:50]}...")
        
        return ChatResponse(response=response)

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/api/logs")
async def get_logs(auth: bool = Depends(require_auth)):
    """Obtener logs recientes (últimas 50 entradas)"""
    try:
        log_file = LOGS_DIR / f"chat_log_{datetime.datetime.now().strftime('%Y-%m-%d')}.json"
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            # Devolver últimas 50 entradas
            return {"logs": logs[-50:]}
        else:
            return {"logs": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor API de Nico Chatbot...")
    print(f"Seguridad habilitada: {REQUIRE_TOKEN}")
    print(f"Límite de peticiones: {RATE_LIMIT_REQUESTS} peticiones por {RATE_LIMIT_WINDOW} segundos")
    port = int(os.environ.get('PORT', 5000))
    uvicorn.run(app, host="0.0.0.0", port=port) 