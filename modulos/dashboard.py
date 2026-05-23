# modulos/dashboard.py — Dashboard mejorado UNMASK v2
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os


def _normalizar_departamento(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["DPTO_HECHO_NEW"] = (
        df["DPTO_HECHO_NEW"]
        .fillna("SIN REGISTRO")
        .astype(str)
        .str.upper()
        .str.strip()
    )
    # Unificar alias de Lima
    lima_alias = {"LIMA METROPOLITANA", "REGION LIMA"}
    df.loc[df["DPTO_HECHO_NEW"].isin(lima_alias), "DPTO_HECHO_NEW"] = "LIMA"
    return df


def calcular_metricas(df: pd.DataFrame) -> dict:
    """Calcula todas las métricas principales del dashboard."""
    df = _normalizar_departamento(df)

    total_casos = len(df)
    distritos_afectados = df["DIST_HECHO"].nunique()

    casos_extorsion = int(df[df["SUB_TIPO"] == "EXTORSION"].shape[0])
    casos_homicidio = int(df[df["SUB_TIPO"] == "HOMICIDIO"].shape[0])

    # Sicariato por modalidad
    col_modal = df["MODALIDAD"].fillna("").astype(str).str.upper()
    casos_sicariato = int(
        col_modal.isin(
            {"SICARIATO", "CONSPIRACION Y OFRECIMIENTO PARA EL DELITO DE SICARIATO"}
        ).sum()
    )

    # Top 5 departamentos por extorsión + homicidio
    df_criticos = df[df["SUB_TIPO"].isin(["EXTORSION", "HOMICIDIO"])]
    top5 = (
        df_criticos.groupby("DPTO_HECHO_NEW")
        .size()
        .reset_index(name="casos")
        .sort_values("casos", ascending=False)
        .head(5)
    )
    top_departamentos = dict(zip(top5["DPTO_HECHO_NEW"], top5["casos"]))

    # Alerta nacional: top 2 departamentos
    if len(top5) >= 2:
        top2_nombres = top5.head(2)["DPTO_HECHO_NEW"].tolist()
        top2_casos = int(top5.head(2)["casos"].sum())
        total_criticos = casos_extorsion + casos_homicidio
        pct = (top2_casos / total_criticos * 100) if total_criticos > 0 else 0
        alerta = (
            f"Se registró un incremento en casos de sicariato. "
            f"{' y '.join(top2_nombres)} concentran el {pct:.1f}% "
            f"de los casos de extorsión y homicidio a nivel nacional."
        )
    else:
        alerta = "Revisa la base de datos SIDPOL para más información."

    return {
        "total_casos": total_casos,
        "distritos_afectados": distritos_afectados,
        "casos_extorsion": casos_extorsion,
        "casos_homicidio": casos_homicidio,
        "casos_sicariato": casos_sicariato,
        "top_departamentos": top_departamentos,
        "alerta": alerta,
    }


def generar_mapa_calor(
    df: pd.DataFrame,
    geojson_path: str = "data/peru_departamental_simple.geojson",
    save_path: str = None,
) -> str:
    """Genera el mapa de calor territorial y lo guarda como PNG. Retorna la ruta."""
    df = _normalizar_departamento(df)
    df_criticos = df[df["SUB_TIPO"].isin(["EXTORSION", "HOMICIDIO"])]

    conteo = (
        df_criticos.groupby("DPTO_HECHO_NEW")
        .size()
        .reset_index(name="Crime_Count")
    )

    peru_gdf = gpd.read_file(geojson_path)
    peru_gdf["NOMBDEP"] = peru_gdf["NOMBDEP"].str.upper().str.strip()

    # Unificar Lima en GDF
    lima_alias = {"LIMA METROPOLITANA", "REGION LIMA"}
    peru_gdf.loc[peru_gdf["NOMBDEP"].isin(lima_alias), "NOMBDEP"] = "LIMA"

    merged = peru_gdf.merge(
        conteo, left_on="NOMBDEP", right_on="DPTO_HECHO_NEW", how="left"
    )
    merged["Crime_Count"] = merged["Crime_Count"].fillna(0).astype(int)

    try:
        merged_proj = merged.to_crs(epsg=3857)
    except Exception:
        merged_proj = merged

    valores = merged_proj["Crime_Count"]
    max_val = int(valores.max()) if len(valores) > 0 else 0

    if max_val == 0:
        merged_proj["color"] = "#FAD1C8"
        legend_levels = ["Sin registros"]
        color_map = {"Sin registros": "#FAD1C8"}
    else:
        q40 = int(np.percentile(valores[valores > 0], 40)) if (valores > 0).any() else 1
        q75 = int(np.percentile(valores[valores > 0], 75)) if (valores > 0).any() else 2
        if q40 <= 0:
            q40 = 1
        if q75 <= q40:
            q75 = q40 + max(1, int(max_val * 0.1))

        fmt = lambda x: f"{int(round(x)):,}".replace(",", ".")
        legend_levels = [
            f"Bajo (≤{fmt(q40)})",
            f"Medio ({fmt(q40+1)}–{fmt(q75)})",
            f"Alto (>{fmt(q75)})",
        ]
        palette = ["#FFE0D0", "#F4846A", "#B3001B"]
        color_map = dict(zip(legend_levels, palette))

        categorias = pd.cut(
            valores,
            bins=[-np.inf, q40, q75, np.inf],
            labels=legend_levels,
            include_lowest=True,
        )
        merged_proj = merged_proj.copy()
        merged_proj["color"] = categorias.astype(str).map(color_map).fillna("#FAD1C8")

    fig, ax = plt.subplots(1, 1, figsize=(10, 12), facecolor="#0A1628")
    ax.set_facecolor("#0A1628")

    merged_proj.plot(ax=ax, color=merged_proj["color"], edgecolor="#1E3A5F", linewidth=0.7)

    for _, row in merged_proj.iterrows():
        if row["Crime_Count"] > 0:
            try:
                pt = row.geometry.representative_point()
                ax.annotate(
                    f"{row['Crime_Count']:,}".replace(",", "."),
                    xy=(pt.x, pt.y),
                    ha="center", va="center",
                    fontsize=6.5, fontweight="bold",
                    color="white" if row["Crime_Count"] >= 1000 else "#CCCCCC",
                )
            except Exception:
                pass

    ax.set_axis_off()

    from matplotlib.patches import Patch
    handles = [Patch(facecolor=color_map[l], edgecolor="#444", label=l) for l in legend_levels]
    leg = ax.legend(
        handles=handles, loc="lower left",
        bbox_to_anchor=(0.02, 0.02),
        frameon=True, framealpha=0.85,
        facecolor="#0F2238", edgecolor="#1E3A5F",
        labelcolor="white", fontsize=8,
    )

    plt.tight_layout(pad=0)

    if not save_path:
        save_path = "img/mapa_dashboard.png"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return save_path
