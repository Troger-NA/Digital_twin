# Módulo de ingenieria de datos

## 📋 Descripción General

Este módulo contiene los componentes para el procesamiento, análisis y vectorización de diferentes tipos de datos que alimentan al gemelo digital.

Cada parte tiene su readme para mas detalles
## Estructura del Módulo

```
data_ing/
├── Factica/                    # Vectorización de información factual
│   ├── create_factual_embeddings.py
│   ├── factual.json
│   ├── temporal_experience.json
│   └── README.md
└── Peronsalidad_DB/            # Análisis de conversaciones y personalidad
    ├── main.py
    ├── parser.py
    ├── pipeline_conversacion.py
    ├── vectorizar_bloques.py
    ├── analisis_simplificado_conversaciones.py
    ├── formal/
    ├── informal/
    └── README.md
```

## 📁 Componentes

### 🔧 Factica - Vectorización de Información Factual

Procesa y vectoriza inform

📖 [Ver documentación completa](Factica/README.md)

### 🧠 Peronsalidad_DB - Análisis de Conversaciones
**Ubicación**: `Peronsalidad_DB/`

Sistema completo para el procesamiento y análisis de conversaciones de WhatsApp, incluyendo análisis de personalidad.



📖 [Ver documentación completa](Peronsalidad_DB/README.md)


##  Outputs

### Factica
- Embeddings vectoriales en Pinecone
- Metadatos estructurados

### Peronsalidad_DB
- Archivos `*_parsed_anon.json` - Mensajes anonimizados
- Archivos `*_conversaciones_analizadas.json` - Análisis por conversación
- `promedio_bigfive_global.json` - Promedio de la metrica OCEAN (big five)
- `matrices_promedio_por_grupo.json` - Análisis por grupos
- Vectorizacion
  **Resta integrarlo a pinecone y ajustar dimensionalidad a 1536**


---

**Volver al [README principal](../README.md)** 