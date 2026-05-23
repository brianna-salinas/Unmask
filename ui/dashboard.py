import os
import tkinter as tk
from tkinter import Canvas, messagebox, ttk, scrolledtext
from datetime import datetime

from PIL import Image, ImageTk

from modulos import B_dashboard, B_explorar_grafo, B_algoritmos, B_resultados
from ui.config import (
    ANCHO,
    ALTO,
    COLOR_FONDO,
    COLOR_UNMASK,
    COLOR_DORADO,
    DF_SIDPOL,
    GDF_GEO,
    FUENTE_LABEL,
    ULTIMO_FILTRO_ALGORITMOS,
)
from ui.helpers import aplicar_icono, centrar


def dashboard(usuario):
    dash = tk.Tk()
    aplicar_icono(dash)
    dash.title("UNMASK — Dashboard")
    centrar(dash, ANCHO, ALTO)

    dash.config(bg="#101a2d")

    panel = tk.Frame(dash, bg="#0F2238", width=250, height=ALTO)
    panel.place(x=0, y=0)

    try:
        logo = tk.PhotoImage(file="img/un.png")
        panel.logo_img = logo
        tk.Label(panel, image=logo, bg="#0F2238").place(x=10, y=10)
    except Exception:
        tk.Label(panel, text="[logo]", bg="#0F2238", fg="white").place(x=10, y=10)

    tk.Label(
        panel,
        text="UNMASK\nSIDPOL 25",
        fg="white",
        bg="#0F2238",
        font=("Segoe UI", 18, "bold"),
        justify="left"
    ).place(x=85, y=18)

    main = tk.Frame(dash, bg="#eef2f6", width=ANCHO-250, height=ALTO)
    main.place(x=250, y=0)

    titulo_seccion = tk.Label(
        main,
        text="Dashboard",
        fg="#052749",
        bg="#eef2f6",
        font=("Segoe UI", 26, "bold")
    )
    titulo_seccion.place(x=25, y=20)

    subtitulo_seccion = tk.Label(
        main,
        text="Resumen general de extorsión y sicariato en el Perú - SIDPOL 2025",
        fg="#4a5d73",
        bg="#eef2f6",
        font=("Segoe UI", 11)
    )
    subtitulo_seccion.place(x=25, y=60)

    contenido = tk.Frame(main, bg="#eef2f6", width=ANCHO-250, height=ALTO-90)
    contenido.place(x=0, y=90)

    def limpiar():
        for w in contenido.winfo_children():
            w.destroy()

    boton_activo = None

    encabezados = {
        "Dashboard": (
            "Dashboard",
            "Resumen general de extorsión y sicariato en el Perú - SIDPOL 2025"
        ),
        "Grafo Territorial": (
            "Explorar Grafo Territorial",
            "Visualización del grafo de distritos sin aplicar algoritmos — Solo exploración visual"
        ),
        "Algoritmos": (
            "Algoritmos avanzados",
            "Ejecuta MST, Floyd-Warshall, BFS/DFS desde main.py en consola"
        ),
        "Resultados": (
            "Resultados estratégicos",
            "Genera el informe ejecutivo detallado desde la opción correspondiente en consola"
        ),
    }

    def actualizar_encabezado(nombre):
        titulo, subtitulo = encabezados.get(nombre, (nombre, ""))
        titulo_seccion.config(text=titulo)
        subtitulo_seccion.config(text=subtitulo)

    def cambiar_seccion(nombre, boton_widget):
        nonlocal boton_activo

        limpiar()

        boton_widget.config(
            bg="white",
            fg="#1E3A5F",
            bd=2,
            relief="solid"
        )

        if boton_activo and boton_activo != boton_widget:
            boton_activo.config(
                bg="#0F2238",
                fg="white",
                bd=0,
                relief="flat"
            )

        boton_activo = boton_widget

        actualizar_encabezado(nombre)

        if nombre == "Dashboard":
            cargar_dashboard()
        elif nombre == "Grafo Territorial":
            cargar_grafo_territorial()
        elif nombre == "Algoritmos":
            cargar_algoritmos()
        elif nombre == "Resultados":
            cargar_resultados()

    botones = [
        "Dashboard",
        "Grafo Territorial",
        "Algoritmos",
        "Resultados"
    ]

    botones_refs = []

    pos_y = 160
    for name in botones:
        b = tk.Label(
            panel,
            text=name,
            fg="white",
            bg="#0F2238",
            font=("Segoe UI", 14, "bold"),
            width=18,
            height=2,
            cursor="hand2"
        )
        b.place(x=20, y=pos_y)
        botones_refs.append(b)
        b.bind("<Button-1>", lambda e, n=name, w=b: cambiar_seccion(n, w))
        pos_y += 60

    def cargar_dashboard():
        limpiar()

        def card(x, title, valor_texto="---"):
            f = tk.Frame(contenido, bg="white", width=210, height=90)
            f.place(x=x, y=20)

            tk.Label(
                f, text=title, bg="white", fg="#3A5875",
                font=("Segoe UI", 11, "bold")
            ).place(x=15, y=10)

            tk.Label(
                f, text=valor_texto, bg="white", fg="#152d41",
                font=("Segoe UI", 24, "bold")
            ).place(x=15, y=40)

        met = B_dashboard.mostrar_dashboard(DF_SIDPOL, render_map=False)
        card(25,  "Total Nacional", f"{met['total_casos']:,}".replace(",", "."))
        card(260, "Distritos Analizados", f"{met['distritos_afectados']:,}".replace(",", "."))
        card(495, "Casos de Sicariato", f"{met['casos_sicariato']:,}".replace(",", "."))
        card(730, "Casos de Extorsión", f"{met['casos_extorsion']:,}".replace(",", "."))

        mapa = tk.Frame(contenido, bg="white", width=650, height=600)
        mapa.place(x=25, y=140)

        tk.Label(
            mapa, text="Mapa de Riesgo Territorial",
            fg="#052749", bg="white",
            font=("Segoe UI", 14, "bold")
        ).place(x=30, y=20)

        tk.Label(
            mapa,
            text="Distribución geográfica de extorsión y sicariato por departamento",
            fg="#526584", bg="white",
            font=("Segoe UI", 9)
        ).place(x=30, y=50)

        ruta_png_mapa = "img/mapa_dashboard.png"
        B_dashboard.mapa_calor_crimenes(
            DF_SIDPOL,
            save_path=ruta_png_mapa,
            show_plot=False
        )

        try:
            img = Image.open(ruta_png_mapa)
            img = img.resize((600, 480), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            mapa.tk_img = tk_img

            mapa_canvas = tk.Canvas(
                mapa,
                width=600,
                height=400,
                bg="white",
                highlightthickness=0
            )
            mapa_canvas.place(x=30, y=90)

            mapa_scroll = tk.Scrollbar(
                mapa,
                orient="vertical",
                command=mapa_canvas.yview
            )
            mapa_scroll.place(x=30 + 600 + 5, y=90, height=400)

            mapa_canvas.configure(yscrollcommand=mapa_scroll.set)
            mapa_canvas.create_image(0, 0, anchor="nw", image=tk_img)
            mapa_canvas.configure(scrollregion=(0, 0, tk_img.width(), tk_img.height()))

        except Exception as e:
            tk.Label(
                mapa,
                text=f"No se pudo cargar el mapa: {e}",
                fg="red", bg="white",
                font=("Segoe UI", 9, "italic")
            ).place(x=30, y=120)

        side = tk.Frame(contenido, bg="#eef2f6", width=260, height=400)
        side.place(x=690, y=140)

        card_analisis = tk.Frame(side, bg="white", width=240, height=120)
        card_analisis.place(x=10, y=0)

        tk.Label(
            card_analisis, text="Análisis Territorial",
            bg="white", fg="#052749",
            font=("Segoe UI", 12, "bold")
        ).place(x=15, y=10)

        tk.Label(
            card_analisis,
            text="Explora el grafo territorial y ejecuta algoritmos de análisis",
            bg="white", fg="#526584",
            wraplength=210, justify="left",
            font=("Segoe UI", 9)
        ).place(x=15, y=35)

        btn_grafo = tk.Button(
            card_analisis,
            text="Explorar Grafo →",
            bg="#007bff", fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            command=lambda: cambiar_seccion("Grafo Territorial", botones_refs[1])
        )
        btn_grafo.place(x=15, y=75, width=210, height=30)

        top = met["top_departamentos"]
        card_top = tk.Frame(side, bg="#111827", width=240, height=220)
        card_top.place(x=10, y=150)
        card_top.pack_propagate(False)

        tk.Label(
            card_top, text="Top 5 Departamentos",
            bg="#111827", fg="white",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=15, pady=(12, 6))

        for idx, (dept, valor) in enumerate(top.items(), start=1):
            fila = tk.Frame(card_top, bg="#1F2937", height=36)
            fila.pack(fill="x", padx=12, pady=4)

            tk.Label(
                fila,
                text=f"#{idx}",
                bg="#1F2937", fg="#FBBF24",
                font=("Segoe UI", 11, "bold")
            ).pack(side="left", padx=(10, 8))

            tk.Label(
                fila,
                text=dept,
                bg="#1F2937", fg="white",
                font=("Segoe UI", 10, "bold")
            ).pack(side="left", expand=True, anchor="w")

            tk.Label(
                fila,
                text=f"{valor:,}".replace(",", "."),
                bg="#1F2937", fg="#E5E7EB",
                font=("Segoe UI", 10)
            ).pack(side="right", padx=12)

    def cargar_grafo_territorial():
        limpiar()

        vista = tk.Frame(contenido, bg="#eef2f6", width=ANCHO-250, height=ALTO-90)
        vista.place(x=0, y=0, width=ANCHO-250, height=ALTO-90)

        opciones = B_explorar_grafo.obtener_opciones_filtros(DF_SIDPOL)

        filtros = tk.Frame(vista, bg="#081629", width=900, height=120)
        filtros.place(x=25, y=20)
        filtros.grid_propagate(False)
        for col in range(5):
            filtros.columnconfigure(col, weight=1)

        estilo = ttk.Style()
        try:
            estilo.theme_use("default")
        except Exception:
            pass
        estilo.configure(
            "Filtro.TCombobox",
            fieldbackground="#142541",
            background="#142541",
            foreground="white",
            borderwidth=0,
            relief="flat"
        )
        estilo.map(
            "Filtro.TCombobox",
            fieldbackground=[("readonly", "#142541")],
            foreground=[("readonly", "white")]
        )

        departamentos = opciones.get("departamentos", [])
        departamentos_display = [d.upper() for d in departamentos]
        depto_map = {display: original for display, original in zip(departamentos_display, departamentos)}

        tipo_opciones = opciones.get("tipo_delito", [])
        tipo_labels = [opt["label"].upper() for opt in tipo_opciones]
        anios = opciones.get("anios", [])

        tipo_map = {opt["label"].upper(): opt["value"] for opt in tipo_opciones}

        color_opciones = opciones.get("color_por", [])
        color_labels = [opt["label"].upper() for opt in color_opciones]
        color_map = {opt["label"].upper(): opt["value"] for opt in color_opciones}

        depto_var = tk.StringVar(value=departamentos_display[0] if departamentos_display else "")
        tipo_var = tk.StringVar(value=tipo_labels[0] if tipo_labels else "")
        anio_var = tk.StringVar(value=anios[-1] if anios else "")
        color_var = tk.StringVar(value=color_labels[0] if color_labels else "")

        def crear_selector(texto, columna, variable, valores):
            tk.Label(
                filtros,
                text=texto,
                bg="#081629",
                fg="#7DA3C9",
                font=("Segoe UI", 10, "bold")
            ).grid(row=0, column=columna, padx=12, pady=(15, 2), sticky="w")

            combo = ttk.Combobox(
                filtros,
                textvariable=variable,
                values=valores,
                state="readonly",
                style="Filtro.TCombobox"
            )
            combo.grid(row=1, column=columna, padx=12, pady=(0, 15), sticky="ew")
            if not valores:
                combo.configure(state="disabled")
            return combo

        crear_selector("Departamento", 0, depto_var, departamentos_display)
        crear_selector("Tipo de delito", 1, tipo_var, tipo_labels)
        crear_selector("Año", 2, anio_var, anios)
        crear_selector("Colorear por", 3, color_var, color_labels)

        btn_generar = tk.Button(
            filtros,
            text="Generar Grafo",
            bg="#12D0A5",
            fg="#051427",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            cursor="hand2"
        )
        btn_generar.grid(row=0, column=4, rowspan=2, padx=12, pady=15, sticky="nsew")

        grafo_card = tk.Frame(vista, bg="white", width=670, height=380)
        grafo_card.place(x=25, y=170)
        grafo_card.pack_propagate(False)

        titulo_grafo = tk.Label(
            grafo_card,
            text="Grafo de Distritos — Selecciona filtros",
            fg="#0A1B2E",
            bg="white",
            font=("Segoe UI", 15, "bold")
        )
        titulo_grafo.place(x=25, y=18)

        subtitulo_grafo = tk.Label(
            grafo_card,
            text="",
            fg="#5B708C",
            bg="white",
            font=("Segoe UI", 10)
        )
        subtitulo_grafo.place(x=25, y=52)

        estado_grafo = tk.Label(
            grafo_card,
            text="Selecciona filtros y presiona Generar Grafo",
            fg="#6B7280",
            bg="white",
            font=("Segoe UI", 9, "italic")
        )
        estado_grafo.place(x=25, y=80)

        imagen_lbl = tk.Label(grafo_card, bg="#030914", width=620, height=240)
        imagen_lbl.place(x=25, y=110, width=620, height=240)
        imagen_lbl.image = None

        leyenda_frame = tk.Frame(grafo_card, bg="white")
        leyenda_frame.place(x=25, y=330)

        derecha = tk.Frame(vista, bg="#eef2f6", width=230, height=360)
        derecha.place(x=720, y=170)

        info_card = tk.Frame(derecha, bg="#112744", width=230, height=110)
        info_card.pack(fill="x")
        tk.Label(
            info_card,
            text="Información del Nodo",
            bg="#112744",
            fg="white",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 6))
        tk.Label(
            info_card,
            text="Haz clic en un nodo del grafo para ver sus estadísticas",
            bg="#112744",
            fg="#C2D5F2",
            wraplength=190,
            justify="left",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=15)

        stats_card = tk.Frame(derecha, bg="white", width=230, height=230)
        stats_card.pack(fill="x", pady=15)
        tk.Label(
            stats_card,
            text="Estadísticas del Grafo",
            bg="white",
            fg="#0A1B2E",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))

        stats_fields = [
            ("Nodos (distritos)", "nodos"),
            ("Aristas (conexiones)", "aristas"),
            ("Casos totales", "casos_totales"),
            ("Extorsión", "extorsion"),
            ("Sicariato", "sicariato"),
            ("Densidad del grafo", "densidad"),
            ("Grado promedio", "grado_promedio"),
        ]

        stats_labels = {}
        for nombre, clave in stats_fields:
            fila = tk.Frame(stats_card, bg="white")
            fila.pack(fill="x", padx=15, pady=2)
            tk.Label(
                fila,
                text=nombre,
                bg="white",
                fg="#5B708C",
                font=("Segoe UI", 10)
            ).pack(side="left")
            valor = tk.Label(
                fila,
                text="--",
                bg="white",
                fg="#0A1B2E",
                font=("Segoe UI", 11, "bold")
            )
            valor.pack(side="right")
            stats_labels[clave] = valor

        ultima_actualizacion = tk.Label(
            stats_card,
            text="Actualizado: --",
            bg="white",
            fg="#94A3B8",
            font=("Segoe UI", 9)
        )
        ultima_actualizacion.pack(anchor="w", padx=15, pady=(10, 15))

        def actualizar_leyenda(items):
            for widget in leyenda_frame.winfo_children():
                widget.destroy()

            if not items:
                tk.Label(
                    leyenda_frame,
                    text="La leyenda aparecerá al generar el grafo",
                    bg="white",
                    fg="#6B7280",
                    font=("Segoe UI", 9)
                ).pack(anchor="w")
                return

            for item in items:
                fila = tk.Frame(leyenda_frame, bg="white")
                fila.pack(side="left", padx=10)
                canvas = tk.Canvas(fila, width=14, height=14, bg="white", highlightthickness=0)
                canvas.pack(side="left")
                canvas.create_oval(2, 2, 12, 12, fill=item.get("color", "#fff"), outline=item.get("color", "#fff"))
                tk.Label(
                    fila,
                    text=item.get("label", ""),
                    bg="white",
                    fg="#0A1B2E",
                    font=("Segoe UI", 9)
                ).pack(side="left", padx=4)

        def actualizar_stats(datos):
            for clave, lbl in stats_labels.items():
                lbl.config(text="--")

            if not datos:
                ultima_actualizacion.config(text="Actualizado: --")
                return

            lbl_map = {
                "nodos": f"{datos['nodos']:,}".replace(",", "."),
                "aristas": f"{datos['aristas']:,}".replace(",", "."),
                "casos_totales": f"{datos['casos_totales']:,}".replace(",", "."),
                "extorsion": f"{datos['extorsion']:,}".replace(",", "."),
                "sicariato": f"{datos['sicariato']:,}".replace(",", "."),
                "densidad": f"{datos['densidad']:.2f}",
                "grado_promedio": f"{datos['grado_promedio']:.2f}",
            }

            for clave, valor in lbl_map.items():
                stats_labels[clave].config(text=valor)

            ultima_actualizacion.config(
                text=f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )

        def render_grafo():
            if not depto_var.get():
                estado_grafo.config(text="Selecciona un departamento válido.", fg="#DC2626")
                return

            tipo_valor = tipo_map.get(tipo_var.get(), "TODO")
            color_valor = color_map.get(color_var.get(), "cases")
            anio_valor = anio_var.get() or (anios[-1] if anios else "")
            depto_real = depto_map.get(depto_var.get(), depto_var.get())

            if not anio_valor:
                estado_grafo.config(text="Selecciona un año válido.", fg="#DC2626")
                return

            try:
                resultado = B_explorar_grafo.generar_grafo_territorial(
                    DF_SIDPOL,
                    GDF_GEO,
                    depto_real,
                    tipo_valor,
                    anio_valor,
                    color_valor,
                    abrir_archivo=False
                )
            except (ValueError, RuntimeError) as exc:
                estado_grafo.config(text=str(exc), fg="#DC2626")
                imagen_lbl.config(image="", text="")
                imagen_lbl.image = None
                actualizar_leyenda([])
                actualizar_stats(None)
                return

            try:
                img = Image.open(resultado["image_path"])
                img.thumbnail((620, 240), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                imagen_lbl.config(image=tk_img)
                imagen_lbl.image = tk_img
            except Exception as exc:
                estado_grafo.config(text=f"No se pudo cargar el grafo: {exc}", fg="#DC2626")
                actualizar_leyenda([])
                actualizar_stats(None)
                return

            titulo_grafo.config(text=resultado.get("graph_title", "Grafo de Distritos"))
            subtitulo_grafo.config(text=resultado.get("graph_subtitle", ""))
            estado_grafo.config(text="Grafo actualizado correctamente.", fg="#059669")
            actualizar_leyenda(resultado.get("legend", []))
            actualizar_stats(resultado.get("stats"))

        btn_generar.config(command=render_grafo)
        actualizar_leyenda([])
        actualizar_stats(None)

    def cargar_algoritmos():
        global ULTIMO_FILTRO_ALGORITMOS
        limpiar()

        contenedor_scroll = tk.Frame(contenido, bg="#eef2f6", width=ANCHO-250, height=ALTO-90)
        contenedor_scroll.place(x=0, y=0, relwidth=1, relheight=1)

        canvas = tk.Canvas(contenedor_scroll, bg="#eef2f6", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(contenedor_scroll, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        vista_base = tk.Frame(canvas, bg="#eef2f6")
        vista_id = canvas.create_window((0, 0), window=vista_base, anchor="nw")

        def _actualizar_scroll_alg(_event=None):
            canvas.configure(yscrollregion=canvas.bbox("all"))

        def _ajustar_ancho_alg(event):
            canvas.itemconfig(vista_id, width=event.width)

        vista_base.bind("<Configure>", _actualizar_scroll_alg)
        canvas.bind("<Configure>", _ajustar_ancho_alg)

        vista = tk.Frame(vista_base, bg="#eef2f6")
        vista.pack(fill="both", expand=True, padx=25, pady=15)

        opciones = B_explorar_grafo.obtener_opciones_filtros(DF_SIDPOL)
        departamentos = opciones.get("departamentos", [])
        departamentos_display = [d.upper() for d in departamentos]
        depto_map = {display: original for display, original in zip(departamentos_display, departamentos)}

        tipo_opciones = opciones.get("tipo_delito", B_explorar_grafo.TIPO_DELITO_OPCIONES)
        tipo_labels = [opt["label"].upper() for opt in tipo_opciones]
        tipo_map = {opt["label"].upper(): opt["value"] for opt in tipo_opciones}

        depto_var = tk.StringVar(value=departamentos_display[0] if departamentos_display else "")
        tipo_var = tk.StringVar(value=tipo_labels[0] if tipo_labels else "TODOS")
        estado_var = tk.StringVar(value="Selecciona filtros y ejecuta un algoritmo.")

        filtros = tk.Frame(vista, bg="#081629", height=120)
        filtros.pack(fill="x", padx=25, pady=(20, 0))
        for col in range(5):
            filtros.columnconfigure(col, weight=1)

        estilo = ttk.Style()
        try:
            estilo.theme_use("default")
        except Exception:
            pass
        estilo.configure(
            "Alg.TCombobox",
            fieldbackground="#142541",
            background="#142541",
            foreground="white",
            borderwidth=0,
            relief="flat",
        )
        estilo.map(
            "Alg.TCombobox",
            fieldbackground=[("readonly", "#142541")],
            foreground=[("readonly", "white")],
        )

        def crear_selector(texto, columna, variable, valores, combo_width=0):
            tk.Label(
                filtros,
                text=texto,
                bg="#081629",
                fg="#7DA3C9",
                font=("Segoe UI", 10, "bold"),
            ).grid(row=0, column=columna, padx=12, pady=(15, 2), sticky="w")

            combo = ttk.Combobox(
                filtros,
                textvariable=variable,
                values=valores,
                state="readonly",
                style="Alg.TCombobox",
                width=combo_width or 0,
            )
            combo.grid(row=1, column=columna, padx=12, pady=(0, 15), sticky="ew")
            if not valores:
                combo.configure(state="disabled")
            return combo

        depto_combo = crear_selector("Departamento", 0, depto_var, departamentos_display)
        crear_selector("Tipo de delito", 1, tipo_var, tipo_labels)

        tabs_frame = tk.Frame(vista, bg="#eef2f6")
        tabs_frame.pack(fill="x", padx=25, pady=(20, 10))

        tab_names = ["BFS/DFS", "Floyd-Warshall", "Kruskal (MST)"]
        selected_tab = tk.StringVar(value=tab_names[0])
        tab_buttons = {}

        def estilo_tab(activo):
            return {
                "bg": "#111C2E" if activo else "#ced6e0",
                "fg": "white" if activo else "#1E3A5F",
            }

        def cambiar_tab(nombre):
            selected_tab.set(nombre)
            for tab, boton in tab_buttons.items():
                style = estilo_tab(tab == nombre)
                boton.config(bg=style["bg"], fg=style["fg"])
            for frame in tab_control_frames.values():
                frame.grid_remove()
            frame = tab_control_frames.get(nombre)
            if frame:
                frame.grid(row=0, column=0, sticky="nsew")
            btn_ejecutar.config(text=f"Ejecutar {nombre}")
            estado_var.set("Configura los parámetros y ejecuta el algoritmo seleccionado.")

        for idx, nombre in enumerate(tab_names):
            style = estilo_tab(idx == 0)
            b = tk.Label(
                tabs_frame,
                text=nombre,
                bg=style["bg"],
                fg=style["fg"],
                font=("Segoe UI", 11, "bold"),
                width=16,
                pady=8,
                cursor="hand2",
            )
            b.grid(row=0, column=idx, padx=4)
            tab_buttons[nombre] = b
            b.bind("<Button-1>", lambda e, n=nombre: cambiar_tab(n))

        controles = tk.Frame(vista, bg="#eef2f6")
        controles.pack(fill="x", padx=25, pady=(0, 20))
        controles.columnconfigure(0, weight=1)
        tab_control_frames = {}

        frame_bfs = tk.Frame(controles, bg="#eef2f6")
        tab_control_frames["BFS/DFS"] = frame_bfs
        frame_bfs.grid(row=0, column=0, sticky="ew")

        metodo_var = tk.StringVar(value="BFS (Por niveles)")
        metodo_map = {
            "BFS (Por niveles)": "bfs",
            "DFS (En profundidad)": "dfs",
        }
        tk.Label(
            frame_bfs,
            text="Algoritmo",
            bg="#eef2f6",
            fg="#1E3A5F",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=5)
        metodo_combo = ttk.Combobox(
            frame_bfs,
            textvariable=metodo_var,
            values=list(metodo_map.keys()),
            state="readonly",
            style="Alg.TCombobox",
            width=25,
        )
        metodo_combo.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        distrito_var = tk.StringVar()
        tk.Label(
            frame_bfs,
            text="Distrito inicial",
            bg="#eef2f6",
            fg="#1E3A5F",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=1, sticky="w", padx=5)
        distrito_combo = ttk.Combobox(
            frame_bfs,
            textvariable=distrito_var,
            values=[],
            state="readonly",
            style="Alg.TCombobox",
            width=30,
        )
        distrito_combo.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        frame_floyd = tk.Frame(controles, bg="#eef2f6")
        tab_control_frames["Floyd-Warshall"] = frame_floyd
        frame_floyd.grid(row=0, column=0, sticky="ew")
        frame_floyd.grid_remove()
        modo_var = tk.StringVar(value="Mayor concentración")
        modo_map = {
            "Mayor concentración": "volume",
            "Ruta eficiente": "efficiency",
        }
        tk.Label(
            frame_floyd,
            text="Modo de análisis",
            bg="#eef2f6",
            fg="#1E3A5F",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=5)
        modo_combo = ttk.Combobox(
            frame_floyd,
            textvariable=modo_var,
            values=list(modo_map.keys()),
            state="readonly",
            style="Alg.TCombobox",
            width=28,
        )
        modo_combo.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        frame_kruskal = tk.Frame(controles, bg="#eef2f6")
        tab_control_frames["Kruskal (MST)"] = frame_kruskal
        frame_kruskal.grid(row=0, column=0, sticky="ew")
        frame_kruskal.grid_remove()
        tk.Label(
            frame_kruskal,
            text="Top K nodos prioritarios (opcional)",
            bg="#eef2f6",
            fg="#1E3A5F",
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=5)
        k_var = tk.StringVar()
        tk.Entry(frame_kruskal, textvariable=k_var, width=10, font=("Segoe UI", 11)).grid(
            row=1, column=0, padx=5, pady=5, sticky="w"
        )

        btn_wrapper = tk.Frame(vista, bg="#eef2f6")
        btn_wrapper.pack(fill="x", padx=25, pady=(0, 15))

        btn_ejecutar = tk.Button(
            btn_wrapper,
            text="Ejecutar BFS/DFS",
            bg="#12D0A5",
            fg="#051427",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            cursor="hand2",
        )
        btn_ejecutar.pack()

        resultado = tk.Frame(vista, bg="#eef2f6")
        resultado.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        resultado.columnconfigure(0, weight=3)
        resultado.columnconfigure(1, weight=1)

        grafico_card = tk.Frame(resultado, bg="white", height=360)
        grafico_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        grafico_card.grid_propagate(False)
        tk.Label(
            grafico_card,
            text="Visualización del Grafo",
            bg="white",
            fg="#0A1B2E",
            font=("Segoe UI", 15, "bold"),
        ).place(x=20, y=15)

        grafico_canvas = tk.Canvas(
            grafico_card,
            width=600,
            height=260,
            bg="#030914",
            highlightthickness=0,
        )
        grafico_canvas.place(relx=0.5, y=60, anchor="n")
        canvas_text_id = grafico_canvas.create_text(
            300,
            130,
            text="Aún no hay imagen generada.",
            fill="#94A3B8",
            font=("Segoe UI", 11),
            width=560,
        )
        canvas_state = {"image_id": None}

        estado_label = tk.Label(
            grafico_card,
            textvariable=estado_var,
            bg="white",
            fg="#64748B",
            font=("Segoe UI", 10, "italic"),
        )
        estado_label.place(x=20, y=330)

        stats_card = tk.Frame(resultado, bg="#112744", height=360)
        stats_card.grid(row=0, column=1, sticky="nsew")
        stats_card.grid_propagate(False)
        tk.Label(
            stats_card,
            text="Análisis Completado",
            bg="#112744",
            fg="white",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", padx=15, pady=(15, 10))

        stats_cards = []
        for _ in range(4):
            card = tk.Frame(stats_card, bg="#0B1C32", height=60)
            card.pack(fill="x", padx=15, pady=6)
            title = tk.Label(card, text="--", bg="#0B1C32", fg="#7DA3C9", font=("Segoe UI", 9))
            title.pack(anchor="w")
            value = tk.Label(card, text="--", bg="#0B1C32", fg="#F8FAFC", font=("Segoe UI", 15, "bold"))
            value.pack(anchor="w")
            stats_cards.append({"title": title, "value": value})

        detalle_frame = tk.Frame(vista, bg="#eef2f6")
        detalle_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        detalle_frame.columnconfigure(0, weight=1)
        detalle_frame.columnconfigure(1, weight=1)

        detalle_izq = tk.Frame(detalle_frame, bg="white", height=220)
        detalle_der = tk.Frame(detalle_frame, bg="white", height=220)
        detalle_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        detalle_der.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        detalle_izq.grid_propagate(False)
        detalle_der.grid_propagate(False)

        titulo_izq = tk.Label(
            detalle_izq,
            text="Detalle Izquierdo",
            bg="white",
            fg="#0A1B2E",
            font=("Segoe UI", 12, "bold"),
        )
        titulo_izq.pack(anchor="w", padx=15, pady=(15, 8))
        cuerpo_izq = scrolledtext.ScrolledText(
            detalle_izq,
            wrap="word",
            height=8,
            font=("Segoe UI", 10),
            bg="white",
            fg="#1F2937",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
        )
        cuerpo_izq.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        cuerpo_izq.config(state="disabled")

        titulo_der = tk.Label(
            detalle_der,
            text="Detalle Derecho",
            bg="white",
            fg="#0A1B2E",
            font=("Segoe UI", 12, "bold"),
        )
        titulo_der.pack(anchor="w", padx=15, pady=(15, 8))
        cuerpo_der = scrolledtext.ScrolledText(
            detalle_der,
            wrap="word",
            height=8,
            font=("Segoe UI", 10),
            bg="white",
            fg="#1F2937",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
        )
        cuerpo_der.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        cuerpo_der.config(state="disabled")

        imagen_cache = {"photo": None}

        def mostrar_mensaje_canvas(texto):
            if canvas_state["image_id"]:
                grafico_canvas.delete(canvas_state["image_id"])
                canvas_state["image_id"] = None
            grafico_canvas.itemconfig(canvas_text_id, text=texto, state="normal")

        def set_text(widget, contenido):
            widget.config(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", contenido or "Sin información disponible.")
            widget.config(state="disabled")

        def actualizar_imagen(ruta):
            if not ruta or not os.path.exists(ruta):
                imagen_cache["photo"] = None
                mostrar_mensaje_canvas("No se generó imagen.")
                return
            try:
                img = Image.open(ruta)
                img.thumbnail((600, 260), Image.Resampling.LANCZOS)
                imagen_cache["photo"] = ImageTk.PhotoImage(img)
                if canvas_state["image_id"]:
                    grafico_canvas.delete(canvas_state["image_id"])
                canvas_state["image_id"] = grafico_canvas.create_image(
                    300,
                    130,
                    image=imagen_cache["photo"],
                )
                grafico_canvas.itemconfig(canvas_text_id, state="hidden")
            except Exception as exc:
                imagen_cache["photo"] = None
                mostrar_mensaje_canvas(f"Error al cargar imagen: {exc}")

        def actualizar_stats(pares):
            for idx, card in enumerate(stats_cards):
                if idx < len(pares):
                    titulo, valor = pares[idx]
                    card["title"].config(text=titulo)
                    card["value"].config(text=valor)
                else:
                    card["title"].config(text="--")
                    card["value"].config(text="--")

        def actualizar_detalles(titulo_left, cuerpo_left, titulo_right, cuerpo_right):
            titulo_izq.config(text=titulo_left)
            set_text(cuerpo_izq, cuerpo_left)
            titulo_der.config(text=titulo_right)
            set_text(cuerpo_der, cuerpo_right)

        def obtener_distritos(dep):
            if not dep:
                return []
            dep_original = depto_map.get(dep, dep)
            dep_upper = dep_original.upper().strip()
            mask = GDF_GEO["NOMBDEP"].str.upper().str.strip() == dep_upper
            distritos = sorted(GDF_GEO.loc[mask, "NOMBDIST"].dropna().unique())
            return distritos

        def refrescar_distritos(*_):
            distritos = obtener_distritos(depto_var.get())
            distrito_combo["values"] = distritos
            if distritos:
                distrito_var.set(distritos[0])
            else:
                distrito_var.set("")

        refrescar_distritos()
        depto_var.trace_add("write", lambda *_: refrescar_distritos())

        def formatear_niveles(levels, frontera):
            if not levels:
                return "No se detectaron niveles."
            lines = []
            for item in levels:
                nodos = ", ".join(item.get("nodes", [])) or "--"
                lines.append(f"Nivel {item.get('level', 0)}: {nodos} ({item.get('cases', 0)} casos)")
            if frontera:
                lines.append("")
                lines.append(f"Frontera vigente: {', '.join(frontera)}")
            return "\n".join(lines)

        def formatear_clusters(clusters):
            if not clusters:
                return "No se detectaron agrupaciones críticas."
            return "\n".join(
                f"{c['name']}: {c['cases']} casos · {c['connections']} conexiones · {', '.join(c['nodes'])}" for c in clusters
            )

        def formatear_rutas(rutas, limite=5):
            if not rutas:
                return "No se encontraron rutas."
            lines = []
            for idx, ruta in enumerate(rutas[:limite], start=1):
                camino = " -> ".join(ruta.get("path", []))
                lines.append(f"Ruta {idx}: {camino} ({ruta.get('concentration', 0)} casos)")
            return "\n".join(lines)

        def formatear_puentes(bridge_report):
            if not bridge_report:
                return "No se identificaron distritos puente."
            return "\n".join(
                f"{item.get('Distrito')}: {item.get('Frecuencia en Rutas')} apariciones" for item in bridge_report
            )

        def formatear_nodos_criticos(nodes):
            if not nodes:
                return "Sin nodos críticos registrados."
            return "\n".join(f"{n.get('distrito')}: {n.get('casos')} casos" for n in nodes)

        def formatear_columna(columna):
            if not columna:
                return "Sin enlaces destacados."
            return "\n".join(
                f"{c.get('Enlace')}: {c.get('Casos Acumulados')} casos (Costo {c.get('Costo (MST)')})" for c in columna
            )

        def ejecutar_algoritmo():
            departamento = depto_map.get(depto_var.get().strip(), depto_var.get().strip())
            if not departamento:
                estado_var.set("Selecciona un departamento válido.")
                return

            crime_value = tipo_map.get(tipo_var.get(), "TODO")
            try:
                G, crime_types = B_algoritmos.preparar_grafo_para_algoritmos(
                    DF_SIDPOL,
                    GDF_GEO,
                    departamento,
                    crime_value,
                    verbose=False,
                )
            except Exception as exc:
                estado_var.set(f"Error al preparar grafo: {exc}")
                return

            if not G or not G.nodes:
                estado_var.set("El grafo está vacío para los filtros seleccionados.")
                actualizar_imagen(None)
                actualizar_stats([])
                actualizar_detalles("Detalle", "Sin datos", "Detalle", "Sin datos")
                return

            ULTIMO_FILTRO_ALGORITMOS["departamento"] = departamento
            ULTIMO_FILTRO_ALGORITMOS["tipo_label"] = tipo_var.get()
            ULTIMO_FILTRO_ALGORITMOS["tipo_value"] = crime_value

            tab = selected_tab.get()

            try:
                if tab == "BFS/DFS":
                    nodo_inicio = distrito_var.get().strip()
                    if not nodo_inicio:
                        estado_var.set("Selecciona un distrito inicial.")
                        return
                    if nodo_inicio not in G.nodes:
                        estado_var.set("El distrito inicial no tiene datos para este filtro.")
                        return
                    metodo_value = metodo_map.get(metodo_var.get(), "bfs")
                    resultado = B_algoritmos.expansion_tree(
                        G,
                        nodo_inicio,
                        metodo_value,
                        None,
                        crime_types,
                        departamento,
                        show_plot=False,
                        verbose=False,
                    )
                    if not resultado:
                        estado_var.set("No se pudo generar el árbol de expansión.")
                        return

                    stats = resultado.get("stats", {})
                    actualizar_stats([
                        ("Algoritmo", stats.get("algoritmo", "--")),
                        ("Nodos alcanzados", stats.get("nodos_alcanzados_pct", "--")),
                        ("Casos acumulados", str(stats.get("casos_acumulados_ruta", "--"))),
                        ("Profundidad", str(stats.get("profundidad_maxima", "--"))),
                    ])

                    actualizar_imagen(resultado.get("image_path"))
                    actualizar_detalles(
                        "Árbol de Expansión por Niveles",
                        formatear_niveles(resultado.get("levels", []), resultado.get("frontier_nodes", [])),
                        "Agrupaciones Delictivas Detectadas",
                        formatear_clusters(resultado.get("clusters", [])),
                    )
                    estado_var.set("Árbol de expansión generado correctamente.")

                elif tab == "Floyd-Warshall":
                    modo_value = modo_map.get(modo_var.get(), "volume")
                    resultado = B_algoritmos.floyd_warshall_routes(
                        G,
                        crime_types,
                        modo_value,
                        departamento,
                        show_plot=False,
                        verbose=False,
                    )
                    if not resultado:
                        estado_var.set("No se pudieron calcular rutas críticas.")
                        return

                    stats = resultado.get("stats", {})
                    actualizar_stats([
                        ("Caminos calculados", str(stats.get("num_caminos_calculados", "--"))),
                        ("Distritos puente", str(stats.get("num_distritos_puentes", "--"))),
                        ("Máx. concentración", str(stats.get("mayor_concentracion_casos", "--"))),
                        ("Ruta eficiente", str(stats.get("ruta_mas_eficiente_casos", "--"))),
                    ])

                    actualizar_imagen(resultado.get("image_path"))
                    actualizar_detalles(
                        "Rutas Críticas Identificadas",
                        formatear_rutas(resultado.get("critical_paths", [])),
                        "Distritos Puente Estratégicos",
                        formatear_puentes(resultado.get("bridge_report", [])),
                    )
                    estado_var.set("Rutas críticas analizadas con éxito.")

                else:
                    k_value = k_var.get().strip()
                    k_num = int(k_value) if k_value.isdigit() else None
                    resultado = B_algoritmos.kruskal_mst_analysis(
                        G,
                        k_num,
                        crime_types,
                        departamento,
                        show_plot=False,
                        verbose=False,
                    )
                    if not resultado:
                        estado_var.set("No se pudo calcular el MST.")
                        return

                    stats = resultado.get("stats", {})
                    actualizar_stats([
                        ("Aristas en MST", str(stats.get("MST_aristas", "--"))),
                        ("Aristas eliminadas", str(stats.get("aristas_eliminadas", "--"))),
                        ("Reducción de peso", f"{stats.get('reduccion_peso_pct', 0):.2f}%" if stats.get('reduccion_peso_pct') is not None else "--"),
                        ("Focos detectados", str(stats.get("focos_del_crimen_detectados", "--"))),
                    ])

                    actualizar_imagen(resultado.get("image_path"))
                    actualizar_detalles(
                        "Nodos Críticos",
                        formatear_nodos_criticos(resultado.get("critical_nodes", [])),
                        "Columna Central (Enlaces)",
                        formatear_columna(resultado.get("central_column", [])),
                    )
                    estado_var.set("Red mínima optimizada con Kruskal.")

            except Exception as exc:
                estado_var.set(f"Error al ejecutar {tab}: {exc}")

        btn_ejecutar.config(command=ejecutar_algoritmo)
        cambiar_tab(selected_tab.get())

    def cargar_resultados():
        global ULTIMO_FILTRO_ALGORITMOS
        limpiar()

        COLOR_BG = "#050f1f"
        COLOR_CARD = "#0f1f38"
        COLOR_ACCENT = "#ef4444"

        vista = tk.Frame(contenido, bg=COLOR_BG, width=ANCHO-250, height=ALTO-90)
        vista.pack(fill="both", expand=True)
        vista.pack_propagate(False)

        opciones = B_explorar_grafo.obtener_opciones_filtros(DF_SIDPOL)
        departamentos = opciones.get("departamentos", [])
        departamentos_display = [d.upper() for d in departamentos]
        depto_map = {display: original for display, original in zip(departamentos_display, departamentos)}

        tipo_opciones = opciones.get("tipo_delito", B_explorar_grafo.TIPO_DELITO_OPCIONES)
        tipo_labels = [opt["label"].upper() for opt in tipo_opciones]
        tipo_map = {opt["label"].upper(): opt["value"] for opt in tipo_opciones}

        default_depto = ULTIMO_FILTRO_ALGORITMOS.get("departamento")
        if default_depto:
            default_depto = default_depto.upper()
        else:
            default_depto = departamentos_display[0] if departamentos_display else ""

        default_tipo = ULTIMO_FILTRO_ALGORITMOS.get("tipo_label") or (tipo_labels[0] if tipo_labels else "TODOS")

        filtros = tk.Frame(vista, bg="#081629")
        filtros.pack(fill="x", padx=25, pady=(20, 10))

        tk.Label(
            filtros,
            text="Resultados del Análisis Territorial",
            bg="#081629",
            fg="white",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(10, 5))

        tk.Label(
            filtros,
            text="Consolidado de hallazgos — BFS/DFS, Floyd-Warshall y Kruskal MST",
            bg="#081629",
            fg="#9fb8d9",
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, columnspan=3, sticky="w")

        for col in range(3):
            filtros.columnconfigure(col, weight=1)

        depto_var = tk.StringVar(value=default_depto)
        tipo_var = tk.StringVar(value=default_tipo.upper() if default_tipo else "")
        estado_var = tk.StringVar(value="Selecciona un departamento y genera el resumen.")

        def crear_selector(texto, columna, variable, valores):
            tk.Label(
                filtros,
                text=texto,
                bg="#081629",
                fg="#9fb8d9",
                font=("Segoe UI", 10, "bold"),
            ).grid(row=2, column=columna, sticky="w", pady=(15, 2))
            combo = ttk.Combobox(
                filtros,
                textvariable=variable,
                values=valores,
                state="readonly",
                width=25,
            )
            combo.grid(row=3, column=columna, sticky="we", padx=(0, 20))
            return combo

        crear_selector("Departamento", 0, depto_var, departamentos_display)
        crear_selector("Tipo de delito", 1, tipo_var, tipo_labels)

        boton_frame = tk.Frame(filtros, bg="#081629")
        boton_frame.grid(row=3, column=2, sticky="e")

        resumen_data = {"mst_image": None}
        btn_generar = None

        body_container = tk.Frame(vista, bg=COLOR_BG)
        body_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        body_container.pack_propagate(False)

        canvas = tk.Canvas(body_container, bg=COLOR_BG, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(body_container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        body = tk.Frame(canvas, bg=COLOR_BG)
        body_id = canvas.create_window((0, 0), window=body, anchor="nw")

        def _update_scroll(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _resize_body(event):
            canvas.itemconfig(body_id, width=event.width)

        body.bind("<Configure>", _update_scroll)
        canvas.bind("<Configure>", _resize_body)

        def limpiar_body():
            for widget in body.winfo_children():
                widget.destroy()

        def formatear_valor(valor):
            try:
                if isinstance(valor, (int, float)):
                    return f"{valor:,}".replace(",", ".")
            except Exception:
                pass
            return str(valor)

        def render_resumen(datos):
            limpiar_body()
            if not datos:
                tk.Label(
                    body,
                    text="Aún no hay información generada para esta sección.",
                    bg=COLOR_BG,
                    fg="white",
                    font=("Segoe UI", 12),
                ).pack(pady=40)
                return

            cards_frame = tk.Frame(body, bg=COLOR_BG)
            cards_frame.pack(fill="x", padx=10, pady=(10, 5))

            for idx, card_data in enumerate(datos.get("cards", [])):
                card = tk.Frame(cards_frame, bg=COLOR_CARD, width=190, height=90)
                card.grid(row=0, column=idx, padx=8, pady=5, sticky="nsew")
                card.grid_propagate(False)
                tk.Label(
                    card,
                    text=formatear_valor(card_data.get("value", "--")),
                    bg=COLOR_CARD,
                    fg="white",
                    font=("Segoe UI", 20, "bold"),
                ).pack(anchor="w", padx=15, pady=(15, 0))
                tk.Label(
                    card,
                    text=card_data.get("label", ""),
                    bg=COLOR_CARD,
                    fg="#9fb8d9",
                    font=("Segoe UI", 10),
                ).pack(anchor="w", padx=15, pady=(5, 0))

            tk.Label(
                body,
                text="Nodos Estratégicos Identificados",
                bg=COLOR_BG,
                fg="white",
                font=("Segoe UI", 14, "bold"),
            ).pack(anchor="w", padx=10, pady=(20, 5))

            nodos_frame = tk.Frame(body, bg=COLOR_BG)
            nodos_frame.pack(fill="x", padx=5)

            for nodo in datos.get("nodos", []):
                card = tk.Frame(nodos_frame, bg=COLOR_CARD, highlightbackground="#213658", highlightthickness=1)
                card.pack(fill="x", padx=5, pady=6)

                header = tk.Frame(card, bg=COLOR_CARD)
                header.pack(fill="x", padx=15, pady=10)

                badge = tk.Frame(header, bg="#1a2d4a", width=54, height=54)
                badge.pack(side="left")
                badge.pack_propagate(False)
                tk.Label(
                    badge,
                    text=nodo.get("sigla", "--"),
                    bg="#1a2d4a",
                    fg="white",
                    font=("Segoe UI", 13, "bold"),
                ).pack(expand=True)

                info = tk.Frame(header, bg=COLOR_CARD)
                info.pack(side="left", padx=15, fill="x", expand=True)
                tk.Label(
                    info,
                    text=nodo.get("nombre", "--"),
                    bg=COLOR_CARD,
                    fg="white",
                    font=("Segoe UI", 12, "bold"),
                ).pack(anchor="w")
                tk.Label(
                    info,
                    text=nodo.get("rol", ""),
                    bg=COLOR_CARD,
                    fg="#9fb8d9",
                    font=("Segoe UI", 10),
                ).pack(anchor="w", pady=(2, 0))

                chip_color = COLOR_ACCENT if nodo.get("nivel") == "Crítico" else ("#f97316" if nodo.get("nivel") == "Alto" else "#14b8a6")
                tk.Label(
                    header,
                    text=f"{nodo.get('nivel', '--')} nivel",
                    bg=chip_color,
                    fg="white",
                    font=("Segoe UI", 9, "bold"),
                    padx=12,
                    pady=3,
                ).pack(side="right")

                metrics = tk.Frame(card, bg=COLOR_CARD)
                metrics.pack(fill="x", padx=15, pady=(0, 10))

                for label, valor in [
                    ("Extorsión", nodo.get("extorsion", 0)),
                    ("Sicariato/Homicidios", nodo.get("sicariato", 0)),
                    ("Casos totales", nodo.get("total", 0)),
                ]:
                    item = tk.Frame(metrics, bg="#142643", width=150, height=50)
                    item.pack(side="left", padx=5)
                    item.pack_propagate(False)
                    tk.Label(item, text=label, bg="#142643", fg="#9fb8d9", font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(6, 0))
                    tk.Label(item, text=formatear_valor(valor), bg="#142643", fg="white", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10)

                tags = tk.Frame(card, bg=COLOR_CARD)
                tags.pack(fill="x", padx=15, pady=(0, 8))
                tk.Label(tags, text="Detectado por:", bg=COLOR_CARD, fg="#9fb8d9", font=("Segoe UI", 9)).pack(side="left")
                for alg in nodo.get("algoritmos", []):
                    tk.Label(
                        tags,
                        text=alg,
                        bg="#1a2d4a",
                        fg="white",
                        font=("Segoe UI", 9, "bold"),
                        padx=8,
                        pady=2,
                    ).pack(side="left", padx=4)

                tk.Label(
                    card,
                    text=nodo.get("recomendacion", ""),
                    bg=COLOR_CARD,
                    fg="white",
                    font=("Segoe UI", 10),
                    wraplength=820,
                    justify="left",
                ).pack(fill="x", padx=15, pady=(0, 12))

            tk.Label(
                body,
                text="Rutas Críticas de Propagación",
                bg=COLOR_BG,
                fg="white",
                font=("Segoe UI", 14, "bold"),
            ).pack(anchor="w", padx=10, pady=(25, 8))

            rutas_frame = tk.Frame(body, bg=COLOR_BG)
            rutas_frame.pack(fill="x", padx=5)

            riesgo_colores = {
                "Riesgo crítico": COLOR_ACCENT,
                "Riesgo alto": "#f97316",
                "Riesgo medio": "#eab308",
                "Riesgo bajo": "#14b8a6",
            }

            for ruta in datos.get("rutas", []):
                card = tk.Frame(rutas_frame, bg="#111e37", highlightbackground="#242f4a", highlightthickness=1)
                card.pack(fill="x", padx=5, pady=6)

                header = tk.Frame(card, bg="#111e37")
                header.pack(fill="x", padx=15, pady=10)

                badge = tk.Label(
                    header,
                    text=ruta.get("id", "R"),
                    bg="#1a2d4a",
                    fg="white",
                    font=("Segoe UI", 11, "bold"),
                    width=4,
                    pady=4,
                )
                badge.pack(side="left")

                tk.Label(
                    header,
                    text=ruta.get("descripcion", "Corredor"),
                    bg="#111e37",
                    fg="white",
                    font=("Segoe UI", 12, "bold"),
                ).pack(side="left", padx=15)

                tk.Label(
                    header,
                    text=ruta.get("riesgo", ""),
                    bg=riesgo_colores.get(ruta.get("riesgo"), "#2563eb"),
                    fg="white",
                    font=("Segoe UI", 9, "bold"),
                    padx=12,
                    pady=3,
                ).pack(side="right")

                body_ruta = tk.Frame(card, bg="#111e37")
                body_ruta.pack(fill="x", padx=15, pady=(0, 12))
                tk.Label(
                    body_ruta,
                    text=ruta.get("path", ""),
                    bg="#111e37",
                    fg="#9fb8d9",
                    font=("Segoe UI", 10, "italic"),
                ).pack(anchor="w")

                stats = tk.Frame(card, bg="#0d1627")
                stats.pack(fill="x")
                for label, valor in [("Casos acumulados", ruta.get("casos", 0)), ("Distancia", ruta.get("distancia", 0))]:
                    sub = tk.Frame(stats, bg="#0d1627")
                    sub.pack(side="left", padx=20, pady=10)
                    tk.Label(sub, text=label, bg="#0d1627", fg="#9fb8d9", font=("Segoe UI", 9)).pack(anchor="w")
                    tk.Label(sub, text=formatear_valor(valor), bg="#0d1627", fg="white", font=("Segoe UI", 12, "bold")).pack(anchor="w")

                tk.Label(
                    card,
                    text=ruta.get("estrategia", ""),
                    bg="#111e37",
                    fg="white",
                    font=("Segoe UI", 10),
                    wraplength=820,
                    justify="left",
                ).pack(fill="x", padx=15, pady=(0, 12))

            tk.Label(
                body,
                text="Red Mínima de Intervención (MST)",
                bg=COLOR_BG,
                fg="white",
                font=("Segoe UI", 14, "bold"),
            ).pack(anchor="w", padx=10, pady=(25, 8))

            mst_wrapper = tk.Frame(body, bg=COLOR_BG)
            mst_wrapper.pack(fill="x", padx=5, pady=(0, 20))
            mst_wrapper.columnconfigure(0, weight=2)
            mst_wrapper.columnconfigure(1, weight=1)

            mst_left = tk.Frame(mst_wrapper, bg=COLOR_CARD)
            mst_left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

            tk.Label(
                mst_left,
                text="Árbol de expansión mínima — Algoritmo Kruskal",
                bg=COLOR_CARD,
                fg="white",
                font=("Segoe UI", 12, "bold"),
            ).pack(anchor="w", padx=15, pady=(15, 5))

            mst_canvas = tk.Canvas(mst_left, width=360, height=240, bg="#051024", highlightthickness=0)
            mst_canvas.pack(padx=15, pady=(0, 10))

            img_path = datos.get("mst", {}).get("image_path")
            if img_path and os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    img.thumbnail((340, 220), Image.Resampling.LANCZOS)
                    resumen_data["mst_image"] = ImageTk.PhotoImage(img)
                    mst_canvas.create_image(180, 120, image=resumen_data["mst_image"])
                except Exception as exc:
                    mst_canvas.create_text(180, 120, text=f"Error al cargar imagen: {exc}", fill="white", width=320)
            else:
                mst_canvas.create_text(180, 120, text="Sin visual disponible", fill="#9fb8d9")

            metrics_frame = tk.Frame(mst_left, bg=COLOR_CARD)
            metrics_frame.pack(fill="x", padx=15, pady=(0, 15))
            for metric in datos.get("mst", {}).get("metrics", []):
                block = tk.Frame(metrics_frame, bg="#142643", width=120, height=60)
                block.pack(side="left", padx=5)
                block.pack_propagate(False)
                tk.Label(block, text=metric.get("label", ""), bg="#142643", fg="#9fb8d9", font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(8, 0))
                tk.Label(block, text=formatear_valor(metric.get("value", "--")), bg="#142643", fg="white", font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=10)

            mst_right = tk.Frame(mst_wrapper, bg=COLOR_CARD)
            mst_right.grid(row=0, column=1, sticky="nsew")

            tk.Label(
                mst_right,
                text="Conexiones críticas",
                bg=COLOR_CARD,
                fg="white",
                font=("Segoe UI", 12, "bold"),
            ).pack(anchor="w", padx=15, pady=(15, 5))

            for conn in datos.get("mst", {}).get("conexiones", []):
                fila = tk.Frame(mst_right, bg="#142643")
                fila.pack(fill="x", padx=15, pady=4)
                tk.Label(fila, text=conn.get("rank", 0), bg="#1a2d4a", fg="white", font=("Segoe UI", 10, "bold"), width=3).pack(side="left", padx=6, pady=6)
                tk.Label(
                    fila,
                    text=conn.get("enlace", "--"),
                    bg="#142643",
                    fg="white",
                    font=("Segoe UI", 10, "bold"),
                ).pack(side="left")
                tk.Label(
                    fila,
                    text=formatear_valor(conn.get("casos", "--")),
                    bg="#142643",
                    fg="#9fb8d9",
                    font=("Segoe UI", 10),
                ).pack(side="right", padx=6)

            tk.Label(
                mst_right,
                text="Métricas del MST",
                bg=COLOR_CARD,
                fg="#9fb8d9",
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w", padx=15, pady=(15, 5))
            for insight in datos.get("mst", {}).get("insights", []):
                tk.Label(
                    mst_right,
                    text=f"{insight.get('label')}: {insight.get('value')}",
                    bg=COLOR_CARD,
                    fg="white",
                    font=("Segoe UI", 10),
                ).pack(anchor="w", padx=15, pady=2)

        def generar_resumen(auto=False):
            nonlocal btn_generar
            depto_display = depto_var.get().strip()
            depto = depto_map.get(depto_display, depto_display)
            tipo_label = tipo_var.get().strip()
            crime_value = tipo_map.get(tipo_label, "TODO")
            if not depto:
                estado_var.set("Selecciona un departamento válido.")
                return
            if btn_generar:
                btn_generar.config(state="disabled")
            estado_var.set("Generando resumen actualizado...")
            vista.update_idletasks()
            try:
                datos = B_resultados.generar_resumen_ui(DF_SIDPOL, GDF_GEO, depto, crime_value)
            except Exception as exc:
                estado_var.set(f"No se pudo generar el resumen: {exc}")
                if btn_generar:
                    btn_generar.config(state="normal")
                return

            render_resumen(datos)
            estado_var.set(f"Resumen actualizado para {depto}.")
            ULTIMO_FILTRO_ALGORITMOS["departamento"] = depto
            ULTIMO_FILTRO_ALGORITMOS["tipo_label"] = tipo_label
            ULTIMO_FILTRO_ALGORITMOS["tipo_value"] = crime_value
            if btn_generar:
                btn_generar.config(state="normal")

        btn_generar = tk.Button(
            boton_frame,
            text="Generar resumen",
            bg="#12D0A5",
            fg="#051427",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            cursor="hand2",
            command=generar_resumen,
        )
        btn_generar.pack(pady=(10, 0), padx=5)

        tk.Label(
            filtros,
            textvariable=estado_var,
            bg="#081629",
            fg="#9fb8d9",
            font=("Segoe UI", 9, "italic"),
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=10)

        if default_depto:
            vista.after(400, lambda: generar_resumen(auto=True))

    tk.Frame(panel, bg="#0F2238", height=60, width=250).place(x=0, y=ALTO-60)
    tk.Label(panel, text="Usuario", bg="#0F2238", fg="#c7d4e8",
        font=("Segoe UI", 9)).place(x=50, y=ALTO-45)
    tk.Label(panel, text=usuario, bg="#0F2238", fg="white",
        font=("Segoe UI", 11, "bold")).place(x=110, y=ALTO-47)

    if botones_refs:
        cambiar_seccion("Dashboard", botones_refs[0])

    dash.mainloop()
