import os
import subprocess
import json
from parser import parse_whatsapp, anonimizar_texto

""" siempre que se lea anon, hace referencia al texto curado (anonimizado)"""


folders = ["formal", "informal"]

for folder in folders:
    if not os.path.exists(folder):
        print(f"Carpeta no encontrada: {folder}")
        continue
    txt_files = [fname for fname in os.listdir(folder) if fname.endswith(".txt")]
    for fname in txt_files:
        #Creo la rutas I/O
        input_path = os.path.join(folder, fname)
        base = fname.replace(".txt", "")
        parsed_anon_path = os.path.join(folder, f"{base}_parsed_anon.json")
        
        # 1. Parsear
        print(f"Parseando {input_path} ...")
        mensajes = parse_whatsapp(input_path, chat_tag=folder.capitalize())

        # 2. Anonimizar (curar)
        for m in mensajes:
            m["mensaje"] = anonimizar_texto(m["mensaje"])
        
        # 3. Guardar anonimizados
        with open(parsed_anon_path, "w", encoding="utf-8") as f:
            json.dump(mensajes, f, indent=2, ensure_ascii=False)
        print(f"Guardado {parsed_anon_path} ({len(mensajes)} mensajes)")
        
        
        # 4.Ejecuto el pipleine de analisis de conversaciones.
        """
        El pipeline se encarga de:
        - Filtrar mensajes triviales (menos de 6 caracteres)
        - Agrupar mensajes por conversacion (por dia y gap de 5 horas)
        - Analizar emociones, temas y big five de cada conversacion
        - Guardar los resultados en un archivo JSON.
        
        """
        
        output_path = os.path.join(folder, f"{base}_conversaciones_analizadas.json")
        print(f"Analizando conversaciones en {parsed_anon_path} ...")
        subprocess.run([
            "python", "pipeline_conversacion.py",
            "--input_json", parsed_anon_path,
            "--output_json", output_path
        ])
print("✅ Procesamiento por lote finalizado.") 