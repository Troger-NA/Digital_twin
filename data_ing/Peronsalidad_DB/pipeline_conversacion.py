import os
import json
from datetime import datetime, timedelta
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
import torch.nn.functional as F
import pandas as pd
from tqdm import tqdm

### Configurro los modelos ###

# Emoción
EMO_MODEL = "finiteautomata/beto-emotion-analysis"
emo_tokenizer = AutoTokenizer.from_pretrained(EMO_MODEL)
emo_model = AutoModelForSequenceClassification.from_pretrained(EMO_MODEL)
emo_labels = emo_model.config.id2label

# Big Five
BF_MODEL = "Minej/bert-base-personality"
bf_tokenizer = AutoTokenizer.from_pretrained(BF_MODEL)
bf_model = AutoModelForSequenceClassification.from_pretrained(BF_MODEL)
bf_labels = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']

# Temas (zero-shot)
TOPIC_MODEL = "facebook/bart-large-mnli"
topic_classifier = pipeline("zero-shot-classification", model=TOPIC_MODEL)
TOPIC_LABELS = [
    "trabajo", "amistad", "familia", "salud", "emociones", 
    "ocio", "estudios", "dinero", "viajes", "tecnología",
    "deportes", "comida", "política", "entretenimiento", "amor"
]

### Filtro mensajes triviales (cortos) ###

def filtrar_mensajes_triviales(mensajes, min_len=6):
    return [m for m in mensajes if len(m["mensaje"].strip()) >= min_len and m["mensaje"].strip().lower() not in ["ok", "dale", "jaja", "👍", "👌", "no", "sí", "si"]]



### Agrupo por conversdacion ###
def segmentar_conversaciones_por_dia_y_gap(mensajes, horas_gap=5):
    """
    Agrupa mensajes por conversacion.
    Args:
        mensajes (list): Lista de mensajes.
        horas_gap (int): Gap de horas para nueva conversacion.
   Uso pandas por ser un dataset pequeño.
    """

    df = pd.DataFrame(mensajes)
    # Creo la columna de fecha y hora
    df["datetime"] = pd.to_datetime(df["fecha"] + " " + df["hora"])
    df = df.sort_values("datetime").reset_index(drop=True)
    df["conv_id"] = 0
    
    #inicializo el id de la conversacion
    actual_id = 0
    for i in range(1, len(df)):
        t_actual = df.loc[i, "datetime"]
        t_anterior = df.loc[i - 1, "datetime"]
        #Condicion de salto de dia
        cambio_dia = t_actual.date() != t_anterior.date()
        #Condicion de gap de horas
        gap_grande = (t_actual - t_anterior) > timedelta(hours=horas_gap)
        if cambio_dia and gap_grande:
            actual_id += 1
        df.loc[i, "conv_id"] = actual_id
    conversaciones = []
    
    #Creo el diccionario de conversaciones
    for cid, grupo in df.groupby("conv_id"):
        mensajes = []
        for _, row in grupo.iterrows():
            mensajes.append({
                "remitente": row["remitente"],
                "mensaje": row["mensaje"],
                "datetime": str(row["datetime"])
            })
        conversaciones.append({
            "conversacion_id": int(cid),
            "inicio": str(grupo.iloc[0]["datetime"]),
            "fin": str(grupo.iloc[-1]["datetime"]),
            "remitentes": list(grupo["remitente"].unique()),
            "mensajes": mensajes
        })
    return conversaciones



### Analisis de emocion, tema y bigfice por conversacion ###
def analizar_emocion(texto):
    try:
        inputs = emo_tokenizer(texto, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            logits = emo_model(**inputs).logits
            probs = F.softmax(logits, dim=-1)[0]
            idx = torch.argmax(probs).item()
            if idx < len(emo_labels):
                return {"emo_user": emo_labels[idx], "emo_score": round(probs[idx].item(), 3)}
            else:
                return {"emo_user": "unknown", "emo_score": 0.0}
    except Exception:
        return {"emo_user": "unknown", "emo_score": 0.0}

def analizar_tema(texto):
    try:
        if not texto.strip():
            return {"tema": "otros", "tema_score": 0.0}
        resultado = topic_classifier(texto, candidate_labels=TOPIC_LABELS, multi_label=False)
        return {"tema": resultado['labels'][0], "tema_score": round(resultado['scores'][0], 3)}
    except Exception:
        return {"tema": "otros", "tema_score": 0.0}

def analizar_bigfive(texto):
    try:
        inputs = bf_tokenizer(texto, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            logits = bf_model(**inputs).logits
            probs = torch.sigmoid(logits)[0]
            return {f"bf_{trait.lower()}": round(probs[i].item(), 3) for i, trait in enumerate(bf_labels)}
    except Exception:
        return {f"bf_{trait.lower()}": 0.5 for trait in bf_labels}




# ========== Pipeline principal al ejecutar ==========
def main(input_json, output_json, min_len=6, horas_gap=5):
    """
    Pipeline principal al ejecutar el script.
    Args:
        input_json (str): Archivo JSON de mensajes (anonimizados y parseados).
        output_json (str): Archivo de salida JSON por conversación.
        min_len (int): Longitud mínima de mensaje para considerar.
        el resultado es un json por conversacion con los siguientes campos:
        - conversacion_id: id de la conversacion.
        - remitentes: lista de remitentes.
        - fecha_inicio: fecha de inicio de la conversacion.
        - fecha_fin: fecha de fin de la conversacion.
        - num_mensajes: numero de mensajes.
        - texto: texto de la conversacion.
        
        """
    with open(input_json, "r", encoding="utf-8") as f:
        mensajes = json.load(f)
    mensajes_filtrados = filtrar_mensajes_triviales(mensajes, min_len=min_len)
    conversaciones = segmentar_conversaciones_por_dia_y_gap(mensajes_filtrados, horas_gap=horas_gap)
    resultados = []
    for conv in tqdm(conversaciones, desc="Analizando conversaciones"):
        # Concatenar texto con remitente
        texto = " ".join([f"{m['remitente']}: {m['mensaje']}" for m in conv["mensajes"]])
        analisis_emo = analizar_emocion(texto)
        analisis_tema = analizar_tema(texto)
        analisis_bf = analizar_bigfive(texto)
        resultado = {
            "conversacion_id": conv["conversacion_id"],
            "remitentes": conv["remitentes"],
            "fecha_inicio": conv["inicio"],
            "fecha_fin": conv["fin"],
            "num_mensajes": len(conv["mensajes"]),
            "texto": texto,
            **analisis_emo,
            **analisis_tema,
            **analisis_bf
        }
        resultados.append(resultado)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"✅ Guardado: {output_json} ({len(resultados)} conversaciones)")

if __name__ == "__main__":
    import argparse

    # Parseo los argumentos. Es prescindible.
    parser = argparse.ArgumentParser(description="Pipeline simple por conversación (filtra, agrupa, analiza)")
    parser.add_argument("--input_json", required=True, help="Archivo JSON de mensajes (anonimizados y parseados)")
    parser.add_argument("--output_json", required=True, help="Archivo de salida JSON por conversación")
    parser.add_argument("--min_len", type=int, default=6, help="Longitud mínima de mensaje para considerar")
    parser.add_argument("--horas_gap", type=int, default=5, help="Gap de horas para nueva conversación")
    args = parser.parse_args()
    main(args.input_json, args.output_json, min_len=args.min_len, horas_gap=args.horas_gap) 