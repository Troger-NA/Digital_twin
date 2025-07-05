# Fase factual.json y carga en Pinecone

Este módulo permite vectorizar información factual (experiencias, roles, skills) y cargarla en una base de datos vectorial (Pinecone) para búsquedas semánticas. Para local se podria usar Qdrat.

## ¿Qué es factual.json?

Es un archivo JSON con información estructurada sobre experiencias y habilidades. Ejemplo de entrada:

```json
{
  "empresa": "Acme Corp",
  "rol": "Data Engineer",
  "periodo": "2021-2023",
  "skills": ["Python", "ETL", "SQL"],
  "skill_details": {
    "Python": {
      "nivel": "Avanzado",
      "como_aprendi": "Trabajo y cursos",
      "proyectos": "Automatización de pipelines"
    }
  }
}
```

## ¿Qué hace create_factual_embeddings.py?

- Lee el archivo `db_personality/factual.json`.
- Genera un embedding para cada skill usando OpenAI.
- Crea vectores con metadatos (empresa, rol, periodo, skill).
- Sube los vectores a un índice de Pinecone para búsquedas semánticas filtradas por metadata.

Esto creará el índice (si no existe) y subirá los vectores a Pinecone. 