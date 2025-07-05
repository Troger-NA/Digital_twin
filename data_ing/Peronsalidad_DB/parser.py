import re
from datetime import datetime
import pandas as pd



def parse_whatsapp(file_path, chat_tag="Informal"):
    """
    Parsea un archivo de WhatsApp y devuelve una lista de mensajes.
    El Pattern surge del formato de los chats: [12/5/23 14:32:10] Juan Perez: Hola, ¿cómo estás?
    Args:
        file_path (str): La ruta al archivo de WhatsApp.
        chat_tag (str): El tag del chat.


    """
    
    pattern = r"\[(\d{1,2}/\d{1,2}/\d{2,4}) (\d{1,2}:\d{2}:\d{2})\] ([^:]+): (.+)"
    parsed_messages = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(pattern, line)
            if match:
                fecha_raw, hora, remitente, mensaje = match.groups()

                # Formato standard de fecha
                try:
                    fecha = datetime.strptime(fecha_raw, "%d/%m/%y").strftime("%Y-%m-%d")
                except ValueError:
                    fecha = datetime.strptime(fecha_raw, "%d/%m/%Y").strftime("%Y-%m-%d")

                # Omitir mensajes automáticos
                if "cifrados de extremo a extremo" in mensaje.lower():
                    continue

                parsed_messages.append({
                    "fecha": fecha,
                    "hora": hora,
                    "remitente": remitente,
                    "mensaje": mensaje.strip(),
                    "chat_tag": chat_tag
                })

    return parsed_messages



# Carga modelo SpaCy (español)
#nlp = spacy.load("es_core_news_md")  # o 'sm' si no tenés espacio

# Palabras clave para censura temática
CENSURA_CATEGORIAS = {
    "discriminación": ["insertar palabras"],
    "política": ["insertar palabras"],
    "religión": ["insertar palabras"],
    "sexual": ["insertar palabras"]
}

def anonimizar_texto(texto: str) -> str:
    """
    Anonimiza un texto reemplazando entidades personales, mails y teléfonos, y censurando palabras temáticas.
    Args:
        texto (str): El texto a curar.
    Returns:
        str: El texto curado.
    """
    texto = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', '[EMAIL]', texto)
    texto = re.sub(r'\b\d{8,15}\b', '[TELEFONO]', texto)

    for categoria, palabras in CENSURA_CATEGORIAS.items():
        for palabra in palabras:
            texto = re.sub(rf'\b{palabra}\b', f"[CENSURADO_{categoria.upper()}]", texto, flags=re.IGNORECASE)

    return texto


