from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
import random
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage
import json
import dotenv
import os
import re
import numpy as np
import openai
from pinecone import Pinecone
from helper_temporal import parse_periodo, get_empresa_periodo, aplicar_regla_temporal
dotenv.load_dotenv()



"""
En este file se define el grafo del chatbot y toda su ejecucion
Se separa del main para que sea mas facil de entender y modificar.
"""
def normalize_skills(skills: list) -> list:
    """ Esta funcion tiene como intencion normalizar los skills para que la prueba sea mas efectiva.
    Esto es importante porque posteriormenten, en el detector node se extrae sobre que skill se pregunta.
    Como los skills no cambian con el tiempo (a lo sumo se agregan) no es un hardcode inadecuado para un primer PoC """


    if not skills:
        return []
    
    # Mapeo de variaciones a términos estándar
    skill_mapping = {
        # AI variations
        "inteligencia artificial": "ai",
        "ia": "ai", 
        "ai": "ai",
        "desarrollo de ia": "ai",
        "desarrollo de ai": "ai",
        "desarrollo ia": "ai",
        "desarrollo ai": "ai",
        
        # Machine Learning variations
        "machine learning": "machine learning",
        "ml": "machine learning",
        "aprendizaje automatico": "machine learning",
        "aprendizaje automático": "machine learning",
        
        # Data Science variations
        "data science": "data science",
        "ciencia de datos": "data science",
        "datascience": "data science",
        
        # Programming variations
        "programacion": "python",  # default to python if no specific language
        "programación": "python",
        "coding": "python",
        "desarrollo": "python",
        
        # Web development
        "desarrollo web": "backend",
        "web development": "backend",
        "frontend": "backend",  # assuming backend for now
        
        # Other common variations
        "ci/cd": "ci/cd",
        "cicd": "ci/cd",
        "continuous integration": "ci/cd",
        "github": "github actions",
        "aws lambda": "lambda",
        "lambda functions": "lambda",
        "apis": "apis",
        "api": "apis",
        "rest api": "apis",
        "graphql": "apis",
        
        # Personal skills variations
        "cocinar": "cocina",
        "cooking": "cocina",
        "music": "musica",
        "sports": "deportes",
        "languages": "idiomas",
        "photography": "fotografia",
        "travel": "viajes",
        "reading": "lectura",
        "writing": "escritura",
        "meditation": "meditacion",
        "cycling": "ciclismo",
        "soccer": "futbol",
        "football": "futbol",
        "guitar": "guitarra",
        "spanish": "espanol",
        "english": "ingles",
        "portuguese": "portugues",
        "video editing": "edicion de video",
        "blog": "blogging",
        "podcast": "podcasting"
    }
    
    normalized = []
    for skill in skills:
        skill_lower = skill.lower().strip()
        # Buscar en el mapeo
        if skill_lower in skill_mapping:
            normalized.append(skill_mapping[skill_lower])
        else:
            # Si no está en el mapeo, mantener el original
            normalized.append(skill_lower)
    
    # Remover duplicados manteniendo el orden
    seen = set()
    unique_normalized = []
    for skill in normalized:
        if skill not in seen:
            seen.add(skill)
            unique_normalized.append(skill)
    
    return unique_normalized

# Define the state with messages
class State(TypedDict):
    messages: Annotated[list, add_messages]
    detector: str
    temporal: str
    factual: str
    personality: str
    response: str

def detector_node(state: State) -> dict:
    """Detecta si la pregunta del input es de tipo factual, o sobre un evento temporal, y extrae skills mencionados."""
    
    

    prompt = f""" Identifica si el prompt introducido responde a un evento temporal, factual, o combinado.
    temporal es una pregunta del
    Identifica el topico segun: ("trabajo", "amistad", "familia", "salud", "emociones", "ocio", "estudios", "dinero", "viajes", "tecnología", "deportes", "comida", "política", "entretenimiento", "amor") y la emocion segun ("joy", "anger", "sadness", "surprise", "others")
    
    También extrae skills mencionados en la consulta. Los skills pueden ser:
    - Laborales: python, javascript, react, node, sql, aws, docker, langchain, ai, machine learning, data science, ci/cd, github actions, lambda, apis, backend, metodologia, estadistica, simulacion, drug discovery, multiagente, automatizacion, pipelines, hpc, coordinacion, planificacion, community manager, rag, faiss, pinecone, fluorescencia
    - Personales: cocina, musica, deportes, idiomas, fotografia, viajes, lectura, escritura, meditacion, yoga, ciclismo, futbol, guitarra, piano, espanol, ingles, portugues, blogging, podcasting, fotografia digital, edicion de video
    
    IMPORTANTE: Normaliza los skills a términos simples. Por ejemplo:
    - "inteligencia artificial", "IA", "AI", "desarrollo de IA", "desarrollo de AI" → "ai"
    - "machine learning", "ML", "aprendizaje automático" → "machine learning"
    - "data science", "ciencia de datos" → "data science"
    - "desarrollo web", "web development" → "backend" (si es backend) o "frontend" (si es frontend)
    - "programación", "coding", "desarrollo" → buscar el lenguaje específico mencionado
    
    ADEMÁS, detecta:
    1. EMPRESA: Si se menciona alguna empresa laboral (ej: "Google", "Microsoft", "Santex", "Acme Corp") o referencias a estudios (ej: "doctorado", "maestría", "universidad"). Si no se menciona, devuelve null.
    2. RANGO_TEMPORAL: Si se mencionan años o rangos temporales (ej: "2020-2023", "2019", "últimos 2 años", "hace 5 años"). Si no se menciona, devuelve null.
    3. CONECTOR_TEMPORAL: Si hay conectores temporales como "antes", "después", "durante", "cuando", "mientras", "desde", "hasta", "entre", "después de", "antes de", "en", "durante el", "por". Si no hay, devuelve null.
    
    NOTA IMPORTANTE: 
    - Si se menciona un año específico (ej: "en 2020", "durante 2019"), el conector temporal debe ser "durante" o "en".
    - Si se menciona "doctorado", "maestría" o "universidad", la empresa debe ser "Universidad de Buenos Aires".
    
    Input del usuario: {state["messages"][-1].content}.
    Responde con un json que tenga la forma:
    {{
        "tipo": "temporal" | "factual" | "combinado",
        "topic": "topic",
        "emotion": "emotion",
        "skills": ["skill1", "skill2"],
        "empresa": "nombre_empresa" | null,
        "rango_temporal": "rango_o_año" | null,
        "conector_temporal": "conector" | null
    }}
    """
    # Instanciamos el modelo y hacemos la llamada.
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.05)
    response = model.invoke([HumanMessage(content=prompt)])
    
    # Parse el json de la respuesta, ya que si bien se pide un json, el formato no siempre es correcto.
    try:

        # Remuevo los markers de codigo si los hay.
        content = response.content.strip()
        if content.startswith('```'):
            # Remuevo los markers de codigo.
            content = content.strip('`')
            # Remuevo el label 'json' si lo hay.
            if content.startswith('json'):
                content = content[4:]
            content = content.strip()
        response_json = json.loads(content)
        selection_tipo = response_json.get("tipo", "")
        selection_topic = response_json.get("topic", "")
        selection_emotion = response_json.get("emotion", "")
        selection_skills = response_json.get("skills", [])
        selection_empresa = response_json.get("empresa", None)
        selection_rango_temporal = response_json.get("rango_temporal", None)
        selection_conector_temporal = response_json.get("conector_temporal", None)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        selection_tipo = selection_topic = selection_emotion = ""
        selection_skills = []
        selection_empresa = selection_rango_temporal = selection_conector_temporal = None
    
    # Normalizar skills extraídos
    normalized_skills = normalize_skills(selection_skills)
    
    print(f"[DETECTOR] Tipo: {selection_tipo} | Skills: {normalized_skills} | Empresa: {selection_empresa} | Rango: {selection_rango_temporal} | Conector: {selection_conector_temporal}")

    return {
        "detector": {
            "tipo": selection_tipo,
            "topic": selection_topic,
            "emotion": selection_emotion,
            "skills": normalized_skills,
            "empresa": selection_empresa,
            "rango_temporal": selection_rango_temporal,
            "conector_temporal": selection_conector_temporal
        }
    }

def temporal_node(state: State) -> dict:
    """Extrae información temporal del JSON y determina qué experiencias son relevantes."""

    # Extraigo el tipo de consulta del detector.
    detector = state.get("detector", {})
    tipo_consulta = detector.get("tipo", "factual")
    
    # Si no es temporal, retornar vacío.
    if tipo_consulta != "temporal":
        return {"temporal_info": "", "temporal_filters": {}}
    

    # Cargar experiencias temporales. En este caso cargo todo porque el json es pequeño.
    try:
        temporal_path = "/Users/laviejave/Dropbox/Santex/repo_entrega/data_ing/Factica/temporal_experience.json"
        with open(temporal_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            experiencias_temporales = data.get("experiencia_laboral", [])
    except FileNotFoundError:
        print("[TEMPORAL] No se encontró el archivo temporal_experience.json")
        return {"temporal_info": "", "temporal_filters": {}}
    
    # Extraer filtros del detector
    skills = detector.get("skills", [])
    empresa = detector.get("empresa", None)
    rango_temporal = detector.get("rango_temporal", None)
    conector_temporal = detector.get("conector_temporal", None)
    
    
    # Aplicar reglas temporales si hay conector. Ver el helper_temporal.py para mas detalles.
    if conector_temporal:
        experiencias_temporales = aplicar_regla_temporal(
            experiencias_temporales, 
            conector_temporal, 
            rango_temporal, 
            empresa
        )
    
    # Usar directamente las experiencias filtradas por reglas temporales
    experiencias_filtradas = experiencias_temporales

    # Construir información temporal para el siguiente nodo.
    temporal_info = ""
    if experiencias_filtradas:
        temporal_info = "Experiencias laborales relevantes:\n"
        for exp in experiencias_filtradas:  #
            empresa_exp = exp.get("empresa", "")
            periodo = exp.get("periodo", "")
            rol = exp.get("rol", "")
            skills_exp = exp.get("skills", [])
            
            temporal_info += f"- {empresa_exp} ({rol}, {periodo}): {', '.join(skills_exp[:3])}\n"
    else:
        temporal_info = "No se encontraron experiencias laborales relevantes."
    

    
    return {
        "temporal": temporal_info
        }
    

def factual_node(state: State) -> dict:
    """Extrae información factual usando Pinecone. Filtra por skills y empresa para no pasar toda la DB"""
    query = state["messages"][-1].content
    detector = state.get("detector", {})
    skills = detector.get("skills", [])
    empresa = detector.get("empresa", None)
    
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index("Nombre_de_la_DB")
        
        # Crear embedding de la pregunta
        embedding = openai.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        ).data[0].embedding
        
        # Construir filtros para Pinecone
        filter_dict = {}
        if empresa:
            filter_dict["empresa"] = {"$eq": empresa}
        if skills:
            # Si hay skills específicos, filtrar por ellos
            filter_dict["skill"] = {"$in": skills}
        
        # Buscar en Pinecone con filtros
        results = index.query(
            vector=embedding,
            top_k=10,
            include_metadata=True,
            filter=filter_dict if filter_dict else None
        )
        
        if results.matches:
            factual_info = "Experiencias laborales relevantes:\n"
            for match in results.matches:
                metadata = match.metadata
                empresa = metadata.get("empresa", "")
                rol = metadata.get("rol", "")
                periodo = metadata.get("periodo", "")
                skill = metadata.get("skill", "")
                score = match.score
                
                factual_info += f"- {empresa} ({rol}, {periodo}): {skill} (relevancia: {score:.2f})\n"
            print(f"[FACTUAL] Información encontrada en Pinecone:\n{factual_info}")
            return {"factual": factual_info}
        else:
            print("[FACTUAL] No se encontraron resultados en Pinecone")
            return {"factual": "No se encontraron experiencias laborales relevantes para tu consulta."}
            
    except Exception as e:
        print(f"[FACTUAL] Error con Pinecone: {e}")
        return {"factual": "No se pudo recuperar información factual en este momento."}



def personality_node(state: State) -> dict:
    """Devuelve OCEAN promedio y ejemplos de tono aleatorios.
    En esta versiond el PoC se pasan ejemplos random hasta tener la Db en pinecone"""
    user_question = state["messages"][-1].content
 

    ocean_promedio = {
        "openness": 0.566,
        "conscientiousness": 0.505,
        "extraversion": 0.494,
        "agreeableness": 0.366,
        "neuroticism": 0.598
    }

    try:
        with open("data_ing/Factica/db_personality/faiss_metadata.json", "r", encoding="utf-8") as f:
            metadata = json.load(f)
        textos = [m.get("texto", "") for m in metadata if m.get("texto")]
        ejemplos = random.sample(textos, min(3, len(textos))) if textos else []
        personality_example = "\n---\n".join(ejemplos) if ejemplos else "¡Hola! Si necesitas ayuda, decímelo directo. Me gusta ser claro y concreto, pero siempre con buena onda."
    except Exception as e:
        print(f"[PERSONALITY] Error cargando ejemplos: {e}")
        personality_example = "¡Hola! Si necesitas ayuda, decímelo directo. Me gusta ser claro y concreto, pero siempre con buena onda."

    personalidad = "Nico, tono promedio"
    response = f"(Tono: {personalidad})\nEjemplos de estilo:\n{personality_example}"

    return {
        "personality": personalidad,
        "personality_response": response,
        "personality_ocean": ocean_promedio,
        "personality_example": personality_example
    }

def response_node(state: State) -> dict:

    #Recopilo toda la info que tengo para el prompt.
    factual_info = state.get("factual", "")
    temporal_info = state.get("temporal", "")
    personality = state.get("personality", "")
    personality_ocean = state.get("personality_ocean", None)
    personality_example = state.get("personality_example", None)
    user_question = state["messages"][-1].content if state["messages"] else ""

    # Ejemplo por defecto si no hay uno real
    default_example = "¡Hola! Si necesitas ayuda, decímelo directo. Me gusta ser claro y concreto, pero siempre con buena onda."
    if not personality_example:
        personality_example = default_example

    # Explicación de OCEAN para la LLM
    ocean_explanation = """
Los valores OCEAN representan rasgos de personalidad:
- O (Apertura a la experiencia): alto = creativo, curioso; bajo = tradicional, práctico
- C (Responsabilidad): alto = organizado, cumplidor; bajo = flexible, desordenado
- E (Extraversión): alto = sociable, expresivo; bajo = reservado, tranquilo
- A (Amabilidad): alto = empático, cooperativo; bajo = directo, competitivo
- N (Neuroticismo): alto = emocional, sensible; bajo = estable, calmado
Ajusta el tono de la respuesta según estos valores.
"""

    prompt = f"""Eres Nico. Responde como lo haría él, usando SOLO la información proporcionada.

Pregunta: {user_question}

Información disponible:
- Factual: {factual_info}
- Temporal: {temporal_info}

Ejemplo de estilo de Nico: {personality_example}, {personality}

{ocean_explanation}
Valores OCEAN: {personality_ocean}

Reglas:
- Si no hay información relevante, di cortésmente que no puedes responder
- NO inventes información
- Usa solo los datos proporcionados
- Mantén el estilo del ejemplo
- Ajusta el tono según los valores OCEAN
- No contestes en neutral. Contesta como argentino, pero sin lunfardo

Respuesta:"""

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.05)
    response = model.invoke([HumanMessage(content=prompt)]).content.strip()

    print(f"🤖 {response}")
    return {
        "response": response
    }



# Constuimos los nodos y edges.
builder = StateGraph(State)
builder.add_node("detector_node", detector_node)
builder.add_node("temporal_node", temporal_node)
builder.add_node("factual_node", factual_node)
builder.add_node("personality_node", personality_node)
builder.add_node("response_node", response_node)

# edges
builder.add_edge(START, "detector_node")
builder.add_edge("detector_node", "temporal_node")
builder.add_edge("temporal_node", "factual_node")
builder.add_edge("factual_node", "personality_node")
builder.add_edge("personality_node", "response_node")
builder.add_edge("response_node", END)

graph = builder.compile()