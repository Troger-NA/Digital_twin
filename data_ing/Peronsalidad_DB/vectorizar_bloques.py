import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer

"""
Este script vectoriza los bloques de texto de las conversaciones analizadas.
Mucho cuidado con el modelo de embeddings y la dimensionalidad.
Corroborar que la dimensionalidad es la misma que cuando se haga el RAG


"""


# 1. Cargar modelo de embeddings (cambiar por uno de 1536 dimensiones!!")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 2. Leer todos los bloques
folders = ["formal", "informal"]
all_blocks = []
for folder in folders:
    if not os.path.exists(folder):
        continue
    for fname in os.listdir(folder):
        if fname.endswith("_conversaciones_analizadas.json"):
            with open(os.path.join(folder, fname), "r", encoding="utf-8") as f:
                all_blocks.extend(json.load(f))

# 3. Vectorizar cada bloque
embeddings = []
metadata = []
for bloque in all_blocks:
    texto = bloque["texto"]
    emb = model.encode(texto)
    embeddings.append(emb)

    #recorro las claves k y valores v del diccionario e incluyo la metadata que no sea texto (convversacion)
    meta = {k: v for k, v in bloque.items() if k != "texto"}
    metadata.append(meta)

# 4. Guardar embeddings y metadata
np.save("embeddings.npy", np.array(embeddings))
with open("metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print(f"Listo: {len(embeddings)} bloques vectorizados y guardados.") 