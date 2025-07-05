import os
import json
from collections import Counter, defaultdict
import numpy as np

"""
Este script analiza las conversaciones analizadas y calcula el promedio de Big Five de los bloques.

Esto es valido para primeras aproximaciones y datasets pequeños.
Para datasets grandes, se tiene que usar otro enfoque como paralelizar en dask y usar chunks.

"""



folders = ["formal", "informal"]
all_blocks = []
blocks_by_folder = defaultdict(list)

# 1. Leer todos los archivos *_conversaciones_analizadas.json
def cargar_bloques():
    for folder in folders:
        if not os.path.exists(folder):
            continue
        for fname in os.listdir(folder):
            if fname.endswith("_conversaciones_analizadas.json"):
                path = os.path.join(folder, fname)
                with open(path, "r", encoding="utf-8") as f:
                    bloques = json.load(f)
                    all_blocks.extend(bloques)
                    blocks_by_folder[folder].extend(bloques)

def promedio_bigfive(bloques):
    """
    Calcula el promedio de Big Five de los bloques. Util para primeras aproximaciones.
    Args:
        bloques (list): Lista de bloques.
    Returns:
        dict: Diccionario con el promedio de Big Five.
    """

    keys = ["bf_openness", "bf_conscientiousness", "bf_extraversion", "bf_agreeableness", "bf_neuroticism"]
    arr = np.array([[b.get(k, 0.0) for k in keys] for b in bloques if all(k in b for k in keys)])
    if len(arr) == 0:
        return {k: 0.0 for k in keys}
    return dict(zip(keys, np.round(arr.mean(axis=0), 3)))

def matriz_promedio_por_grupo(bloques, group_keys):
    """
    Calcula el promedio de Big Five agrupando por las claves indicadas (ej: ['tema'], ['emo_user'], ['tema','emo_user'], etc.)
    Devuelve un dict: {grupo: {bf_openness:..., ...}}
    """
    from collections import defaultdict
    keys = ["bf_openness", "bf_conscientiousness", "bf_extraversion", "bf_agreeableness", "bf_neuroticism"]
    grupos = defaultdict(list)
    for b in bloques:
        if all(k in b for k in keys) and all(gk in b for gk in group_keys):
            grupo = tuple(b[gk] for gk in group_keys)
            grupos[grupo].append([b[k] for k in keys])
    matriz = {}
    for grupo, vals in grupos.items():
        arr = np.array(vals)
        avg = np.round(arr.mean(axis=0), 3)
        matriz[grupo] = dict(zip(keys, avg))
    return matriz

def stringify_keys(d):
    return {str(k): v for k, v in d.items()}

if __name__ == "__main__":
    cargar_bloques()
    # Matriz promedio global
    promedio_global = promedio_bigfive(all_blocks)
    with open("promedio_bigfive_global.json", "w", encoding="utf-8") as f:
        json.dump(promedio_global, f, indent=2, ensure_ascii=False)
    print("✅ Promedio Big Five global guardado en promedio_bigfive_global.json")

    # Matrices promedio por grupo
    matrices = {
        "por_tema": matriz_promedio_por_grupo(all_blocks, ["tema"]),
        "por_emocion": matriz_promedio_por_grupo(all_blocks, ["emo_user"]),
        "por_formalidad": matriz_promedio_por_grupo(all_blocks, ["carpeta"] if "carpeta" in all_blocks[0] else []),
        "por_tema_emocion": matriz_promedio_por_grupo(all_blocks, ["tema", "emo_user"])
    }
    matrices = {k: stringify_keys(v) for k, v in matrices.items()}
    with open("matrices_promedio_por_grupo.json", "w", encoding="utf-8") as f:
        json.dump(matrices, f, indent=2, ensure_ascii=False)
    print("✅ Matrices promedio por grupo guardadas en matrices_promedio_por_grupo.json") 