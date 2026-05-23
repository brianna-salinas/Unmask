# modulos/algoritmos.py — Algoritmos mejorados UNMASK v2
import networkx as nx
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd
import os
from typing import Dict, List, Optional, Tuple

from modulos.explorar_grafo import (
    filtrar_dataframe, obtener_conteos, construir_grafo,
    asignar_atributos, calcular_centralidad, categorizar_distritos,
    _get_positions, _normalizar_dpto, LIMA_ALIAS,
)

# ─────────────────────────── COLORES ────────────────────────────────
C_EPICENTRO   = "#48c9b0"
C_ALTA        = "#d73027"
C_MEDIA       = "#fc8d59"
C_BAJA        = "#00B8DB"
C_RUTA        = "#6a0dad"
C_PUENTE      = "#ffd54f"
C_MST         = "#fc8d59"
C_REMOVIDA    = "#cccccc"


# ─────────────────────────── HELPERS ────────────────────────────────
def _get_case_count(G: nx.Graph, node: str, crime_types: Optional[List[str]]) -> int:
    if not crime_types or crime_types == ["TODO"]:
        return G.nodes[node].get("cases_total", G.nodes[node].get("Crime_Count", 0))
    cb = G.nodes[node].get("cases_by_type", G.nodes[node].get("Crime_Subtypes", {}))
    return sum(cb.get(c, 0) for c in crime_types)


def _get_pos(G: nx.Graph) -> Dict:
    pos = nx.get_node_attributes(G, "pos")
    if not pos:
        pos = nx.kamada_kawai_layout(G)
    return pos


def _draw_and_save(
    G: nx.Graph,
    pos: Dict,
    title: str,
    subtitle: str,
    node_colors: List,
    edge_colors: List,
    labels: Dict,
    legend: Dict,
    filename: str,
) -> str:
    out_dir = "resultados_algoritmos"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, filename)

    fig, ax = plt.subplots(figsize=(16, 11), dpi=120, facecolor="#081425")
    ax.set_facecolor("#081425")

    # Aristas
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colors, width=1.8, alpha=0.8)
    # Nodos
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=900, linewidths=1.5, edgecolors="#0F172A")
    # Etiquetas
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                            font_size=7, font_color="white", font_weight="bold")

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    handles = []
    for lbl, col in legend.get("nodes", {}).items():
        handles.append(Line2D([0], [0], marker="o", color="w",
                               markerfacecolor=col, markersize=10, label=lbl))
    for lbl, col in legend.get("edges", {}).items():
        handles.append(Patch(facecolor=col, edgecolor="gray", label=lbl))

    ax.legend(handles=handles, loc="lower left",
              frameon=True, framealpha=0.85,
              facecolor="#0F2238", edgecolor="#1E3A5F",
              labelcolor="white", fontsize=8)

    ax.set_title(f"{title}\n{subtitle}", color="white", fontsize=11,
                 fontweight="bold", pad=12)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor=fig.get_facecolor(), dpi=120)
    plt.close(fig)
    return out_path


# ─────────────────────────── PREPARAR GRAFO ─────────────────────────
def preparar_grafo_para_algoritmos(
    df: pd.DataFrame,
    gdf: gpd.GeoDataFrame,
    department: str,
    crime_filter,
    verbose: bool = False,
) -> Tuple[nx.Graph, List[str]]:
    """Construye el grafo NetworkX listo para los algoritmos."""
    # Normalizar crime_filter
    if isinstance(crime_filter, (list, tuple, set)):
        crime_types = [str(c).upper().strip() for c in crime_filter if c]
    else:
        val = str(crime_filter or "TODO").upper().strip()
        crime_types = [val]
    if not crime_types:
        crime_types = ["TODO"]
    if any(ct in {"TODO", "TODOS"} for ct in crime_types):
        crime_types = ["TODO"]

    # Usar todos los años disponibles
    years = sorted(df["ANIO"].dropna().unique())
    all_frames = []
    for yr in years:
        ct_str = crime_types[0] if crime_types != ["TODO"] else "TODO"
        df_y = filtrar_dataframe(df, department, ct_str, str(int(yr)))
        if not df_y.empty:
            all_frames.append(df_y)

    if not all_frames:
        return nx.Graph(), crime_types

    df_all = pd.concat(all_frames, ignore_index=True)
    df_counts, df_subtypes = obtener_conteos(df_all)

    dep_norm = _normalizar_dpto(department)
    if dep_norm == "LIMA":
        mask = gdf["NOMBDEP"].str.upper().str.strip().isin(LIMA_ALIAS | {"LIMA"})
    else:
        mask = gdf["NOMBDEP"].str.upper().str.strip() == dep_norm

    gdf_dep = gdf[mask].copy().reset_index(drop=True)
    if gdf_dep.empty:
        return nx.Graph(), crime_types

    G = construir_grafo(gdf_dep)
    G = asignar_atributos(G, df_counts, df_subtypes)

    # Agregar atributos requeridos por los algoritmos
    for node in G.nodes():
        G.nodes[node]["cases_total"]  = G.nodes[node].get("Crime_Count", 0)
        G.nodes[node]["cases_by_type"] = G.nodes[node].get("Crime_Subtypes", {})
        # Posición geográfica
        norm = node.upper().strip()
        match = gdf_dep[gdf_dep["NOMBDIST"].str.upper().str.strip() == norm]
        if not match.empty:
            try:
                pt = match.iloc[0].geometry.representative_point()
                G.nodes[node]["pos"] = (float(pt.x), float(pt.y))
            except Exception:
                pass

    return G, crime_types


# ─────────────────────────── BFS / DFS ──────────────────────────────
def expansion_tree(
    G: nx.Graph,
    inicio: str,
    method: str = "bfs",
    max_depth: Optional[int] = None,
    crime_types: Optional[List[str]] = None,
    department: Optional[str] = None,
    show_plot: bool = False,
    verbose: bool = False,
) -> Dict:

    if inicio not in G:
        return {}

    # Árbol de expansión
    if method.lower() == "bfs":
        T = nx.bfs_tree(G, source=inicio, depth_limit=max_depth)
        algoritmo = "BFS (Expansión por Niveles)"
    else:
        T = nx.dfs_tree(G, source=inicio, depth_limit=max_depth)
        algoritmo = "DFS (Expansión en Profundidad)"

    distancias = nx.shortest_path_length(G, source=inicio)

    levels: Dict[int, List[str]] = {}
    alcanzados: set = set()
    total_casos = 0
    max_level = 0

    for node in T.nodes():
        if node in distancias:
            nivel = distancias[node]
            max_level = max(max_level, nivel)
            levels.setdefault(nivel, []).append(node)
            alcanzados.add(node)
            total_casos += _get_case_count(G, node, crime_types)

    pct = (len(alcanzados) / G.number_of_nodes() * 100) if G.number_of_nodes() > 0 else 0

    # Velocidad y dirección
    vel = "Rápida (por niveles)" if method.lower() == "bfs" else "Profunda (en árbol)"
    pos_attr = nx.get_node_attributes(G, "pos")
    if pos_attr and len(alcanzados) > 1 and inicio in pos_attr:
        cx = np.mean([pos_attr[n][0] for n in alcanzados if n in pos_attr])
        cy = np.mean([pos_attr[n][1] for n in alcanzados if n in pos_attr])
        ix, iy = pos_attr[inicio]
        dir_str = f"{'Norte' if cy > iy else 'Sur'}-{'Este' if cx > ix else 'Oeste'} desde {inicio}"
    else:
        dir_str = f"Desde {inicio} — {max_level} niveles de profundidad"

    # Clusters (componentes de alta concentración)
    cases_vals = [_get_case_count(G, n, crime_types) for n in G.nodes()]
    thr_alta  = np.percentile(cases_vals, 75) if cases_vals else 0
    thr_media = np.percentile(cases_vals, 50) if cases_vals else 0

    G_hot = nx.Graph()
    for n in alcanzados:
        if _get_case_count(G, n, crime_types) > thr_alta:
            G_hot.add_node(n)
    for u, v in G.edges():
        if u in G_hot and v in G_hot:
            G_hot.add_edge(u, v)
    hotspots = [list(c) for c in nx.connected_components(G_hot)]

    cluster_details = []
    for i, cl in enumerate(hotspots):
        casos_cl = sum(_get_case_count(G, n, crime_types) for n in cl)
        conex = G_hot.subgraph(cl).number_of_edges()
        cluster_details.append({
            "name": f"Cluster {i+1}",
            "nodes": cl,
            "cases": int(casos_cl),
            "connections": int(conex),
        })

    stats = {
        "algoritmo": algoritmo,
        "nodo_inicial": inicio,
        "profundidad_maxima": max_level,
        "nodos_alcanzados_pct": f"{pct:.1f}%",
        "casos_acumulados_ruta": int(total_casos),
        "velocidad_expansion": vel,
        "direccion_detectada": dir_str,
        "clusters_detectados": len(hotspots),
    }

    # Colores
    node_colors = []
    labels = {}
    for n in G.nodes():
        cc = _get_case_count(G, n, crime_types)
        labels[n] = f"{n}\n({cc})"
        if n == inicio:
            node_colors.append(C_EPICENTRO)
        elif n not in alcanzados:
            node_colors.append(C_REMOVIDA)
        elif cc > thr_alta:
            node_colors.append(C_ALTA)
        elif cc > thr_media:
            node_colors.append(C_MEDIA)
        else:
            node_colors.append(C_BAJA)

    edge_colors = [
        C_MEDIA if T.has_edge(u, v) or T.has_edge(v, u) else C_REMOVIDA
        for u, v in G.edges()
    ]

    pos = _get_pos(G)
    legend = {
        "nodes": {
            f"Epicentro ({inicio})": C_EPICENTRO,
            f"Alta concentración (>{thr_alta:.0f})": C_ALTA,
            f"Media concentración (>{thr_media:.0f})": C_MEDIA,
            "Visitado / Bajo": C_BAJA,
            "No alcanzado": C_REMOVIDA,
        },
        "edges": {
            f"Expansión {method.upper()}": C_MEDIA,
            "No usada": C_REMOVIDA,
        },
    }

    image_path = _draw_and_save(
        G, pos,
        "ÁRBOL DE EXPANSIÓN TERRITORIAL DEL DELITO",
        f"Análisis {algoritmo} desde {inicio}",
        node_colors, edge_colors, labels, legend,
        f"expansion_{method.lower()}_{inicio.replace(' ', '_')}.png",
    )

    levels_detail = [
        {
            "level": int(lv),
            "nodes": ns,
            "cases": int(sum(_get_case_count(G, n, crime_types) for n in ns)),
        }
        for lv, ns in sorted(levels.items())
    ]
    frontier = levels.get(max_level, [])

    return {
        "stats": stats,
        "levels": levels_detail,
        "clusters": cluster_details,
        "frontier_nodes": frontier,
        "thresholds": {"high": float(thr_alta), "medium": float(thr_media)},
        "image_path": image_path,
        "method": method.upper(),
    }


# ─────────────────────────── FLOYD–WARSHALL ─────────────────────────
def floyd_warshall_routes(
    G: nx.Graph,
    crime_types: Optional[List[str]] = None,
    mode: str = "volume",
    department: Optional[str] = None,
    show_plot: bool = False,
    verbose: bool = False,
) -> Dict:

    nodes = list(G.nodes())
    n = len(nodes)
    if n < 2:
        return {}

    idx = {nd: i for i, nd in enumerate(nodes)}

    # Construir matriz de costos
    D = np.full((n, n), np.inf)
    np.fill_diagonal(D, 0)
    P = np.full((n, n), -1, dtype=int)

    for u, v in G.edges():
        i, j = idx[u], idx[v]
        cu = _get_case_count(G, u, crime_types)
        cv = _get_case_count(G, v, crime_types)
        weight = cu + cv
        cost = 1.0 / (weight + 1) if mode == "volume" else float(weight + 1)
        D[i, j] = D[j, i] = cost

    # Algoritmo Floyd–Warshall
    for k in range(n):
        for i in range(n):
            if D[i, k] == np.inf:
                continue
            for j in range(n):
                if D[i, k] + D[k, j] < D[i, j]:
                    D[i, j] = D[i, k] + D[k, j]
                    P[i, j] = k

    def reconstruct(i, j):
        if D[i, j] == np.inf:
            return []
        if P[i, j] == -1:
            return [nodes[i], nodes[j]]
        k = P[i, j]
        l = reconstruct(i, k)
        r = reconstruct(k, j)
        return l[:-1] + r if l and r else []

    # Recopilar caminos
    critical_paths = []
    for i in range(n):
        for j in range(i + 1, n):
            if D[i, j] < np.inf:
                path = reconstruct(i, j)
                if len(path) >= 2:
                    conc = sum(_get_case_count(G, nd, crime_types) for nd in path)
                    critical_paths.append({
                        "path": path,
                        "concentration": int(conc),
                        "cost": float(D[i, j]),
                    })

    critical_paths.sort(key=lambda x: x["concentration"], reverse=True)

    # Distritos puente
    all_nodes_in_paths = [nd for p in critical_paths for nd in p["path"]]
    node_freq = pd.Series(all_nodes_in_paths).value_counts()
    bridge_thr = node_freq.quantile(0.75) if not node_freq.empty else 0
    bridge_nodes = list(node_freq[node_freq >= bridge_thr].index)

    most_crit = critical_paths[0] if critical_paths else None
    most_eff  = critical_paths[-1] if critical_paths else None  # menor concentración

    stats = {
        "algoritmo": "Floyd–Warshall",
        "modo_analisis": mode,
        "num_caminos_calculados": len(critical_paths),
        "num_distritos_puentes": len(bridge_nodes),
        "mayor_concentracion_casos": most_crit["concentration"] if most_crit else 0,
        "ruta_mayor_concentracion": " → ".join(most_crit["path"]) if most_crit else "N/A",
        "ruta_mas_eficiente_casos": most_eff["concentration"] if most_eff else 0,
    }

    # Visualización
    cases_all = [_get_case_count(G, nd, crime_types) for nd in G.nodes()]
    vuln_thr = np.percentile(cases_all, 75) if cases_all else 0
    crit_edges = set()
    if most_crit:
        for a, b in zip(most_crit["path"][:-1], most_crit["path"][1:]):
            crit_edges.add((a, b))
            crit_edges.add((b, a))

    node_colors = []
    labels = {}
    for nd in G.nodes():
        cc = _get_case_count(G, nd, crime_types)
        labels[nd] = f"{nd}\n({cc} cs)"
        if nd in bridge_nodes:
            node_colors.append(C_PUENTE)
        elif cc > vuln_thr:
            node_colors.append(C_ALTA)
        else:
            node_colors.append(C_BAJA)

    edge_colors = [
        C_RUTA if (u, v) in crit_edges else C_REMOVIDA
        for u, v in G.edges()
    ]

    pos = _get_pos(G)
    legend = {
        "nodes": {
            "Distrito puente (alto flujo)": C_PUENTE,
            f"Alta concentración (>{vuln_thr:.0f})": C_ALTA,
            "Otros distritos": C_BAJA,
        },
        "edges": {
            "Ruta crítica máx. concentración": C_RUTA,
            "Conexión regular": C_REMOVIDA,
        },
    }

    image_path = _draw_and_save(
        G, pos,
        "RUTAS DE MAYOR CONCENTRACIÓN DE DENUNCIAS",
        f"Análisis Floyd-Warshall — Modo: {mode}",
        node_colors, edge_colors, labels, legend,
        f"floyd_warshall_{mode}.png",
    )

    bridge_report = [
        {"Distrito": nd, "Frecuencia en Rutas": int(node_freq.get(nd, 0))}
        for nd in sorted(bridge_nodes, key=lambda x: node_freq.get(x, 0), reverse=True)
    ]

    return {
        "stats": stats,
        "critical_paths": critical_paths,
        "bridge_nodes": bridge_nodes,
        "bridge_report": bridge_report,
        "most_critical_path": most_crit,
        "most_efficient_path": most_eff,
        "image_path": image_path,
        "mode": mode,
    }


# ─────────────────────────── KRUSKAL (MST) ──────────────────────────
def kruskal_mst_analysis(
    G: nx.Graph,
    k: Optional[int] = None,
    crime_types: Optional[List[str]] = None,
    department: Optional[str] = None,
    show_plot: bool = False,
    verbose: bool = False,
) -> Dict:

    if G.number_of_nodes() < 2:
        return {}

    node_cases = {n: _get_case_count(G, n, crime_types) for n in G.nodes()}
    cases_list = list(node_cases.values())
    red_thr = np.percentile(cases_list, 75) if cases_list else 0

    # Construir grafo ponderado con costo inverso
    G_w = G.copy()
    total_graph_weight = 0.0
    for u, v in G_w.edges():
        cu = _get_case_count(G_w, u, crime_types)
        cv = _get_case_count(G_w, v, crime_types)
        cost = 1.0 / (cu + cv + 1)
        G_w.edges[u, v]["weight"] = cost
        total_graph_weight += cost

    # Kruskal MST
    MST = nx.minimum_spanning_tree(G_w, algorithm="kruskal")

    mst_weight = MST.size(weight="weight")
    reduccion_pct = 100 * (1 - mst_weight / total_graph_weight) if total_graph_weight > 0 else 0

    edges_mst = list(MST.edges())
    edges_removed = [
        e for e in G.edges()
        if e not in edges_mst and (e[1], e[0]) not in edges_mst
    ]

    # Nodos críticos
    crit_nodes = [
        {"distrito": n, "casos": int(c)}
        for n, c in sorted(node_cases.items(), key=lambda x: x[1], reverse=True)
        if c > red_thr
    ]

    # Columna central: top 5 aristas MST con menor costo (mayor importancia)
    mst_edge_data = sorted(
        [(u, v, d["weight"]) for u, v, d in MST.edges(data=True)],
        key=lambda x: x[2]
    )[:5]
    central_column = [
        {
            "Enlace": f"{u} ↔ {v}",
            "Casos Acumulados": int(node_cases.get(u, 0) + node_cases.get(v, 0)),
            "Costo (MST)": f"{cost:.4f}",
        }
        for u, v, cost in mst_edge_data
    ]

    stats = {
        "MST_nodos": MST.number_of_nodes(),
        "MST_aristas": len(edges_mst),
        "aristas_eliminadas": len(edges_removed),
        "peso_total_MST": round(mst_weight, 4),
        "reduccion_peso_pct": round(reduccion_pct, 2),
        "cobertura_territorial": f"{MST.number_of_nodes() / G.number_of_nodes() * 100:.1f}%",
        "focos_del_crimen_detectados": len(crit_nodes),
    }

    # Visualización
    mst_edge_set = {(u, v) for u, v in edges_mst} | {(v, u) for u, v in edges_mst}
    node_colors = [C_ALTA if node_cases.get(n, 0) > red_thr else C_MEDIA for n in G.nodes()]
    labels = {n: f"{n}\n({node_cases.get(n, 0)} cs)" for n in G.nodes()}
    edge_colors = [C_MST if (u, v) in mst_edge_set else C_REMOVIDA for u, v in G.edges()]

    pos = _get_pos(G)
    legend = {
        "nodes": {
            f"Crítico (>{red_thr:.0f} casos)": C_ALTA,
            "Otros distritos": C_MEDIA,
        },
        "edges": {
            "Arista MST (esencial)": C_MST,
            "Arista eliminada": C_REMOVIDA,
        },
    }

    image_path = _draw_and_save(
        G, pos,
        "RED MÍNIMA DE DISTRITOS CON MAYOR ACUMULACIÓN DELICTIVA",
        f"Algoritmo Kruskal — Reducción: {reduccion_pct:.1f}% del costo total",
        node_colors, edge_colors, labels, legend,
        f"kruskal_mst_k_{k or 'auto'}.png",
    )

    return {
        "stats": stats,
        "critical_nodes": crit_nodes,
        "central_column": central_column,
        "image_path": image_path,
        "edges_removed": edges_removed,
        "edges_mst": edges_mst,
    }
