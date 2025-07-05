import os
import json
import openai
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv


""" Asegurarse de tener el .env con las APIS (OCULTAS en el gitignore!!)"""
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "nico-factual"

# Crear el índice si no existe. La dimension coincide con el modelo de openAI
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    print(f"Índice '{index_name}' creado")

index = pc.Index(index_name)

# Cargar datos factuales
with open("db_personality/factual.json", "r", encoding="utf-8") as f:
    experiencias = json.load(f)

# Preparar y subir los vectores
vectors = []
for i, exp in enumerate(experiencias):
    empresa = exp.get("empresa", "")
    rol = exp.get("rol", "")
    periodo = exp.get("periodo", "")
    skills = exp.get("skills", [])
    for skill in skills:
        contenido = f"Empresa: {empresa}\nRol: {rol}\nPeríodo: {periodo}\nSkill: {skill}\n"
        if "skill_details" in exp and skill in exp["skill_details"]:
            skill_detail = exp["skill_details"][skill]
            contenido += f"Nivel: {skill_detail.get('nivel', 'N/A')}\n"
            contenido += f"Cómo aprendí: {skill_detail.get('como_aprendi', 'N/A')}\n"
            contenido += f"Proyectos: {skill_detail.get('proyectos', 'N/A')}\n"
        
        # Obtener embedding. Chequear dimensionalidad
        embedding = openai.embeddings.create(
            input=contenido,
            model="text-embedding-3-small"
        ).data[0].embedding
        # ID único para cada vector
        vector_id = f"{i}-{skill}"
        # Metadata
        metadata = {
            "empresa": empresa,
            "rol": rol,
            "periodo": periodo,
            "skill": skill,
            "skills": skills
        }
        vectors.append({"id": vector_id, "values": embedding, "metadata": metadata})

# Subir a Pinecone
print(f"Subiendo {len(vectors)} vectores a Pinecone...")
index.upsert(vectors)
print("¡Listo!") 