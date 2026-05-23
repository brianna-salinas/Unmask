# modulos/resultados.py — Resultados mejorados UNMASK v2
import pandas as pd
import numpy as np
import networkx as nx
import geopandas as gpd
from typing import Dict, List, Optional

from modulos.algoritmos import (
    preparar_grafo_para_algoritmos,
    expansion_tree,
    floyd_warshall_routes,
    kruskal_mst_analysis,
    _get_case_count,
)


def _sigla(nombre: str) -> str:
    tokens = [t for t in nombre.split() if t]
    if not tokens:
        return (nombre[:3] or "ND").upper()
    if len(tokens) == 1:
        return tokens[0][:3].upper()
    return "".join(t[0] for t in tokens[:3]).upper()


def _fmt(valor) -> str:
    try:
        return f"{int(valor):,}".replace(",", ".")
    except Exception:
        return str(valor)


def _nivel(casos: int, q75: int, q50: int) -> str:
    if casos >= q75:
        return "Crítico"
    if casos >= q50:
        return "Alto"
    return "Medio"


def generar_resumen_ui(
    df: pd.DataFrame,
    gdf: gpd.GeoDataFrame,
    department: str,
    crime_filter: str = "TODO",
) -> Dict:
    """
    Genera el resumen estratégico completo para la UI.
    Retorna un dict compatible con el renderer de la GUI.
    """
    # ── Construir grafo ──────────────────────────────────────────────
    G, crime_types = preparar_grafo_para_algoritmos(
        df, gdf, department, crime_filter, verbose=False
    )
    if not G or G.number_of_nodes() < 2:
        return {}

    node_cases = {n: _get_case_count(G, n, crime_types) for n in G.nodes()}
    cases_vals = list(node_cases.values())
    q75 = int(np.percentile(cases_vals, 75)) if cases_vals else 0
    q50 = int(np.percentile(cases_vals, 50)) if cases_vals else 0

    # ── Ejecutar algoritmos ─────────────────────────────────────────
    # Elegir epicentro: distrito con más casos
    epicentro = max(node_cases, key=node_cases.get, default=list(G.nodes())[0])

    bfs_res     = expansion_tree(G, epicentro, "bfs",  crime_types=crime_types, verbose=False)
    fw_res      = floyd_warshall_routes(G, crime_types=crime_types, mode="volume", verbose=False)
    kruskal_res = kruskal_mst_analysis(G, crime_types=crime_types, verbose=False)

    # ── Cards superiores ────────────────────────────────────────────
    bfs_stats = bfs_res.get("stats", {})
    fw_stats  = fw_res.get("stats", {})
    k_stats   = kruskal_res.get("stats", {})

    epi_count = len(bfs_res.get("clusters", []))
    rutas_count = len(fw_res.get("critical_paths", []))
    puentes_count = fw_stats.get("num_distritos_puentes", 0)
    conexiones_mst = k_stats.get("MST_aristas", 0)
    casos_ruta = fw_stats.get("mayor_concentracion_casos", 0)

    cards = [
        {"value": epi_count,       "label": "Epicentros detectados"},
        {"value": rutas_count,     "label": "Rutas críticas"},
        {"value": puentes_count,   "label": "Distritos puente"},
        {"value": conexiones_mst,  "label": "Conexiones MST"},
        {"value": casos_ruta,      "label": "Casos en rutas críticas"},
    ]

    # ── Nodos estratégicos ──────────────────────────────────────────
    # Identificar por qué algoritmos detectó cada nodo
    bfs_hot_nodes = {n for cl in bfs_res.get("clusters", []) for n in cl.get("nodes", [])}
    fw_bridge     = set(fw_res.get("bridge_nodes", []))
    kruskal_crit  = {d["distrito"] for d in kruskal_res.get("critical_nodes", [])}

    estrategicos = sorted(
        [n for n in G.nodes() if n in bfs_hot_nodes or n in fw_bridge or n in kruskal_crit],
        key=lambda x: node_cases.get(x, 0),
        reverse=True,
    )[:6]

    nodos_ui = []
    for n in estrategicos:
        algs = []
        if n in bfs_hot_nodes:
            algs.append("BFS")
        if n in fw_bridge:
            algs.append("Floyd")
        if n in kruskal_crit:
            algs.append("Kruskal")

        cc = node_cases.get(n, 0)
        sub = G.nodes[n].get("Crime_Subtypes", G.nodes[n].get("cases_by_type", {}))
        ext = sub.get("EXTORSION", 0)
        hom = sub.get("HOMICIDIO", 0)
        nivel = _nivel(cc, q75, q50)

        if n in bfs_hot_nodes and n in fw_bridge:
            rol = "Epicentro principal"
        elif n in fw_bridge:
            rol = "Nodo puente estratégico"
        elif n in kruskal_crit:
            rol = "Distrito de tránsito"
        else:
            rol = "Conector zona sur"

        if nivel == "Crítico":
            rec = f"Requiere intervención inmediata. Mayor concentración registrada. Distrito puente que conecta múltiples corredores. Clave en la red mínima; mantener vigilancia."
        elif nivel == "Alto":
            rec = f"Distrito de alta actividad delictiva. Monitoreo reforzado necesario."
        else:
            rec = f"Distrito de tránsito. Vigilancia estándar recomendada."

        nodos_ui.append({
            "nombre": n,
            "sigla": _sigla(n),
            "rol": rol,
            "nivel": nivel,
            "extorsion": int(ext),
            "sicariato": int(hom),
            "total": int(cc),
            "algoritmos": algs,
            "recomendacion": rec,
        })

    # ── Rutas críticas ───────────────────────────────────────────────
    rutas_ui = []
    riesgo_labels = ["Riesgo crítico", "Riesgo alto", "Riesgo alto",
                     "Riesgo medio", "Riesgo medio"]
    estrategias = [
        "Establecer puntos de control en nodos intermedios. Reforzar vigilancia en rutas de acceso.",
        "Operativo conjunto en los distritos. Desarticular estructura operativa.",
        "Interceptar en nodo puente. Monitorear flujos entre zonas.",
        "Monitoreo reforzado de accesos.",
        "Vigilancia estándar y patrullaje preventivo.",
    ]
    descripciones = [
        "Corredor de mayor propagación. Conecta epicentro con zona central.",
        "Red consolidada zona sur. Alta cohesión territorial.",
        "Corredor norte conectando con epicentro principal.",
        "Corredor supervisado.",
        "Corredor de menor riesgo relativo.",
    ]

    for idx, ruta in enumerate(fw_res.get("critical_paths", [])[:5]):
        path = ruta.get("path", [])
        rutas_ui.append({
            "id": f"R{idx+1}",
            "descripcion": descripciones[idx] if idx < len(descripciones) else f"Corredor {idx+1}",
            "path": " → ".join(path),
            "riesgo": riesgo_labels[idx] if idx < len(riesgo_labels) else "Riesgo medio",
            "casos": ruta.get("concentration", 0),
            "distancia": len(path) - 1,
            "estrategia": estrategias[idx] if idx < len(estrategias) else "",
        })

    # ── MST ─────────────────────────────────────────────────────────
    mst_metrics = [
        {"label": "Nodos", "value": k_stats.get("MST_nodos", "--")},
        {"label": "Aristas MST", "value": k_stats.get("MST_aristas", "--")},
        {"label": "Peso total", "value": k_stats.get("peso_total_MST", "--")},
        {"label": "Reducción", "value": f"{k_stats.get('reduccion_peso_pct', 0):.1f}%"},
    ]
    mst_conexiones = [
        {
            "rank": i + 1,
            "enlace": c.get("Enlace", "--"),
            "casos": c.get("Casos Acumulados", 0),
        }
        for i, c in enumerate(kruskal_res.get("central_column", [])[:5])
    ]
    mst_insights = [
        {"label": "Cobertura territorial", "value": k_stats.get("cobertura_territorial", "--")},
        {"label": "Eficiencia", "value": "Alta"},
        {"label": "Complejidad reducida", "value": f"{k_stats.get('reduccion_peso_pct', 0):.1f}%"},
    ]

    return {
        "cards": cards,
        "nodos": nodos_ui,
        "rutas": rutas_ui,
        "mst": {
            "image_path": kruskal_res.get("image_path"),
            "metrics": mst_metrics,
            "conexiones": mst_conexiones,
            "insights": mst_insights,
        },
    }
