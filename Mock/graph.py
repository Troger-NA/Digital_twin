import langgraph
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables import RunnablePassthrough
from typing import TypedDict, Annotated
import random

# Define the state with messages
class State(TypedDict):
    messages: Annotated[list, add_messages]
    detector: str
    temporal: str
    factual: str
    personality: str
    response: str

def detector_node(state: State) -> dict:
    """Detecta si la pregunta del input es de tipo factual, o sobre un evento temporal.
    Detecta topico y emoción"""
    examples_tipo = ["factual", "temporal", "ambos"]
    examples_topic = ["finanzas", "salud", "educacion", "tecnologia", "politica", "deportes", "entretenimiento", "otros"]
    examples_emotion = ["positivo", "negativo", "neutral", "ira", "tristeza", "alegria", "sorpresa", "miedo", "disgusto", "confianza"]

    selection_tipo = random.choice(examples_tipo)
    selection_topic = random.choice(examples_topic)
    selection_emotion = random.choice(examples_emotion)

    return {
        "detector": {
            "tipo": selection_tipo,
            "topic": selection_topic,
            "emotion": selection_emotion
        }
    }

def temporal_node(state: State) -> dict:
    """Busca los eventos temporales en la DB. Tiene que ser determinista."""
    return {"temporal": "Información temporal de la base de datos"}

def factual_node(state: State) -> dict:
    """Hace RAG sobre la base de datos factuales"""
    examples = ["Se el skill A", "Se el skill B", "Se el skill C", "Se el skill D"]
    selection = random.choice(examples)
    return {"factual": selection}

def personality_node(state: State) -> dict:
    """Extrae el topico y el tono del user, y devuelve la personalidad de nico"""
    examples_topic = ["finanzas", "salud", "educacion", "tecnologia", "politica", "deportes", "entretenimiento", "otros"]
    examples_emotion = ["positivo", "negativo", "neutral", "ira", "tristeza", "alegria", "sorpresa", "miedo", "disgusto", "confianza"]
    
    examples_personalidad = ["Empatico y formal", "Empatico e informal", "Profesional y formal", "Profesional e informal", "Amigable y formal", "Amigable e informal"]
    personality = random.choice(examples_personalidad)
    return {"personality": personality}

def response_node(state: State) -> dict:
    """Genera la respuesta de nico"""
    factual_info = state.get("factual", "")
    temporal_info = state.get("temporal", "")
    personality = state.get("personality", "")
    
    # Get the user's question from the last message
    user_question = state["messages"][-1].content if state["messages"] else ""

    prompt = f"""
    Eres un gemelo digital de Nico. Te haran una pregunta y tendras que responder como el lo haria.
    Usaras la base factual y la linea de tiempo para responder la pregunta segun corresponda.
    La respuesta debe ser como lo haria nico segun su personalidad.
    Pregunta: {user_question}
    Base factual: {factual_info}
    Linea de tiempo: {temporal_info}
    Personalidad: {personality}
    """
    
    response = f"Respuesta del clon digital de Nico (Personalidad: {personality}): Basándome en la información factual '{factual_info}' y temporal '{temporal_info}', te respondo que..."

    return {
        "response": response
    }

def route_after_detector(state: State) -> str:
    """Router que determina si ir a temporal_node o directamente a factual_node"""
    detector = state.get("detector", {})
    tipo = detector.get("tipo", "factual")
    
    if tipo == "temporal":
        return "temporal_node"
    else:
        return "factual_node"

# Build the graph
builder = StateGraph(State)
builder.add_node("detector_node", detector_node)
builder.add_node("temporal_node", temporal_node)
builder.add_node("factual_node", factual_node)
builder.add_node("personality_node", personality_node)
builder.add_node("response_node", response_node)

# Add edges
builder.add_edge(START, "detector_node")
builder.add_conditional_edges(
    "detector_node",
    route_after_detector,
    {
        "temporal_node": "temporal_node",
        "factual_node": "factual_node"
    }
)
builder.add_edge("temporal_node", "factual_node")
builder.add_edge(START, "personality_node")
builder.add_edge("personality_node", "response_node")
builder.add_edge("factual_node", "response_node")
builder.add_edge("response_node", END)

graph = builder.compile()
