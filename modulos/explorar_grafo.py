# modulos/explorar_grafo.py — Módulo mejorado UNMASK v2
import pandas as pd
import numpy as np
import networkx as nx
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# ─────────────────────────── CONSTANTES ───────────────────────────
TIPO_DELITO_OPCIONES: List[Dict[str, str]] = [
    {"label": "Todos los delitos", "value": "TODO"},
    {"label": "Solo Extorsión",    "value": "SOLO_EXTORSION"},
    {"label": "Solo Homicidio",    "value": "SOLO_HOMICIDIO"},
    {"label": "Extorsión + Homicidio", "value": "AMBOS"},
]

COLOR_POR_OPCIONES: List[Dict[str, str]] = [
    {"label": "Volumen de casos",  "value": "cases"},
    {"label": "Conectividad",      "value": "connectivity"},
]

LIMA_ALIAS = {"LIMA METROPOLITANA", "REGION LIMA", "LIMA METROPOLITANO", "PROVINCIA DE LIMA"}

CRIME_PALETTE = {
    "High Crime":   "#E7000B",
    "Medium Crime": "#FF6900",
    "Low Crime":    "#00B8DB",
}
CONN_PALETTE = {
    "High Connectivity":   "#38BDF8",
    "Medium Connectivity": "#FACC15",
    "Low Connectivity":    "#94A3B8",
}


# ─────────────────────────── HELPERS ───────────────────────────────
def _normalizar_dpto(nombre: str) -> str:
    key = str(nombre).upper().strip()
    return "LIMA" if key in LIMA_ALIAS else key


def obtener_opciones_filtros(df: pd.DataFrame) -> Dict:
    departamentos = sorted(
        {str(d).strip() for d in df["DPTO_HECHO_NEW"].dropna().unique() if str(d).strip()}
    )
    anios = [str(int(a)) for a in sorted(df["ANIO"].dropna().unique())]
    return {
        "departamentos": departamentos,
        "tipo_delito": TIPO_DELITO_OPCIONES,
        "color_por": COLOR_POR_OPCIONES,
        "anios": anios,
    }


# ─────────────────────────── FILTRADO ──────────────────────────────
def filtrar_dataframe(df: pd.DataFrame, department: str, crime_type: str, year: str) -> pd.DataFrame:
    dep_norm = _normalizar_dpto(department)
    ct_upper = str(crime_type).upper().strip()

    # Filtrar año
    try:
        yr = int(year)
        df_y = df[df["ANIO"] == yr]
    except (ValueError, TypeError):
        df_y = df[df["ANIO"].astype(str).str.strip() == str(year).strip()]

    # Filtrar departamento (admite alias Lima)
    dpto_col = df_y["DPTO_HECHO_NEW"].astype(str).str.upper().str.strip()
    if dep_norm == "LIMA":
        df_d = df_y[dpto_col.isin(LIMA_ALIAS | {"LIMA"})]
    else:
        df_d = df_y[dpto_col == dep_norm]

    if df_d.empty:
        return df_d

    sub = df_d["SUB_TIPO"].astype(str).str.upper().str.strip()

    if ct_upper == "TODO":
        return df_d
    if ct_upper in {"AMBOS", "EXTORSION Y HOMICIDIO", "EXTORSION Y SICARIATO"}:
        return df_d[sub.isin(["EXTORSION", "HOMICIDIO"])]
    if ct_upper in {"SOLO_EXTORSION", "SOLO EXTORSION"}:
        return df_d[sub == "EXTORSION"]
    if ct_upper in {"SOLO_HOMICIDIO", "SOLO HOMICIDIO", "SOLO_SICARIATO"}:
        return df_d[sub == "HOMICIDIO"]

    return df_d[sub == ct_upper]


# ─────────────────────────── CONTEOS ───────────────────────────────
def obtener_conteos(df_filtered: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Cuenta FILAS (denuncias) por distrito y subtipo."""
    df_counts = (
        df_filtered.groupby("DIST_HECHO")
        .size()
        .reset_index(name="Crime_Count")
    )
    df_subtypes = (
        df_filtered.groupby(["DIST_HECHO", "SUB_TIPO"])
        .size()
        .reset_index(name="Subtype_Crime_Count")
    )
    return df_counts, df_subtypes


# ─────────────────────────── GRAFO ─────────────────────────────────
def construir_grafo(gdf_dep: gpd.GeoDataFrame) -> nx.Graph:
    """Construye el grafo de adyacencia basado en contigüidad de polígonos."""
    G = nx.Graph()
    gdf = gdf_dep.copy().reset_index(drop=True)
    gdf["geometry"] = gdf["geometry"].buffer(0)  # reparar topología

    nombres = gdf["NOMBDIST"].tolist()
    geoms   = gdf["geometry"].tolist()
    bboxes  = [g.bounds for g in geoms]

    for n in nombres:
        G.add_node(n)

    n_total = len(nombres)
    for i in range(n_total):
        gi, bi = geoms[i], bboxes[i]
        for j in range(i + 1, n_total):
            gj, bj = geoms[j], bboxes[j]
            # Prueba rápida de bbox antes de calcular topología
            if bi[2] < bj[0] or bj[2] < bi[0] or bi[3] < bj[1] or bj[3] < bi[1]:
                continue
            try:
                if gi.touches(gj) or (gi.intersects(gj) and not gi.disjoint(gj)):
                    G.add_edge(nombres[i], nombres[j])
            except Exception:
                try:
                    if gi.buffer(0).touches(gj.buffer(0)):
                        G.add_edge(nombres[i], nombres[j])
                except Exception:
                    pass
    return G


def asignar_atributos(G: nx.Graph, df_counts: pd.DataFrame, df_subtypes: pd.DataFrame) -> nx.Graph:
    crime_map = {
        k.upper().strip(): v
        for k, v in df_counts.set_index("DIST_HECHO")["Crime_Count"].to_dict().items()
    }
    sub_map: Dict[str, Dict] = {}
    for _, row in df_subtypes.iterrows():
        key = row["DIST_HECHO"].upper().strip()
        sub_map.setdefault(key, {})
        sub_map[key][row["SUB_TIPO"]] = row["Subtype_Crime_Count"]

    for node in G.nodes():
        norm = node.upper().strip()
        G.nodes[node]["Crime_Count"] = crime_map.get(norm, 0)
        G.nodes[node]["Crime_Subtypes"] = sub_map.get(norm, {})

    for u, v in G.edges():
        G.edges[u, v]["weight"] = G.nodes[u]["Crime_Count"] + G.nodes[v]["Crime_Count"]

    return G


def calcular_centralidad(G: nx.Graph, df_counts: pd.DataFrame) -> pd.DataFrame:
    deg = nx.degree_centrality(G)
    btw = nx.betweenness_centrality(G, normalized=True)
    clo = nx.closeness_centrality(G)

    df_c = pd.DataFrame({
        "District": list(deg.keys()),
        "Degree Centrality": list(deg.values()),
        "Betweenness Centrality": [btw[n] for n in deg],
        "Closeness Centrality": [clo[n] for n in deg],
    })

    df_c["_norm"] = df_c["District"].str.upper().str.strip()
    tmp = df_counts.copy()
    tmp["_norm"] = tmp["DIST_HECHO"].str.upper().str.strip()
    df_c = df_c.merge(tmp[["_norm", "Crime_Count"]], on="_norm", how="left").fillna({"Crime_Count": 0})
    df_c.drop(columns=["_norm"], inplace=True)
    df_c["Crime_Count"] = df_c["Crime_Count"].astype(int)
    return df_c


def categorizar_distritos(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    df = df.copy()
    counts = df["Crime_Count"]
    max_val = int(counts.max()) if len(counts) > 0 else 0

    if max_val == 0:
        q_high, q_med = 1, 1
    else:
        q_high = max(1, int(counts.quantile(0.75)))
        q_med  = max(1, int(counts.quantile(0.50)))
        if q_high <= q_med:
            q_high = q_med + max(1, int(max_val * 0.1))

    df["Crime_Category"] = "Low Crime"
    df.loc[counts >= q_high, "Crime_Category"] = "High Crime"
    df.loc[(counts >= q_med) & (counts < q_high), "Crime_Category"] = "Medium Crime"

    d_high = float(df["Degree Centrality"].quantile(0.75)) if not df.empty else 0.0
    d_med  = float(df["Degree Centrality"].quantile(0.50)) if not df.empty else 0.0
    df["Connectivity_Category"] = "Low Connectivity"
    df.loc[df["Degree Centrality"] >= d_med,  "Connectivity_Category"] = "Medium Connectivity"
    df.loc[df["Degree Centrality"] >= d_high, "Connectivity_Category"] = "High Connectivity"

    thresholds = {
        "crime": {"high": q_high, "medium": q_med},
        "connectivity": {"high": d_high, "medium": d_med},
    }
    return df, thresholds


# ─────────────────────────── RENDER ────────────────────────────────
def _get_positions(gdf_dep: gpd.GeoDataFrame) -> Dict[str, Tuple[float, float]]:
    pos = {}
    for _, row in gdf_dep.iterrows():
        if row.geometry is None or row.geometry.is_empty:
            continue
        pt = row.geometry.representative_point()
        pos[row["NOMBDIST"]] = (float(pt.x), float(pt.y))
    return pos


def graficar_grafo(
    G: nx.Graph,
    df_centrality: pd.DataFrame,
    department: str,
    color_mode: str = "cases",
    node_positions: Optional[Dict] = None,
) -> str:
    """Renderiza el grafo con Matplotlib y guarda PNG. Retorna la ruta."""
    output_dir = "grafos_generados"
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_dir, f"grafo_{department.lower().replace(' ', '_')}_{ts}.png")

    palette = CRIME_PALETTE if color_mode != "connectivity" else CONN_PALETTE
    cat_key = "Crime_Category" if color_mode != "connectivity" else "Connectivity_Category"

    df_look = (
        df_centrality
        .assign(_n=lambda d: d["District"].str.upper().str.strip())
        .drop_duplicates("_n")
        .set_index("_n")
    )

    # Posiciones geográficas normalizadas
    if node_positions:
        xs = [v[0] for v in node_positions.values()]
        ys = [v[1] for v in node_positions.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        rx = max_x - min_x or 1
        ry = max_y - min_y or 1
        pos = {
            n: (0.05 + (node_positions[n][0] - min_x) / rx * 0.9,
                0.05 + (node_positions[n][1] - min_y) / ry * 0.9)
            if n in node_positions else (0.5, 0.5)
            for n in G.nodes()
        }
    else:
        pos = nx.kamada_kawai_layout(G)

    max_cases = max((df_look.loc[n.upper().strip(), "Crime_Count"]
                     if n.upper().strip() in df_look.index else 0
                     for n in G.nodes()), default=1) or 1

    node_colors, node_sizes, labels = [], [], {}
    for n in G.nodes():
        norm = n.upper().strip()
        row = df_look.loc[norm] if norm in df_look.index else None
        cc = int(row["Crime_Count"]) if row is not None else 0
        cat = row[cat_key] if row is not None else list(palette.keys())[0]
        node_colors.append(palette.get(cat, "#94A3B8"))
        node_sizes.append(600 + (cc / max_cases) * 800)
        labels[n] = n

    # Anchos de aristas proporcionales al peso
    weights = [G.edges[u, v].get("weight", 1) for u, v in G.edges()]
    min_w = min(weights) if weights else 1
    max_w = max(weights) if weights else 1
    edge_widths = [
        0.5 + (w - min_w) / (max_w - min_w + 1e-9) * 3
        for w in weights
    ]

    fig, ax = plt.subplots(figsize=(14, 10), dpi=130, facecolor="#081425")
    ax.set_facecolor("#081425")

    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#2C4A70", width=edge_widths, alpha=0.75)
    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_color=node_colors, node_size=node_sizes,
        linewidths=1.5, edgecolors="#0F172A",
    )
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                            font_size=7, font_color="white", font_weight="bold")

    # Leyenda
    from matplotlib.lines import Line2D
    legend_items = [
        Line2D([0], [0], marker="o", color="w", label=k,
               markerfacecolor=v, markersize=10)
        for k, v in palette.items()
    ]
    ax.legend(handles=legend_items, loc="lower left",
              frameon=True, framealpha=0.85,
              facecolor="#0F2238", edgecolor="#1E3A5F",
              labelcolor="white", fontsize=9)

    ax.set_title(
        f"ÁRBOL DE EXPANSIÓN TERRITORIAL DEL DELITO\n{department.upper()}",
        color="white", fontsize=12, fontweight="bold", pad=10
    )
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", facecolor=fig.get_facecolor(), dpi=130)
    plt.close(fig)
    return out_path


# ─────────────────────────── ESTADÍSTICAS ──────────────────────────
def resumir_estadisticas(df_filtered: pd.DataFrame, G: nx.Graph) -> Dict:
    total = len(df_filtered)
    sub = df_filtered["SUB_TIPO"].astype(str).str.upper().str.strip()
    extorsion = int((sub == "EXTORSION").sum())
    homicidio = int((sub == "HOMICIDIO").sum())

    modal = df_filtered["MODALIDAD"].fillna("").astype(str).str.upper()
    sicariato = int(modal.isin(
        {"SICARIATO", "CONSPIRACION Y OFRECIMIENTO PARA EL DELITO DE SICARIATO"}
    ).sum())

    densidad = float(nx.density(G)) if G.number_of_nodes() > 1 else 0.0
    grados = [d for _, d in G.degree()]
    grado_prom = float(np.mean(grados)) if grados else 0.0

    return {
        "nodos": G.number_of_nodes(),
        "aristas": G.number_of_edges(),
        "casos_totales": total,
        "extorsion": extorsion,
        "homicidio": homicidio,
        "sicariato": sicariato,
        "densidad": densidad,
        "grado_promedio": grado_prom,
    }


def construir_leyenda(color_mode: str, thresholds: Dict) -> List[Dict]:
    if color_mode == "connectivity":
        lim = thresholds.get("connectivity", {})
        high, med = lim.get("high", 0), lim.get("medium", 0)
        return [
            {"color": "#38BDF8", "label": f"Alta conectividad (≥{high:.2f})"},
            {"color": "#FACC15", "label": f"Media (≥{med:.2f})"},
            {"color": "#94A3B8", "label": f"Baja (<{med:.2f})"},
        ]
    lim = thresholds.get("crime", {})
    high, med = max(int(lim.get("high", 1)), 1), max(int(lim.get("medium", 1)), 1)
    return [
        {"color": "#E7000B", "label": f"Alta (≥{high} casos)"},
        {"color": "#FF6900", "label": f"Media ({med}–{high-1} casos)"},
        {"color": "#00B8DB", "label": f"Baja (<{med} casos)"},
    ]


# ─────────────────────────── API PRINCIPAL ─────────────────────────
def generar_grafo_territorial(
    df: pd.DataFrame,
    gdf: gpd.GeoDataFrame,
    department: str,
    crime_type: str,
    year: str,
    color_mode: str = "cases",
    abrir_archivo: bool = False,
) -> Dict:
    if not department:
        raise ValueError("Selecciona un departamento válido.")

    df_filtered = filtrar_dataframe(df, department, crime_type, year)
    if df_filtered.empty:
        raise ValueError(f"Sin registros para '{department}' — '{crime_type}' — {year}.")

    df_counts, df_subtypes = obtener_conteos(df_filtered)

    dep_norm = _normalizar_dpto(department)
    if dep_norm == "LIMA":
        mask = gdf["NOMBDEP"].str.upper().str.strip().isin(LIMA_ALIAS | {"LIMA"})
    else:
        mask = gdf["NOMBDEP"].str.upper().str.strip() == dep_norm

    gdf_dep = gdf[mask].copy().reset_index(drop=True)
    if gdf_dep.empty:
        raise ValueError(f"Sin geometrías para '{department}'.")

    node_positions = _get_positions(gdf_dep)
    G = construir_grafo(gdf_dep)
    if G.number_of_nodes() == 0:
        raise RuntimeError("El grafo quedó vacío.")

    G = asignar_atributos(G, df_counts, df_subtypes)
    df_centrality = calcular_centralidad(G, df_counts)
    df_centrality, thresholds = categorizar_distritos(df_centrality)

    image_path = graficar_grafo(G, df_centrality, department, color_mode, node_positions)
    legend = construir_leyenda(color_mode, thresholds)
    stats  = resumir_estadisticas(df_filtered, G)

    return {
        "image_path":     image_path,
        "graph":          G,
        "centralidad":    df_centrality,
        "stats":          stats,
        "legend":         legend,
        "thresholds":     thresholds,
        "graph_title":    f"Grafo de Distritos — {department.title()}",
        "graph_subtitle": f"{stats['nodos']} distritos | {stats['aristas']} conexiones territoriales",
    }
