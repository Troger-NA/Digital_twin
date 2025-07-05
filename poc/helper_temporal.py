import re

def parse_periodo(periodo_str: str) -> tuple:
    """
    Parsea un string de período y devuelve (año_inicio, año_fin)
    Este parsing se debe eliminar si el json de experiencias laborales se arma de forma homogenea
    """
    # Patrones comunes de fechas.
    patterns = [
        r'(\d{4})\s*–\s*(\d{4})',  # Fecha1 – Fecha2
        r'(\d{4})\s*-\s*(\d{4})',  # Fecha1-Fecha2
        r'(\d{4})\s*–\s*Presente',  # Fecha1 – Presente
        r'(\d{4})\s*-\s*Presente',  # Fecha1-Presente
        r'(\d{4})',  # Solo año
    ]
    for pattern in patterns:
        match = re.search(pattern, periodo_str)
        if match:
            if len(match.groups()) == 2:
                return (int(match.group(1)), int(match.group(2)))
            else:
                return (int(match.group(1)), int(match.group(1)))
    return (None, None)

def get_empresa_periodo(empresa_nombre: str, experiencias: list) -> tuple:
    """
    Busca el período de una empresa específica
    """
    for exp in experiencias:
        if exp.get("empresa", "").lower() == empresa_nombre.lower():
            periodo = exp.get("periodo", "")
            return parse_periodo(periodo)
    return (None, None)

def aplicar_regla_temporal(experiencias: list, conector: str, rango_temporal: str, empresa: str) -> list:
    """
    Aplica reglas temporales sobre una lista de experiencias laborales para filtrar según conectores y referencias temporales.

    Espera que cada experiencia tenga al menos los campos:
        - 'empresa': nombre de la empresa (str)
        - 'periodo': string con el rango de años (ej: '2019 – 2024', '2020', '2018 – Presente')

    Parámetros:
        experiencias (list): Lista de dicts con experiencias laborales.
        conector (str): Conector temporal detectado en la consulta del usuario. Ejemplos: 'antes', 'después', 'desde', 'hasta', 'durante'.
        rango_temporal (str): Año o rango temporal extraído de la consulta (ej: '2020', '2017-2019'). Puede ser None.
        empresa (str): Nombre de la empresa de referencia si se menciona en la consulta. Puede ser None.

    Lógica:
        - Si hay conector y empresa, busca el período de esa empresa y lo usa como referencia temporal.
        - Si hay un año/rango explícito, lo usa como referencia temporal.
        - Si no hay referencia temporal, devuelve la lista original (sin filtrar).
        - Filtra las experiencias según el conector:
            * 'antes': experiencias que comienzan antes del año de referencia
            * 'después': experiencias que comienzan después del año de referencia
            * 'desde': experiencias que comienzan en o después del año de referencia
            * 'hasta': experiencias que terminan en o antes del año de referencia
            * 'durante': experiencias que incluyen el año de referencia en su rango

    Devuelve:
        list: Subconjunto de experiencias que cumplen la condición temporal.
    """
    # Extraer año del rango temporal si existe
    año_específico = None
    if rango_temporal:
        año_match = re.search(r'(\d{4})', rango_temporal)
        if año_match:
            año_específico = int(año_match.group(1))
    # Determinar el año de referencia
    año_referencia = None
    if conector and empresa:
        # Caso: "después de meton"
        año_inicio, año_fin = get_empresa_periodo(empresa, experiencias)
        if año_fin:
            año_referencia = año_fin
        elif año_inicio:
            año_referencia = año_inicio
    elif año_específico:
        # Caso: "antes de 2017"
        año_referencia = año_específico
    if not año_referencia:
        return experiencias  # Sin filtro temporal
    
    # Aplicar filtro según conector
    experiencias_filtradas = []
    for exp in experiencias:
        periodo = exp.get("periodo", "")
        año_inicio, año_fin = parse_periodo(periodo)
        if not año_inicio:
            continue
        if conector == "antes":
            if año_inicio < año_referencia:
                experiencias_filtradas.append(exp)
        elif conector == "después":
            if año_inicio > año_referencia:
                experiencias_filtradas.append(exp)
        elif conector in ["durante", "en", "durante el"]:
            # Para "en 2020" o "durante 2020", buscar experiencias que incluyan ese año
            if año_inicio <= año_referencia <= (año_fin or año_inicio):
                experiencias_filtradas.append(exp)
        elif conector == "desde":
            if año_inicio >= año_referencia:
                experiencias_filtradas.append(exp)
        elif conector == "hasta":
            if (año_fin or año_inicio) <= año_referencia:
                experiencias_filtradas.append(exp)
    return experiencias_filtradas 