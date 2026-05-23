# modulos/B_resultados.py

# modulos/B_resultados.py

import pandas as pd
import numpy as np
import networkx as nx
import geopandas as gpd
from typing import List, Dict, Tuple, Optional

from modulos.B_algoritmos import _filter_subgraph, _get_case_count, _create_graph_from_data, expansion_tree, floyd_warshall_routes, kruskal_mst_analysis
from modulos.utils import normalize_department_name, normalize_text

# --- Subtipos de Delito Focales para el Reporte Estratégico ---
CRIME_FOCUS_TYPES = ['EXTORSION', 'HOMICIDIO', 'SICARIATO']


def _sigla_distrito(nombre: str) -> str:
    tokens = [t for t in nombre.split() if t]
    if not tokens:
        return (nombre[:3] or "ND").upper()
    if len(tokens) == 1:
        return tokens[0][:3].upper()
    return "".join(token[0] for token in tokens[:3]).upper()


def _formatear_numero(valor: float) -> str:
    try:
        if isinstance(valor, (int, float)):
            return f"{valor:,}".replace(",", ".")
    except Exception:
        pass
    return str(valor)


def _preparar_datos_filtrados(df_delitos: pd.DataFrame, gdf_geo: gpd.GeoDataFrame, department: str) -> Tuple[pd.DataFrame, gpd.GeoDataFrame]:
    """
    Realiza el filtrado y normalización de DataFrames para asegurar la coincidencia de nombres
    antes de pasarlos a la función _create_graph_from_data.
    
    Esta función SOLUCIONA el problema de los 'ceros' al estandarizar los nombres de distritos.
    """
    # Normalización del departamento
    dept_norm = normalize_department_name(department)

    # 1. Filtrar GeoDataFrame por el departamento
    # Suponemos que la columna de departamento en el GDF es 'NOMBDEP'
    gdf_dep = gdf_geo[gdf_geo["NOMBDEP"].astype(str).apply(normalize_department_name) == dept_norm].copy()
    
    if gdf_dep.empty:
        print(f"Error: No se encontraron datos geográficos para {department}.")
        return pd.DataFrame(), gpd.GeoDataFrame()

    # ** PASO CRÍTICO: NORMALIZACIÓN DE GEOMETRÍA **
    gdf_dep = gdf_dep[gdf_dep.geometry.notna()].copy()

    # 2. Filtrar el DataFrame de Delitos
    # Suponemos que la columna de departamento en el DF es 'DPTO_HECHO_NEW'
    df_dep = df_delitos[df_delitos["DPTO_HECHO_NEW"].astype(str).apply(normalize_department_name) == dept_norm].copy()
    
    if df_dep.empty:
        print(f"Advertencia: El DataFrame de delitos filtrado por departamento está vacío para {department}.")
        return pd.DataFrame(), gdf_dep
    
    
    # Crea un set de nombres de distritos válidos del GDF
    gdf_dep['NOMBDIST_NORM'] = gdf_dep['NOMBDIST'].astype(str).apply(normalize_text)
    valid_districts = set(gdf_dep['NOMBDIST_NORM'])

    # Normaliza la columna 'DIST_HECHO' en el DF de delitos
    df_dep['DIST_HECHO_NORM'] = df_dep['DIST_HECHO'].astype(str).apply(normalize_text)
    
    # Filtra el DF de delitos para solo incluir distritos que existen en el GDF
    df_dep = df_dep[df_dep['DIST_HECHO_NORM'].isin(valid_districts)].copy()
    
    print(f"[INFO] Preparación de datos: {len(df_dep)} casos de delitos y {len(gdf_dep)} distritos listos.")
    
    return df_dep, gdf_dep


# === 1. FUNCIÓN DE CÁLCULO Y CONSOLIDACIÓN: consolidar_resultados ===


def consolidar_resultados(G_base: nx.Graph, department: str, epicentro: str) -> Dict:
    """
    Ejecuta todos los análisis de grafos y consolida los hallazgos.
    """
    print(f"\n==================== 1/3. INICIANDO CONSOLIDACIÓN DE RESULTADOS PARA {department.upper()} ====================")

    # 1. Filtro y Verificación (G_base ya debe ser el grafo del departamento)
    G_filtered = G_base # Asumimos que _create_graph_from_data ya creó el grafo filtrado
    
    if G_filtered.number_of_nodes() == 0:
        print("Advertencia: El grafo está vacío. No se puede generar el reporte.")
        return {}

    # 2. Ejecución de los Algoritmos de Grafo
    print("[INFO] Ejecutando algoritmos de análisis estructural...")
    # NOTA: Los algoritmos deben poder manejar grafos grandes y filtrar internamente
    bfs_stats = expansion_tree(G_base, epicentro, method='bfs', crime_types=CRIME_FOCUS_TYPES, department=department)
    fw_stats = floyd_warshall_routes(G_base, mode='volume', crime_types=CRIME_FOCUS_TYPES, department=department)
    kruskal_stats = kruskal_mst_analysis(G_base, k=None, crime_types=CRIME_FOCUS_TYPES, department=department)
    
    reporte_final = {}
    
    # --- PARTE 1: Métricas de Alto Nivel 📊 ---
    # ... (Se mantiene la lógica original, usando G_filtered = G_base) ...
    total_casos_focus_subgraph = sum(_get_case_count(G_filtered, n, CRIME_FOCUS_TYPES) for n in G_filtered.nodes())
    total_nodos_subgraph = G_filtered.number_of_nodes()
    
    try:
        all_paths = [p['path'] for p in fw_stats.get('critical_paths', [])]
        node_counts = pd.Series([node for path in all_paths for node in path]).value_counts()
        bridge_threshold = node_counts.quantile(0.75) if not node_counts.empty else 0
        num_distritos_puente = len(node_counts[node_counts >= bridge_threshold])
        bridge_nodes_list = list(node_counts[node_counts >= bridge_threshold].index)
    except:
        num_distritos_puente = 0
        bridge_nodes_list = []

    mst_stats = kruskal_stats.get('stats', {}) if isinstance(kruskal_stats, dict) else {}

    metrica_global = {
        'total_distritos_analizados': total_nodos_subgraph,
        'total_casos_focus_subtipos': total_casos_focus_subgraph,
        'total_epicentro_detectados': 1, 
        'total_rutas_criticas_fw': fw_stats.get('stats', {}).get('num_caminos_calculados', 0) if isinstance(fw_stats, dict) else fw_stats.get('num_caminos_calculados', 0),
        'total_distritos_puente': num_distritos_puente,
        'total_conexiones_mst': mst_stats.get('MST_aristas', 0),
        'total_casos_ruta_max_conc': fw_stats.get('stats', {}).get('mayor_concentracion_casos', 0) if isinstance(fw_stats, dict) else fw_stats.get('mayor_concentracion_casos', 0),
        'peso_total_mst_inverso': mst_stats.get('peso_total_MST', 0),
    }
    reporte_final['Métricas Globales'] = metrica_global
    
    # --- PARTE 2: Nodos Estratégicos Identificados (Distritos) 🚨 ---
    print("\n--- 2. IDENTIFICANDO NODOS ESTRATÉGICOS ---")
    
    # ... (Se mantiene la lógica original de clasificación y reporte) ...
    nodos_reporte = []
    cases_list = [_get_case_count(G_filtered, n, CRIME_FOCUS_TYPES) for n in G_filtered.nodes()]
    threshold_alta = np.percentile(cases_list, 75) if cases_list else 0
    
    for node in G_filtered.nodes():
        cases_total_focus = _get_case_count(G_filtered, node, CRIME_FOCUS_TYPES)
        cases_by_type = G_filtered.nodes[node].get('cases_by_type', {})
        extorsion_count = cases_by_type.get('EXTORSIÓN', 0)
        homicidio_sicariato_count = cases_by_type.get('HOMICIDIOS', 0) + cases_by_type.get('SICARIATO', 0) 

        recomendacion = ""
        is_epicentro = (node == epicentro)
        is_bridge = node in bridge_nodes_list

        if cases_total_focus > threshold_alta and (extorsion_count > 0 or homicidio_sicariato_count > 0):
            recomendacion += "Requiere **Intervención Inmediata (Foco Rojo)**. "
        elif is_bridge and G_filtered.degree(node) >= 3:
            recomendacion += "Es un **Distrito Puente Estratégico**, su control afecta a múltiples zonas. "
        elif is_epicentro:
            recomendacion += "**Epicentro/Origen** de la expansión delictiva. "
        elif cases_total_focus > np.percentile(cases_list, 50):
            recomendacion += "Zona de **Riesgo Alto**, concentración significativa de los subtipos focales. "
        else:
            recomendacion += "Zona de Riesgo Moderado. "
            
        nodos_reporte.append({
            'Distrito': node,
            'Casos (Focus)': cases_total_focus,
            'Extorsión': extorsion_count,
            'Homicidio/Sicariato': homicidio_sicariato_count,
            'Grado': G_filtered.degree(node),
            'Recomendación Estratégica': recomendacion.strip()
        })
        
    df_nodos_reporte = pd.DataFrame(nodos_reporte).sort_values(by='Casos (Focus)', ascending=False)
    reporte_final['Nodos Estratégicos'] = df_nodos_reporte.to_dict('records')


    # --- PARTE 3: Rutas Críticas de Propagación (Floyd–Warshall) 🗺️ ---
    print("\n--- 3. IDENTIFICANDO RUTAS CRÍTICAS ---")

    # ... (Se mantiene la lógica original) ...
    critical_paths = fw_stats.get('critical_paths', [])
    rutas_reporte = []
    max_concentration = metrica_global['total_casos_ruta_max_conc']
    
    for i, ruta in enumerate(critical_paths[:10]): 
        if max_concentration > 0:
            pct = ruta['concentration'] / max_concentration
            riesgo = "CRÍTICO (Máxima Concentración)" if pct >= 0.9 else ("ALTO" if pct >= 0.7 else ("MEDIO" if pct >= 0.5 else "BAJO"))
        else:
            riesgo = "BAJO (Concentración Nula)"

        rutas_reporte.append({
            'Ruta ID': i + 1,
            'Casos Acumulados (Focus)': ruta['concentration'],
            'Distritos (Corredor)': " -> ".join(ruta['path']),
            'Riesgo': riesgo,
            'Peso Distancia (Inverso)': f"{ruta['cost']:.4f}",
        })

    reporte_final['Rutas Críticas FW'] = rutas_reporte

    # --- PARTE 4: Red Mínima de Intervención (Kruskal MST) 🔗 ---
    print("\n--- 4. ANALIZANDO RED MÍNIMA DE INTERVENCIÓN ---")
    
    # ... (Se mantiene la lógica original) ...
    mst_metrica = {
        'MST_nodos': mst_stats.get('MST_nodos', 0),
        'MST_aristas': mst_stats.get('MST_aristas', 0),
        'aristas_eliminadas': mst_stats.get('aristas_eliminadas', 0),
        'peso_total_MST_inverso': f"{mst_stats.get('peso_total_MST', 0):.4f}",
        'reduccion_complejidad_pct': mst_stats.get('reduccion_peso_pct', 0),
        'cobertura_territorial': mst_stats.get('cobertura_territorial', "0.00%"),
        'eficiencia_complejidad': f"Se mantiene el {mst_stats.get('cobertura_territorial', '0.00%')} del territorio con una reducción de {mst_stats.get('reduccion_peso_pct', 0):.2f}% en la complejidad de la red."
    }
    reporte_final['Métricas MST'] = mst_metrica
    
    conexiones_reporte = []
    central_column_rank = kruskal_stats.get('central_column', [])
    
    for enlace in central_column_rank:
        if isinstance(enlace, dict):
            conexiones_reporte.append({
                'Conexión (Distritos)': enlace.get('Enlace', '--'),
                'Casos Acumulados (Focus)': enlace.get('Casos Acumulados', '--'),
                'Costo (Peso Inverso)': enlace.get('Costo (MST)', '--'),
                'Recomendación': enlace.get('Recomendación', "Enlace de Mínima Conexión, crucial para la intervención centralizada."),
            })
        
    reporte_final['Conexiones Críticas MST'] = conexiones_reporte

    print("\n==================== 2/3. CONSOLIDACIÓN COMPLETADA ====================")
    return reporte_final


# === 2. FUNCIÓN DE IMPRESIÓN: imprimir_reporte_final (Sin cambios) ===

def imprimir_reporte_final(reporte: Dict):
    """Formatea e imprime el reporte consolidado en la consola (solo texto)."""
    
    if not reporte or 'Métricas Globales' not in reporte:
        print("\nEl reporte está vacío o incompleto. No se puede imprimir.")
        return
        
    print("\n\n" + "="*80)
    print("                 🏆 INFORME ESTRATÉGICO CONSOLIDADO DE DELITOS 🏆")
    print(f" (Foco: {', '.join(CRIME_FOCUS_TYPES)})")
    print("="*80)

    # --- PARTE 1: Métricas de Alto Nivel ---
    print("\n## 1. Métricas Clave de Vulnerabilidad Territorial 📈")
    print("---")
    mg = reporte['Métricas Globales']
    
    print(f"Total Distritos Analizados:** {mg['total_distritos_analizados']}")
    print(f"Casos Focales Totales (Focus Subtipos):** {mg['total_casos_focus_subtipos']}")
    print(f"Total Epicentros Detectados:** {mg['total_epicentro_detectados']}")
    print(f"Total Rutas Críticas FW:** {mg['total_rutas_criticas_fw']}")
    print(f"Total Distritos Puente (Estratégicos):** {mg['total_distritos_puente']}")
    print(f"Total Conexiones Esenciales MST:** {mg['total_conexiones_mst']}")
    print(f"Casos en Ruta Máx. Concentración:** {mg['total_casos_ruta_max_conc']}")
    
    # --- PARTE 2: Nodos Estratégicos Identificados ---
    print("\n## 2. Nodos Estratégicos (Distritos) y Riesgo Específico 🚨")
    print("---")
    
    df_nodos = pd.DataFrame(reporte['Nodos Estratégicos'])
    
    print(df_nodos[['Distrito', 'Casos (Focus)', 'Extorsión', 'Homicidio/Sicariato', 'Grado', 'Recomendación Estratégica']].to_markdown(index=False, floatfmt=".0f"))
    print("\n**Nota:** Casos (Focus) = Suma de Extorsión, Homicidio y Sicariato.")
    
    print("\n## 3. Corredores Delictivos (Rutas Críticas FW) 🗺️")
    print("---")

    # 1. Crea el DataFrame. (Asegúrate de que esta línea y las siguientes están INDENTADAS)
    df_rutas = pd.DataFrame(reporte['Rutas Críticas FW']) 

    # 2. Bloque try-except para manejar el error de columna.
    try:
        # ... (Todo el código de impresión de rutas DEBE ESTAR INDENTADO aquí) ...
        if df_rutas.empty:
            print("No se generaron rutas críticas de Floyd-Warshall.")
        else:
            print("**Top Rutas con Mayor Concentración de Casos Focales**")
            
            # Esta línea DEBE ESTAR INDENTADA.
            rutas_criticas_altas = df_rutas[df_rutas['Riesgo'].isin(['CRÍTICO (Máxima Concentración)', 'ALTO'])]
            
            if not rutas_criticas_altas.empty:
                print(rutas_criticas_altas.to_markdown(index=False))
            else:
                print("No se identificaron rutas CRÍTICAS o ALTAS con la concentración actual de casos.")

    except KeyError:
        print("No se generaron rutas críticas de Floyd-Warshall o el cálculo de Riesgo falló.")

    # --- PARTE 4: Red Mínima de Intervención (MST) ---
    print("\n## 4. Red Mínima Esencial de Intervención (Kruskal MST) 🔗")
    print("---")
    
    mm = reporte['Métricas MST']
    print(f"* **Cobertura Territorial:** {mm['cobertura_territorial']}")
    print(f"* **Eficiencia y Complejidad Reducida:** {mm['eficiencia_complejidad']}")
    print(f"* **Aristas No Esenciales Eliminadas (Complejidad Reducida):** {mm['aristas_eliminadas']}")
    print(f"* **Peso Total Inverso del MST (Costo):** {mm['peso_total_MST_inverso']}")
    
    print("\n### Conexiones Críticas del MST (Enlaces más esenciales y de mayor riesgo)")
    df_conexiones = pd.DataFrame(reporte['Conexiones Críticas MST'])
    print(df_conexiones.to_markdown(index=False, floatfmt=".4f"))
    
    print("\n" + "="*80)
    print("FIN DEL INFORME ESTRATÉGICO")
    print("="*80)

# === 3. FUNCIÓN PRINCIPAL: mostrar_resultados (Nueva Lógica de Filtrado) ===

def mostrar_resultados(df: pd.DataFrame, gdf: gpd.GeoDataFrame, department_name: str, epicentro_name: str):
    """
    Función principal: Prepara los datos, crea el grafo, consolida y muestra el reporte final.
    """
    
    DEPARTAMENTO_ANALISIS = department_name
    EPICENTRO_INICIAL = epicentro_name
    global CRIME_FOCUS_TYPES
    
    # 1. PREPARACIÓN Y FILTRADO DE DATOS (LA NUEVA LÓGICA)
    print(f"\n[INFO] 1/4. Filtrando y preparando datos para {DEPARTAMENTO_ANALISIS}...")
    df_filtrado, gdf_filtrado = _preparar_datos_filtrados(df, gdf, DEPARTAMENTO_ANALISIS)
    
    if df_filtrado.empty or gdf_filtrado.empty:
        print("Error: Los datos filtrados están vacíos. No se puede proceder.")
        return

    # 2. Creación del Grafo Global
    print(f"\n[INFO] 2/4. Creando estructura de análisis (Grafo) con datos preparados...")
    
    # NOTA: Ahora _create_graph_from_data recibe datos YA FILTRADOS Y NORMALIZADOS.
    # Esto soluciona el problema de los ceros sin tocar B_algoritmos.
    G_GLOBAL = _create_graph_from_data(
        df_filtrado, # Pasa el DF de delitos filtrado y normalizado
        gdf_filtrado, # Pasa el GDF filtrado y normalizado
        department=DEPARTAMENTO_ANALISIS,
        crime_types=CRIME_FOCUS_TYPES 
    )
    
    if G_GLOBAL is None or G_GLOBAL.number_of_nodes() == 0:
        print(f"Error fatal: El grafo no tiene nodos. Revise B_algoritmos.py (función _create_graph_from_data) si persiste.")
        return
        
    # 3. Diagnóstico de Datos (Verificación de casos > 0)
    
    print("--- 🔬 DIAGNÓSTICO DE CARGA DE DATOS ---")
    total_focus_cases_sum = 0
    num_diagnosed = 0
    for node in G_GLOBAL.nodes:
        if num_diagnosed >= 3: break
        case_data = G_GLOBAL.nodes[node].get('cases_by_type', {})
        total_focus_cases = sum(case_data.get(c, 0) for c in CRIME_FOCUS_TYPES)
        total_focus_cases_sum += total_focus_cases
        num_diagnosed += 1
        
    if total_focus_cases_sum == 0 and G_GLOBAL.number_of_nodes() > 0:
        print("🛑 ALERTA CRÍTICA: La suma de casos focales en los nodos de muestra es CERO.")
        print("🛑 **Acción:** Revise la función _create_graph_from_data: no está mapeando los casos del DataFrame filtrado.")
    else:
        print(f"✅ Integridad de datos OK. {G_GLOBAL.number_of_nodes()} distritos cargados y con casos.")
        
    print("---------------------------------------")
    
    # 4. Consolidación de Resultados e Impresión
    print("[INFO] 3/4. Ejecutando análisis algorítmicos y consolidando resultados...")
    reporte_final_data = consolidar_resultados(
        G_base=G_GLOBAL, 
        department=DEPARTAMENTO_ANALISIS, 
        epicentro=EPICENTRO_INICIAL 
    )

    print("[INFO] 4/4. Generando reporte escrito final.")
    imprimir_reporte_final(reporte_final_data)


def generar_resumen_ui(
    df: pd.DataFrame,
    gdf: gpd.GeoDataFrame,
    department: str,
    crime_filter: Optional[str] = "TODO",
):
    """Construye un resumen estructurado para la vista gráfica de Resultados."""

    from modulos import B_algoritmos  # importación diferida para evitar ciclos

    G, crime_types = B_algoritmos.preparar_grafo_para_algoritmos(
        df,
        gdf,
        department,
        crime_filter,
        verbose=False,
    )

    if not G or not G.nodes:
        raise ValueError("No se pudo construir el grafo para los filtros seleccionados.")

    # Epicentro = distrito con mayor acumulado
    epicentro = max(
        G.nodes,
        key=lambda n: _get_case_count(G, n, crime_types),
    )

    bfs = B_algoritmos.expansion_tree(
        G,
        epicentro,
        method="bfs",
        crime_types=crime_types,
        department=department,
        show_plot=False,
        verbose=False,
    )
    fw = B_algoritmos.floyd_warshall_routes(
        G,
        crime_types=crime_types,
        mode="volume",
        department=department,
        show_plot=False,
        verbose=False,
    )
    kruskal = B_algoritmos.kruskal_mst_analysis(
        G,
        k=None,
        crime_types=crime_types,
        department=department,
        show_plot=False,
        verbose=False,
    )

    fw_paths = fw.get("critical_paths", []) if fw else []
    fw_stats = fw.get("stats", {}) if fw else {}
    bridge_nodes = set(fw.get("bridge_nodes", [])) if fw else set()

    mst_stats = kruskal.get("stats", {}) if kruskal else {}
    mst_connections = kruskal.get("central_column", []) if kruskal else []
    mst_image = kruskal.get("image_path") if kruskal else None

    # --- Tarjetas resumen ---
    total_epicentros = max(1, len(bfs.get("clusters", [])) if bfs else 1)
    total_rutas = len(fw_paths)
    total_puentes = len(bridge_nodes)
    total_conexiones_mst = mst_stats.get("MST_aristas", 0)
    casos_rutas = sum(ruta.get("concentration", 0) for ruta in fw_paths[:3])

    cards = [
        {"label": "Epicentros detectados", "value": total_epicentros},
        {"label": "Rutas críticas", "value": total_rutas},
        {"label": "Distritos puente", "value": total_puentes},
        {"label": "Conexiones MST", "value": total_conexiones_mst},
        {"label": "Casos en rutas críticas", "value": casos_rutas},
    ]

    # --- Nodos estratégicos ---
    cases_list = [_get_case_count(G, n, crime_types) for n in G.nodes]
    p75 = np.percentile(cases_list, 75) if cases_list else 0
    p55 = np.percentile(cases_list, 55) if cases_list else 0
    bfs_nodes = {n for level in bfs.get("levels", []) for n in level.get("nodes", [])} if bfs else set()
    fw_nodes = {n for ruta in fw_paths for n in ruta.get("path", [])}
    mst_nodes = {item.get("distrito") for item in kruskal.get("critical_nodes", [])} if kruskal else set()

    nodos = []
    for node in sorted(G.nodes, key=lambda n: _get_case_count(G, n, crime_types), reverse=True):
        cases = _get_case_count(G, node, crime_types)
        info = G.nodes[node]
        casos_tipo = info.get("cases_by_type", {})
        extorsion = casos_tipo.get("EXTORSIÓN", casos_tipo.get("EXTORSION", 0))
        sicariato = casos_tipo.get("SICARIATO", 0) + casos_tipo.get("HOMICIDIOS", 0)

        nivel = "Crítico" if cases >= p75 else ("Alto" if cases >= p55 else "Medio")
        rol = "Epicentro principal" if node == epicentro else (
            "Nodo puente estratégico" if node in bridge_nodes else "Distrito de tránsito"
        )

        algoritmos = []
        if node in bfs_nodes or node == epicentro:
            algoritmos.append("BFS")
        if node in fw_nodes:
            algoritmos.append("Floyd")
        if node in mst_nodes:
            algoritmos.append("Kruskal")

        recomendacion = []
        if node == epicentro:
            recomendacion.append("Requiere intervención inmediata. Mayor concentración registrada.")
        if node in bridge_nodes:
            recomendacion.append("Distrito puente que conecta múltiples corredores.")
        if node in mst_nodes:
            recomendacion.append("Clave en la red mínima; mantener vigilancia.")
        if not recomendacion:
            recomendacion.append("Zona monitoreada. Refuerza patrullaje preventivo.")

        nodos.append({
            "nombre": node,
            "sigla": _sigla_distrito(node),
            "rol": rol,
            "nivel": nivel,
            "extorsion": extorsion,
            "sicariato": sicariato,
            "total": cases,
            "algoritmos": algoritmos,
            "recomendacion": " ".join(recomendacion),
        })

    nodos = nodos[:5]

    # --- Rutas críticas ---
    rutas = []
    for idx, ruta in enumerate(fw_paths[:3], start=1):
        path = ruta.get("path", [])
        riesgo = "Riesgo crítico" if idx == 1 else ("Riesgo alto" if idx == 2 else "Riesgo medio")
        estrategia = "Establecer intervención en puntos intermedios." if idx == 1 else (
            "Operativo conjunto en distritos del corredor." if idx == 2 else "Monitoreo reforzado de accesos."
        )
        rutas.append({
            "id": f"R{idx}",
            "descripcion": "Corredor delictivo prioritario" if idx == 1 else "Corredor supervisado",
            "path": " -> ".join(path),
            "casos": ruta.get("concentration", 0),
            "distancia": max(1, len(path) - 1),
            "riesgo": riesgo,
            "estrategia": estrategia,
        })

    # --- Sección MST ---
    mst_metrics = [
        {"label": "Nodos", "value": mst_stats.get("MST_nodos", "--")},
        {"label": "Aristas MST", "value": mst_stats.get("MST_aristas", "--")},
        {"label": "Peso total", "value": int(round(mst_stats.get("peso_total_MST", 0)))},
        {"label": "Reducción", "value": f"{mst_stats.get('reduccion_peso_pct', 0):.0f}%"},
    ]

    conexiones_rank = []
    for idx, item in enumerate(mst_connections, start=1):
        conexiones_rank.append({
            "rank": idx,
            "enlace": item.get("Enlace", "--"),
            "casos": item.get("Casos Acumulados", "--"),
        })

    insights = [
        {"label": "Cobertura territorial", "value": mst_stats.get("cobertura_territorial", "--")},
        {"label": "Eficiencia", "value": "Alta" if mst_stats.get("reduccion_peso_pct", 0) >= 10 else "Media"},
        {"label": "Complejidad reducida", "value": f"{mst_stats.get('reduccion_peso_pct', 0):.2f}%"},
    ]

    mst_section = {
        "image_path": mst_image,
        "metrics": mst_metrics,
        "conexiones": conexiones_rank,
        "insights": insights,
    }

    return {
        "department": department,
        "crime_types": crime_types,
        "epicentro": epicentro,
        "cards": cards,
        "nodos": nodos,
        "rutas": rutas,
        "mst": mst_section,
    }