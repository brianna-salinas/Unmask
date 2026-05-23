# Modulos/B_dashboard.py
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from modulos.utils import normalize_text, resolve_crime_filter

#METRICAS PRINCIPALES
def calcular_total_nacional(df):
    """Total de casos en el dataset, usando n_dist_ID_DGC si existe."""
    if 'n_dist_ID_DGC' in df.columns:
        return int(df['n_dist_ID_DGC'].sum())
    return int(df.shape[0])

def calcular_distritos_afectados(df, tipos_crimen=['EXTORSION', 'HOMICIDIO']):
    total_unique_districts = df['DIST_HECHO'].nunique()

    tipos_norm = {normalize_text(t) for t in tipos_crimen}
    df_filtrado = df[df['SUB_TIPO'].astype(str).apply(normalize_text).isin(tipos_norm)]
    total_distritos = df_filtrado['DIST_HECHO'].nunique()
    total_departamentos = df_filtrado['DPTO_HECHO_NEW'].nunique()

    porcentaje = (total_distritos / total_unique_districts) * 100 if total_unique_districts > 0 else 0
    return total_distritos, total_departamentos, porcentaje

def contar_casos(df, tipo_crimen):
    """Cuenta el número de casos de un tipo específico de crimen."""
    tipo_norm = normalize_text(tipo_crimen)
    df_filtrado = df[df['SUB_TIPO'].astype(str).apply(normalize_text) == tipo_norm]
    if 'n_dist_ID_DGC' in df.columns:
        return int(df_filtrado['n_dist_ID_DGC'].sum())
    return int(df_filtrado.shape[0])

def contar_casos_modalidad(df, modalidades=None):
    """Cuenta casos por modalidad, aceptando múltiples etiquetas."""
    if 'MODALIDAD' not in df.columns:
        return 0

    if modalidades is None:
        modalidades = [
            'SICARIATO',
            'CONSPIRACION Y OFRECIMIENTO PARA EL DELITO DE SICARIATO'
        ]

    modalidades_norm = {normalize_text(m) for m in modalidades}
    col = df['MODALIDAD'].fillna('').astype(str).apply(normalize_text)
    df_filtrado = df[col.isin(modalidades_norm)]
    if 'n_dist_ID_DGC' in df_filtrado.columns:
        return int(df_filtrado['n_dist_ID_DGC'].sum())
    return int(df_filtrado.shape[0])

# TOP 5 DEPARTAMENTOS
def top_5_departamentos(df, anios=None, top_n=5):
    crime_volume = _agrupar_crimenes_por_departamento(
        df,
        anios=anios,
        subtipos=['EXTORSION', 'HOMICIDIO']
    )

    ranking = crime_volume.sort_values('Crime_Count', ascending=False).head(top_n)
    series = pd.Series(
        data=ranking['Crime_Count'].values,
        index=ranking['DPTO_HECHO_NEW']
    )

    periodo_str = (
        f" ({min(anios)}-{max(anios)})" if anios else ""
    )
    print(
        f"\nTop {top_n} Departamentos con mayor volumen de Extorsión y Homicidio{periodo_str}:"
    )
    print(series)

    return series

# ALERTA NACIONAL
def alerta_nacional(df, anio=2025):
    # Filtrar por año
    df_anio = df[df['ANIO'] == anio]
    
    # Métricas principales
    total_nacional_casos = calcular_total_nacional(df_anio)
    total_unique_districts_nacional = df_anio['DIST_HECHO'].nunique()
    
    # Filtrar solo Extorsión y Homicidio
    crimes_for_count = ['EXTORSION', 'HOMICIDIO']
    crimes_norm = {normalize_text(c) for c in crimes_for_count}
    df_specific_crimes = df_anio[df_anio['SUB_TIPO'].astype(str).apply(normalize_text).isin(crimes_norm)]
    
    total_distritos_afectados = df_specific_crimes['DIST_HECHO'].nunique()
    num_departamentos_afectados = df_specific_crimes['DPTO_HECHO_NEW'].nunique()
    
    porcentaje_distritos_afectados = (total_distritos_afectados / total_unique_districts_nacional * 100
        if total_unique_districts_nacional > 0 else 0)
    
    # Casos por tipo
    casos_homicidio = contar_casos(df_anio, 'HOMICIDIO')
    casos_extorsion = contar_casos(df_anio, 'EXTORSION')
    
    # Top 5 departamentos
    top_5_departments = (
        df_specific_crimes['DPTO_HECHO_NEW']
        .astype(str)
        .apply(normalize_text)
        .value_counts()
        .head(5)
    )
    
    # Top 2 departamentos para concentración de casos
    top_2_departments_cases = top_5_departments.head(2).sum()
    total_specific_crimes_cases = casos_homicidio + casos_extorsion
    percentage_top_departments = ((top_2_departments_cases / total_specific_crimes_cases) * 100
    if total_specific_crimes_cases > 0 else 0)
    top_2_departments_names = top_5_departments.head(2).index.tolist()
    departamentos_concentracion_str = " y ".join(top_2_departments_names)
    
    # Crear mensaje de alerta
    mensaje_alerta = (
        f"\nALERTA CRÍTICA NACIONAL: \n"
        f"Total de denuncias SIDPOL en {anio}: {total_nacional_casos}. \n"
        f"Se han identificado {casos_homicidio} casos de Homicidio y {casos_extorsion} casos de Extorsión. \n"
        f"{departamentos_concentracion_str} concentran aproximadamente el "
        f"{percentage_top_departments:.2f}% de los casos de Homicidio y Extorsión a nivel nacional en {anio}, "
        "lo que indica puntos críticos de atención.\n"
    )
    
    print(mensaje_alerta)
    return mensaje_alerta


def _agrupar_crimenes_por_departamento(
    df,
    anios=None,
    subtipos=None,
    columna='DPTO_HECHO_NEW'
):
    """Devuelve DataFrame con columnas departamento y Crime_Count normalizadas."""
    data = df.copy()

    if anios is not None:
        data = data[data['ANIO'].isin(anios)]
    if subtipos is not None:
        subtipos_norm = {normalize_text(s) for s in subtipos}
        data = data[data['SUB_TIPO'].astype(str).apply(normalize_text).isin(subtipos_norm)]

    if 'n_dist_ID_DGC' in data.columns:
        conteo = (
            data.groupby(columna, dropna=False)['n_dist_ID_DGC']
            .sum()
            .reset_index(name='Crime_Count')
        )
    else:
        conteo = (
            data.groupby(columna, dropna=False)
            .size()
            .reset_index(name='Crime_Count')
        )

    conteo[columna] = (
        conteo[columna]
        .fillna('SIN REGISTRO')
        .astype(str)
        .apply(normalize_text)
    )

    lima_alias = {'LIMA', 'LIMA METROPOLITANA', 'REGION LIMA'}
    lima_total = conteo[conteo[columna].isin(lima_alias)]['Crime_Count'].sum()
    conteo = conteo[~conteo[columna].isin(lima_alias)].copy()
    if lima_total > 0:
        conteo = pd.concat(
            [conteo, pd.DataFrame([{columna: 'LIMA', 'Crime_Count': int(lima_total)}])],
            ignore_index=True
        )

    conteo = conteo.groupby(columna, as_index=False)['Crime_Count'].sum()
    return conteo


# MAPA DE CALOR
def mapa_calor_crimenes(
    df,
    geojson_path='data/peru_departamental_simple.geojson',
    anios=[2024, 2025],
    save_path=None,
    show_plot=True
):
    """
    Genera un mapa de calor por departamento para Extorsión y Homicidio.

    - Si save_path es un string, guarda la figura como PNG en esa ruta.
    - Si show_plot es True, muestra la ventana de Matplotlib; si es False, no la muestra.
    """
    crime_volume = _agrupar_crimenes_por_departamento(
        df,
        anios=anios,
        subtipos=['EXTORSION', 'HOMICIDIO']
    )

    # Cargar GeoJSON y merge
    peru_gdf = gpd.read_file(geojson_path)
    peru_gdf['NOMBDEP'] = peru_gdf['NOMBDEP'].astype(str).apply(normalize_text)
    crime_volume['DPTO_HECHO_NEW'] = crime_volume['DPTO_HECHO_NEW'].astype(str).apply(normalize_text)
    merged_gdf = peru_gdf.merge(
        crime_volume,
        left_on='NOMBDEP',
        right_on='DPTO_HECHO_NEW',
        how='left'
    )

    merged_gdf['Crime_Count'] = merged_gdf['Crime_Count'].fillna(0).astype(int)
    merged_gdf_proj = merged_gdf.to_crs(epsg=3857)

    # ---------- CLASIFICACIÓN DINÁMICA (tonos rojos) ----------
    valores = merged_gdf_proj['Crime_Count']
    max_val = int(valores.max())

    if max_val == 0:
        legend_levels = ['Sin registros']
        color_map = {'Sin registros': '#FAD1C8'}
        merged_gdf_proj['categoria_riesgo'] = legend_levels[0]
        merged_gdf_proj['color'] = color_map[legend_levels[0]]
    else:
        q_bajo = int(np.percentile(valores, 40))
        q_alto = int(np.percentile(valores, 75))

        # Evitar cortes iguales para que siempre exista un tramo "alto"
        if q_bajo <= 0:
            q_bajo = 1
        if q_alto <= q_bajo:
            q_alto = q_bajo + max(1, int(max_val * 0.1))

        fmt_num = lambda x: f"{int(round(x)):,}".replace(',', '.')
        legend_levels = [
            f"Riesgo Bajo (≤{fmt_num(q_bajo)})",
            f"Riesgo Medio ({fmt_num(q_bajo + 1)}–{fmt_num(q_alto)})",
            f"Riesgo Alto (>{fmt_num(q_alto)})",
        ]
        legend_colors = ['#FFE5D9', '#F59C9C', '#B3001B']  # claros → oscuro
        color_map = dict(zip(legend_levels, legend_colors))

        merged_gdf_proj['categoria_riesgo'] = pd.cut(
            valores,
            bins=[-float('inf'), q_bajo, q_alto, float('inf')],
            labels=legend_levels,
            include_lowest=True
        )
        # Convertir a str para evitar el error "Cannot setitem on a Categorical"
        merged_gdf_proj['color'] = merged_gdf_proj['categoria_riesgo'].astype(str).map(color_map).fillna('#FAD1C8')

    # ---------- PLOT ----------
    fig, ax = plt.subplots(1, 1, figsize=(13, 7.5))

    merged_gdf_proj.plot(
        ax=ax,
        color=merged_gdf_proj['color'],
        edgecolor='0.8',
        linewidth=0.8
    )

    # Anotaciones de valores
    for geom, label in zip(merged_gdf_proj.geometry, merged_gdf_proj['Crime_Count']):
        point = geom.representative_point()
        ax.annotate(
            str(label),
            xy=(point.x, point.y),
            xytext=(0, 0),
            textcoords="offset points",
            ha='center',
            va='center',
            fontsize=7,
            color='white' if label >= 1000 else 'black'
        )

    ax.set_axis_off()

    # Leyenda manual que sí coincide con los colores
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=color_map[label], edgecolor='k', label=label)
        for label in legend_levels
    ]

    legend = ax.legend(
        handles=legend_elements,
        loc='lower left',
        bbox_to_anchor=(0.02, 0.02),
        ncol=len(legend_elements),
        frameon=False
    )
    for text in legend.get_texts():
        text.set_fontsize(9)

    plt.tight_layout()

    # Guardar PNG si corresponde
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')

    # Mostrar o cerrar según flag
    if show_plot:
        plt.show()
    else:
        plt.close(fig)

    return merged_gdf_proj


def mostrar_dashboard(df, render_map=True, map_kwargs=None):
    # Métricas principales
    total_nacional = calcular_total_nacional(df)
    distritos_afectados, departamentos_afectados, porcentaje = calcular_distritos_afectados(df)
    casos_homicidio = contar_casos(df, 'HOMICIDIO')
    casos_extorsion = contar_casos(df, 'EXTORSION')
    casos_sicariato = contar_casos_modalidad(df)
    
    print("\n--- DASHBOARD ---")
    print(f"\nTOTAL NACIONAL de denuncias SIDPOL (2024-2025): {total_nacional}")
    print(f"Distritos afectados por Extorsión o Homicidio: {distritos_afectados}")
    print(f"Departamentos afectados: {departamentos_afectados} ({porcentaje:.2f}% del Perú)")
    print(f"Casos de Homicidio: {casos_homicidio}")
    print(f"Casos de Extorsión: {casos_extorsion}")
    print(f"Casos de Sicariato: {casos_sicariato}")
    
    # top 5 departamentos
    anios_analisis = [2024, 2025]
    top_departments = top_5_departamentos(df, anios=anios_analisis)
    
    # Mostrar alerta nacional 2025
    mensaje_alerta = alerta_nacional(df, anio=2025)
    
    # mapa de calor
    if render_map:
        mapa_args = map_kwargs.copy() if map_kwargs else {}
        mapa_args.setdefault('anios', anios_analisis)
        mapa_calor_crimenes(df, **mapa_args)
    
    # Retornar todas las métricas y datos útiles
    return {
        "total_casos": total_nacional,
        "distritos_afectados": distritos_afectados,
        "departamentos_afectados": departamentos_afectados,
        "porcentaje_distritos": porcentaje,
        "casos_homicidio": casos_homicidio,
        "casos_extorsion": casos_extorsion,
        "casos_sicariato": casos_sicariato,
        "top_departamentos": top_departments,
        "alerta_nacional": mensaje_alerta
    }