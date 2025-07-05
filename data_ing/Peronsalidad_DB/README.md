# Procesamiento y Análisis de Conversaciones de WhatsApp para extraer personalidad

## Estructura del flujo

1. **Coloca los archivos de texto exportados de WhatsApp** en las carpetas `formal/` o `informal/` según corresponda.
2. **Ejecuta el procesamiento por lote:**

```bash
python main.py
```

Esto realiza automáticamente:
- Parseo de los archivos `.txt` de cada carpeta. (funciones en parser.py)
- Anonimización (curado) de los mensajes (mails, teléfonos, palabras sensibles, etc.). (funciones en parser.py)
- Guardado de los mensajes anonimizados en archivos `*_parsed_anon.json`.
- Ejecución del pipeline de análisis por conversación, que agrupa, filtra y analiza los mensajes, generando archivos `*_conversaciones_analizadas.json`. (Ejecuta pipeline_conversacion.py)

## Ejemplo de conversación (formato WhatsApp)

El archivo de entrada debe tener líneas como:

```
[12/5/23 14:32:10] Juan Perez: Hola, ¿cómo estás?
[12/5/23 14:32:15] Maria Lopez: Todo bien, ¿y vos?
[12/5/23 14:32:20] Juan Perez: Bien también, gracias.
```

Cada línea representa un mensaje, con el siguiente formato:

```
[DD/MM/AA HH:MM:SS] Remitente: Mensaje
```

## Salidas generadas

- `*_parsed_anon.json`: Mensajes anonimizados.
- `*_conversaciones_analizadas.json`: Análisis por bloque de conversación (emociones, temas, Big Five, etc.).

## Ejemplo de salida: conversación analizada

Un bloque típico en un archivo `*_conversaciones_analizadas.json` luce así:

```json
{
    "conversacion_id": 0,
    "remitentes": [
      "Nico",
      "juan doe"
    ],
    "fecha_inicio": "2020-08-15 11:57:09",
    "fecha_fin": "2020-08-15 23:43:44",
    "num_mensajes": 24,
    "texto": "Conversacion ...",
    "emo_user": "others",
    "emo_score": 0.886,
    "tema": "viajes",
    "tema_score": 0.166,
    "bf_openness": 0.588,
    "bf_conscientiousness": 0.498,
    "bf_extraversion": 0.463,
    "bf_agreeableness": 0.317,
    "bf_neuroticism": 0.598
}
```

## Ejemplo de salida: matrices promedio por grupo

Una entrada típica en `matrices_promedio_por_grupo.json` (por ejemplo, agrupando por tema y emoción) es:

```json
"('familia', 'anger')": {
  "bf_openness": 0.566,
  "bf_conscientiousness": 0.505,
  "bf_extraversion": 0.494,
  "bf_agreeableness": 0.366,
  "bf_neuroticism": 0.598
}
```

Esto indica el promedio de los rasgos Big Five para todas las conversaciones clasificadas con tema "familia" y emoción "anger".

## Vectorización y reducción de dimensionalidad

Finalmente, una vez generados los archivos `*_conversaciones_analizadas.json`, es posible vectorizar la información textual de cada bloque/conversación utilizando modelos de embeddings (por ejemplo, con `sentence-transformers`).

Para ello, ejecuta el script correspondiente (por ejemplo, `vectorizar_bloques.py`):

```bash
python vectorizar_bloques.py
```

Este proceso:
- Convierte cada bloque de texto en un vector numérico de alta dimensión (embedding).
- Almacena los vectores y los metadatos asociados para análisis posteriores.
- Permite aplicar técnicas de reducción de dimensionalidad (como PCA) para visualizar los datos en 2D o 3D, facilitando la exploración y el análisis visual de las conversaciones.

De este modo, puedes analizar agrupamientos, similitudes y patrones en las conversaciones de manera eficiente y visual.

## Análisis simplificado de Big Five

Después de vectorizar y analizar las conversaciones, puedes calcular estadísticas agregadas de personalidad (Big Five) sobre los bloques de conversación.

Para ello, ejecuta:

```bash
python analisis_simplificado_conversaciones.py
```

Este script genera dos archivos principales:

- **`promedio_bigfive_global.json`**: contiene el promedio global de los cinco rasgos de personalidad (Big Five) calculado sobre todos los bloques de conversación. Es útil como referencia general del corpus.
- **`matrices_promedio_por_grupo.json`**: contiene matrices de promedios de Big Five agrupadas por diferentes criterios:
  - Por tema
  - Por emoción
  - Por formalidad (carpeta)
  - Por combinación de tema y emoción

Cada matriz te permite comparar cómo varían los rasgos de personalidad según el grupo o contexto conversacional. Las claves de los grupos pueden ser strings o tuplas (por ejemplo, `("amistad", "joy")`).

Estos archivos pueden ser usados para análisis estadístico, visualización o comparación entre distintos subconjuntos de conversaciones.

**Nota:** Este análisis simplificado está diseñado para trabajar con un conjunto reducido de datos como primera aproximación. Para conjuntos de datos más grandes o análisis más complejos, se puede usar dask para paralelizar, o trabajar directamente sobre los vectores, reduciendo via clustering.


