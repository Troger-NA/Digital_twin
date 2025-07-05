# Santex Reto - Mock navegable

Este mock está configurado para ejecutarse con Docker, incluyendo tanto el backend Python como el frontend Node.

## Requisitos

- Docker
- Docker Compose


## Ejecución

### Docker Compose (Recomendado)

```bash
# Construir y ejecutar todos los servicios
docker-compose up --build

# Detener servicios cuando sea necesario
docker-compose down
```

**Acceso a la aplicación**

- **Frontend**: http://localhost:3000
- **API Backend**: http://localhost:5000
- **Health Check**: http://localhost:5000/health



### Entorno Local (No recomendado)

Para desarrollo local sin Docker:

```bash
# Backend
pip install -r requirements.txt
python api_server.py

# Frontend (requiere npm)
cd Front
npm install
npm start
``` 


## Files

En graph está el grafo usado (Mock). Se puede ejecutar tanto en consola (back_test.py) como con el front (ejecutar api_server.py previamente)
