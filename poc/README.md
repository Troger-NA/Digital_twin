# Nico Clon - POC 
**Esto es una muestra de codigo. No se comparte tal cual está desplegado para no exponer la DB con los chats, pero es similar**

## Arquitectura del Sistema

### Componentes Principales

```
POC/
├── Backend_main.py           # Backend por cmd
├── api_server.py             # API con fastapi
├── graph.py                  # Grafo principal
├── Helper_temporal.py        # Usado para "Hard-codear" expresiones temporales.
├── db_personality/           # Base de datos de personalidad (**Oculta**)
│   ├── factual.json         # Experiencias laborales
│   ├── temporal_experience.json  # Eventos temporales
│   ├── embeddings.npy       # Embeddings locales
│   ├── faiss.index          # Índice FAISS
│   └── factual_embeddings/  # Embeddings para Pinecone
└── Front/                   # Frontend web
```
**En la proxima version, la DB de personalidad se implementa en pinecone**