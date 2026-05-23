
import os, sys, threading
from datetime import datetime
import matplotlib
matplotlib.use("Agg")  # forzar backend sin GUI antes de cualquier import de pyplot
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pandas as pd
import geopandas as gpd



from modulos import dashboard as mod_dash
from modulos import explorar_grafo as mod_grafo
from modulos import algoritmos as mod_alg
from modulos import resultados as mod_res
from modulos.widgets import (
    configure_styles, MetricCard, NavButton, FilterBar,
    StatsPanel, AlgoStatCard, ImageViewer, ScrollableFrame,
    TabBar, StatusBar, NodoCard, RutaCard,
    BG_DARK, BG_PANEL, BG_CARD, BG_CARD2, BG_LIGHT, BG_INPUT, BG_HOVER,
    ACCENT, ACCENT_DIM, DANGER, WARNING, BLUE, GOLD,
    TEXT_H, TEXT_B, TEXT_SUB, TEXT_DIM,
    F_TITLE, F_HEADER, F_SUBHEAD, F_BODY, F_SMALL, F_MONO,
)

# ══════════════════════ CONSTANTES ════════════════════════════════
W, H     = 1440, 860
PANEL_W  = 210
HDR_H    = 72
CREDENCIALES = {"Admin": "1234"}

DF_SIDPOL: pd.DataFrame = None
GDF_GEO  : gpd.GeoDataFrame = None
ULTIMO_FILTRO = {"dept": None, "tipo_lbl": None, "tipo_val": "TODO"}


# ══════════════════════ HELPERS ═══════════════════════════════════
def _center(win, w, h):
    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

def _icon(win):
    try:
        ic = tk.PhotoImage(file="img/logo.png")
        win.iconphoto(False, ic); win._ic = ic
    except Exception: pass

def _fmt(v):
    try: return f"{int(v):,}".replace(",", ".")
    except Exception: return str(v)

def _run_thread(fn, on_done=None):
    def _worker():
        result = fn()
        if on_done:
            on_done(result)
    t = threading.Thread(target=_worker, daemon=True)
    t.start()


# ══════════════════════ RAÍZ GLOBAL ══════════════════════════════
# Una sola instancia de Tk() para toda la aplicación.
_root: tk.Tk = None


def _hide_root():
    """Oculta la ventana raíz sin destruirla."""
    if _root:
        _root.withdraw()


def _show_root():
    """Muestra la ventana raíz."""
    if _root:
        _root.deiconify()


# ══════════════════════ SPLASH ════════════════════════════════════
def splash():
    import random
    global _root

    # Crear la única instancia Tk() de toda la app
    _root = tk.Tk()
    _root.withdraw()  # ocultar mientras no se usa

    SW, SH = 650, 450
    CX = SW // 2
    splash_bg = "#FFFFFF"
    star_color = "#001B38"

    sp = tk.Toplevel(_root)
    sp.overrideredirect(True)
    sp.config(bg=splash_bg)
    sp.attributes("-topmost", True)

    cvs = tk.Canvas(sp, width=SW, height=SH, bg=splash_bg, highlightthickness=0)
    cvs.pack()
    _center(sp, SW, SH)

    for _ in range(70):
        x = random.randint(16, SW - 16)
        y = random.randint(16, SH - 90)
        r = random.choice([1, 1, 2])
        cvs.create_oval(x - r, y - r, x + r, y + r, fill=star_color, outline="")

    try:
        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "unmask.png")
        logo = tk.PhotoImage(file=image_path)
        cvs.create_image(CX, 170, image=logo)
        cvs.logo = logo
    except Exception:
        cvs.create_text(CX, 150, text="UNMASK", fill=TEXT_H,
                        font=("Segoe UI", 52, "bold"))

    STATUS = [
        "Cargando dataset SIDPOL…",
        "Leyendo geometrías distritales…",
        "Inicializando módulos de análisis…",
        "Preparando algoritmos de grafos…",
        "Listo.",
    ]

    cvs.create_text(SW - 14, SH - 12,
                    text="v2.0 · UPC 2025",
                    fill="#002244", font=("Segoe UI", 8),
                    anchor="se")

    status_lbl = cvs.create_text(CX, 340, text=STATUS[0], fill="#002244", font=("Segoe UI", 10), anchor="center")
    pct_lbl = cvs.create_text(CX, 362, text="0%", fill="#002244", font=("Segoe UI", 11, "bold"), anchor="center")

    pb_x0, pb_x1 = 80, SW - 80
    pb_y0, pb_y1 = 380, 396
    cvs.create_rectangle(pb_x0, pb_y0, pb_x1, pb_y1, fill="#2A5C8A", outline="", width=0)
    pb_fill = cvs.create_rectangle(pb_x0, pb_y0, pb_x0, pb_y1, fill=ACCENT, outline="", width=0)
    shine = cvs.create_rectangle(pb_x0, pb_y0, pb_x0, pb_y0 + 3, fill="#FFFFFF", outline="", stipple="gray50")

    def _anim(step=0):
        if step > 100:
            sp.destroy()
            _cargar_y_continuar()
            return

        x2 = pb_x0 + (pb_x1 - pb_x0) * step // 100
        cvs.coords(pb_fill, pb_x0, pb_y0, x2, pb_y1)
        cvs.coords(shine, pb_x0, pb_y0, min(x2, pb_x0 + 28), pb_y0 + 3)
        cvs.itemconfig(pct_lbl, text=f"{step}%")
        idx = min(step * len(STATUS) // 101, len(STATUS) - 1)
        cvs.itemconfig(status_lbl, text=STATUS[idx])
        sp.after(18, lambda: _anim(step + 2))

    sp.after(300, _anim)
    _root.mainloop()


def _cargar_y_continuar():
    global DF_SIDPOL, GDF_GEO
    base = os.path.dirname(os.path.abspath(__file__))
    try:
        DF_SIDPOL = pd.read_csv(os.path.join(base, "data", "SIDPOL_DATASET.csv"), encoding="utf-8")
        GDF_GEO   = gpd.read_file(os.path.join(base, "data", "peru_distrital_simple.geojson"))
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar la data:\n{e}"); sys.exit(1)
    pantalla_bienvenida()


# ══════════════════════ BIENVENIDA ════════════════════════════════
def pantalla_bienvenida():
    win = tk.Toplevel(_root)
    _icon(win)
    win.title("UNMASK"); _center(win, W, H)
    win.config(bg=BG_DARK); win.resizable(True, True)
    win.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))

    cvs = tk.Canvas(win, width=W, height=H, bg=BG_DARK, highlightthickness=0)
    cvs.place(x=0, y=0, relwidth=1, relheight=1)
    try:
        bg = tk.PhotoImage(file="img/fondo_inicio.png")
        cvs.create_image(0, 0, image=bg, anchor="nw"); cvs.bg=bg
    except Exception:
        for i in range(20):
            shade = hex(int(6 + i*0.5))[2:].zfill(2)
            cvs.create_rectangle(0, i*H//20, W, (i+1)*H//20, fill=f"#0{shade}1628", outline="")

    try:
        img_btn = tk.PhotoImage(file="img/boton_iniciar.png")
        bid = cvs.create_image(W//2, H//2+60, image=img_btn); cvs.ib=img_btn
        cvs.tag_bind(bid, "<Button-1>", lambda e: (win.destroy(), pantalla_login()))
    except Exception:
        b = tk.Button(win, text="INICIAR  ▶", command=lambda: (win.destroy(), pantalla_login()),
                    bg=ACCENT, fg=BG_DARK, font=("Segoe UI", 15, "bold"),
                    relief="flat", cursor="hand2", padx=30, pady=20)
        b.place(relx=0.5, rely=0.62, anchor="center")


# ══════════════════════ LOGIN ═════════════════════════════════════
def pantalla_login():
    win = tk.Toplevel(_root)
    _icon(win)
    win.title("Acceder a UNMASK"); _center(win, W, H)
    win.config(bg=BG_DARK); win.resizable(True, True)
    win.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))

    cvs = tk.Canvas(win, width=W, height=H, bg=BG_DARK, highlightthickness=0)
    cvs.place(x=0, y=0, relwidth=1, relheight=1)
    try:
        bg = tk.PhotoImage(file="img/fondo_acceder.png")
        cvs.create_image(0, 0, image=bg, anchor="nw"); cvs.bg=bg
    except Exception:
        for i in range(20):
            shade = hex(int(6 + i*0.4))[2:].zfill(2)
            cvs.create_rectangle(0, i*H//20, W, (i+1)*H//20, fill=f"#0{shade}1628", outline="")

    # Panel login centrado
    PW, PH = 460, 370
    px, py = W//2 - PW//2, H//2 - PH//2
    cvs.create_rectangle(px+4, py+4, px+PW+4, py+PH+4, fill="#000000", stipple="gray25", outline="")
    cvs.create_rectangle(px, py, px+PW, py+PH, fill="#EBF5FF", outline="#3B82F6", width=2)
    cvs.create_rectangle(px, py, px+PW, py+5, fill=ACCENT, outline="")
    cvs.create_text(W//2, py+44, text="Acceder a UNMASK", fill="#1E3A5F",
                    font=("Segoe UI", 20, "bold"))
    cvs.create_text(W//2, py+72, text="Sistema de Monitoreo de Incidencias Delictivas",
                    fill="#4B6E8D", font=("Segoe UI", 10))

    for lbl_txt, ey in [("Nombre de usuario:", py+110), ("Contraseña:", py+195)]:
        cvs.create_text(W//2-100, ey, text=lbl_txt, fill="#1E3A5F",
                        font=("Segoe UI", 11, "bold"), anchor="w")
        cvs.create_rectangle(W//2-110, ey+26, W//2+120, ey+54,
                            fill="white", outline="#CBD5E1", width=1)

    ent_user = tk.Entry(win, width=26, font=("Segoe UI", 13), bd=0, bg="white", fg="#1E3A5F")
    cvs.create_window(W//2+5, py+148, window=ent_user, height=32)

    ent_pass = tk.Entry(win, width=26, font=("Segoe UI", 13), bd=0, bg="white",
                        fg="#1E3A5F", show="*")
    cvs.create_window(W//2+5, py+233, window=ent_pass, height=32)

    err_lbl = tk.Label(win, text="", bg="#EBF5FF", fg=DANGER,
                    font=("Segoe UI", 9, "bold"))
    cvs.create_window(W//2, py+272, window=err_lbl)

    def _login():
        u, p = ent_user.get().strip(), ent_pass.get().strip()
        if u in CREDENCIALES and CREDENCIALES[u] == p:
            win.destroy(); main_dashboard(u)
        else:
            err_lbl.config(text="⚠  Usuario o contraseña incorrectos")
            ent_pass.delete(0, "end")

    try:
        ib = tk.PhotoImage(file="img/boton_ingresar.png")
        bid = cvs.create_image(W//2, py+320, image=ib); cvs.ib=ib
        cvs.tag_bind(bid, "<Button-1>", lambda e: _login())
    except Exception:
        tk.Button(win, text="Ingresar", command=_login,
                bg=ACCENT, fg=BG_DARK, font=("Segoe UI", 12, "bold"),
                relief="flat", cursor="hand2").place(
            x=W//2-80, y=py+308, width=160, height=40)

    ent_pass.bind("<Return>", lambda e: _login())
    ent_user.focus()


# ══════════════════════ DASHBOARD PRINCIPAL ══════════════════════
def main_dashboard(usuario: str):
    configure_styles()

    win = tk.Toplevel(_root)
    _icon(win)
    win.title("UNMASK — Dashboard")
    win.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
    try: win.state("zoomed")
    except Exception: _center(win, W, H)
    win.minsize(1200, 720)
    win.config(bg=BG_DARK)

    # ── Layout raíz ──────────────────────────────────────────────
    panel = tk.Frame(win, bg=BG_PANEL, width=PANEL_W)
    panel.place(x=0, y=0, relheight=1)
    panel.pack_propagate(False)

    main = tk.Frame(win, bg=BG_DARK)
    main.place(x=PANEL_W, y=0, relwidth=1, relheight=1)

    # ── Encabezado ───────────────────────────────────────────────
    hdr = tk.Frame(main, bg=BG_CARD2, height=HDR_H)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)

    # Línea decorativa ACCENT arriba
    tk.Frame(hdr, bg=ACCENT, height=3).pack(fill="x")

    hdr_inner = tk.Frame(hdr, bg=BG_CARD2)
    hdr_inner.pack(fill="both", expand=True, padx=24)

    lbl_titulo = tk.Label(hdr_inner, text="Dashboard", fg=TEXT_H,
                        bg=BG_CARD2, font=("Segoe UI", 18, "bold"), anchor="w")
    lbl_titulo.pack(side="left", pady=10)

    lbl_sub = tk.Label(hdr_inner,
                        text="Resumen general de extorsión y sicariato — SIDPOL 2024-2025",
                        fg=TEXT_SUB, bg=BG_CARD2, font=F_SMALL, anchor="w")
    lbl_sub.pack(side="left", padx=20, pady=10)

    # Usuario badge (header derecho)
    user_f = tk.Frame(hdr_inner, bg=BG_HOVER, padx=12, pady=4)
    user_f.pack(side="right", pady=12)
    tk.Label(user_f, text="●", bg=BG_HOVER, fg=ACCENT, font=F_SMALL).pack(side="left")
    tk.Label(user_f, text=f"  {usuario}", bg=BG_HOVER, fg=TEXT_H,
            font=("Segoe UI", 10, "bold")).pack(side="left")

    # ── StatusBar ────────────────────────────────────────────────
    status = StatusBar(main)
    status.pack(side="bottom", fill="x")

    # ── Área de contenido ────────────────────────────────────────
    content_area = tk.Frame(main, bg=BG_DARK)
    content_area.pack(fill="both", expand=True)

    current_view = {"frame": None}

    def _clear_content():
        if current_view["frame"]:
            current_view["frame"].destroy()
        f = tk.Frame(content_area, bg=BG_DARK)
        f.pack(fill="both", expand=True)
        current_view["frame"] = f
        return f

    # ── Panel lateral ────────────────────────────────────────────
    try:
        logo = tk.PhotoImage(file="img/un.png")
        tk.Label(panel, image=logo, bg=BG_PANEL).place(x=12, y=12); panel.logo=logo
    except Exception: pass

    tk.Label(panel, text="UNMASK", fg=TEXT_H, bg=BG_PANEL,
            font=("Segoe UI", 17, "bold")).place(x=80, y=14)
    tk.Label(panel, text="SIDPOL 25", fg=TEXT_SUB, bg=BG_PANEL,
            font=("Segoe UI", 9)).place(x=80, y=40)

    tk.Frame(panel, bg=BG_HOVER, height=1).place(x=12, y=68, width=PANEL_W-24)

    nav_buttons = []
    SECCIONES = [
        ("Dashboard",  "⬛", "dashboard"),
        ("Grafo",      "⬡", "grafo"),
        ("Algoritmos", "⌬", "algoritmos"),
        ("Resultados", "◎", "resultados"),
    ]
    ENCABEZADOS = {
        "dashboard":  ("Dashboard",            "Resumen general — SIDPOL 2024-2025"),
        "grafo":      ("Explorar Grafo",        "Visualización territorial — Solo exploración visual"),
        "algoritmos": ("Algoritmos de Análisis","MST/Kruskal · Floyd-Warshall · BFS/DFS"),
        "resultados": ("Resultados Estratégicos","Consolidado de hallazgos algorítmicos"),
    }

    nav_btn_refs: dict = {}

    def _switch(section: str):
        for s, b in nav_btn_refs.items():
            b.set_active(s == section)
        t, sub = ENCABEZADOS.get(section, (section, ""))
        lbl_titulo.config(text=t)
        lbl_sub.config(text=sub)
        status.set("Cargando…", "info")
        frame = _clear_content()
        dispatch = {
            "dashboard":  lambda: _view_dashboard(frame),
            "grafo":      lambda: _view_grafo(frame),
            "algoritmos": lambda: _view_algoritmos(frame),
            "resultados": lambda: _view_resultados(frame),
        }
        dispatch.get(section, lambda: None)()
        status.set("Listo.", "ok")

    py_nav = 90
    for label_n, icon_n, sec in SECCIONES:
        b = NavButton(panel, label_n, icon_n, command=lambda s=sec: _switch(s))
        b.place(x=0, y=py_nav, width=PANEL_W)
        nav_btn_refs[sec] = b
        nav_buttons.append(b)
        py_nav += 52

    # Separador y pie de panel
    tk.Frame(panel, bg=BG_HOVER, height=1).place(x=12, rely=1.0, y=-56, width=PANEL_W-24)
    tk.Label(panel, text=f"● {usuario}", fg=TEXT_SUB, bg=BG_PANEL,
            font=F_SMALL).place(x=20, rely=1.0, y=-40)
    tk.Label(panel, text="v2.0 — UPC 2025", fg=TEXT_DIM, bg=BG_PANEL,
            font=("Segoe UI", 8)).place(x=20, rely=1.0, y=-22)

    # ══════════════ VISTA: DASHBOARD ════════════════════════════
    def _view_dashboard(frame):
        met = mod_dash.calcular_metricas(DF_SIDPOL)

        # ── Cards métricas — responsivas con grid ────────────────
        cards_row = tk.Frame(frame, bg=BG_DARK)
        cards_row.pack(fill="x", padx=24, pady=(18, 0))
        for i in range(4):
            cards_row.columnconfigure(i, weight=1)

        card_data = [
            ("Total Nacional",       _fmt(met["total_casos"]),        "◈", TEXT_SUB),
            ("Distritos Analizados", _fmt(met["distritos_afectados"]), "⬡", ACCENT),
            ("Casos de Sicariato",   _fmt(met["casos_sicariato"]),    "💀", DANGER),
            ("Casos de Extorsión",   _fmt(met["casos_extorsion"]),    "⚠", WARNING),
        ]
        for i, (title, val, icon, accent) in enumerate(card_data):
            card = tk.Frame(cards_row, bg=BG_CARD,
                            highlightbackground=accent, highlightthickness=1)
            card.grid(row=0, column=i, padx=(0, 12) if i < 3 else 0, sticky="nsew", ipady=6)
            tk.Frame(card, bg=accent, height=3).pack(fill="x")
            inner = tk.Frame(card, bg=BG_CARD)
            inner.pack(fill="both", expand=True, padx=14, pady=(8, 10))
            if icon:
                tk.Label(inner, text=icon, bg=BG_CARD, fg=accent, font=("Segoe UI", 13)).pack(anchor="w")
            tk.Label(inner, text=val, bg=BG_CARD, fg=TEXT_H, font=("Segoe UI", 22, "bold"), anchor="w").pack(anchor="w")
            tk.Label(inner, text=title, bg=BG_CARD, fg=TEXT_SUB, font=F_SMALL, anchor="w").pack(anchor="w")

        # ── Alerta ───────────────────────────────────────────────
        alerta_f = tk.Frame(frame, bg="#1F0505", height=36)
        alerta_f.pack(fill="x", padx=24, pady=(10, 0))
        alerta_f.pack_propagate(False)
        tk.Label(alerta_f, text=f"  ⚠  Alerta crítica:  {met['alerta']}",
                bg="#1F0505", fg="#FCA5A5", font=F_SMALL,
                wraplength=1200, justify="left", anchor="w").pack(
            fill="both", expand=True, padx=8)

        # ── Cuerpo principal ─────────────────────────────────────
        body = tk.Frame(frame, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=24, pady=10)
        body.columnconfigure(0, weight=4)   # mapa más ancho
        body.columnconfigure(1, weight=1)   # panel derecho compacto
        body.rowconfigure(0, weight=1)

        # ─ Mapa izquierda ─
        mapa_card = tk.Frame(body, bg=BG_CARD2,
                            highlightbackground=BG_HOVER, highlightthickness=1)
        mapa_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        mapa_card.rowconfigure(1, weight=1)

        hdr_mapa = tk.Frame(mapa_card, bg=BG_CARD2)
        hdr_mapa.pack(fill="x", padx=16, pady=(12, 4))
        tk.Label(hdr_mapa, text="Mapa de Riesgo Territorial", bg=BG_CARD2,
                fg=TEXT_H, font=F_HEADER).pack(side="left")
        tk.Label(hdr_mapa, text="Extorsión y Homicidio por departamento — 2024-2025",
                bg=BG_CARD2, fg=TEXT_SUB, font=F_SMALL).pack(side="left", padx=12)

        mapa_img_lbl = tk.Label(mapa_card, bg="#030914", cursor="crosshair")
        mapa_img_lbl.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        loading_lbl = tk.Label(mapa_card, text="⟳  Generando mapa…",
                                bg="#030914", fg=TEXT_DIM, font=("Segoe UI", 11, "italic"))
        loading_lbl.place(relx=0.5, rely=0.5, anchor="center")

        def _load_map():
            try:
                path = mod_dash.generar_mapa_calor(DF_SIDPOL, save_path="img/mapa_dashboard.png")
                from PIL import Image, ImageTk
                img = Image.open(path)
                mapa_img_lbl.update_idletasks()
                w = max(mapa_img_lbl.winfo_width(), 700)
                h = max(mapa_img_lbl.winfo_height(), 480)
                img.thumbnail((w, h), Image.Resampling.LANCZOS)
                ph = ImageTk.PhotoImage(img)
                mapa_img_lbl.config(image=ph); mapa_img_lbl.image = ph
                loading_lbl.place_forget()
                status.set("Mapa cargado.", "ok")
            except Exception as ex:
                loading_lbl.config(text=f"Error al generar mapa: {ex}", fg=DANGER)
                status.set(f"Error mapa: {ex}", "error")

        frame.after(400, _load_map)

        # ─ Panel derecho ─
        right = tk.Frame(body, bg=BG_DARK)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        # Botón Análisis Territorial
        an_card = tk.Frame(right, bg=BG_CARD,
                        highlightbackground=ACCENT, highlightthickness=1)
        an_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tk.Frame(an_card, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(an_card, text="Análisis Territorial", bg=BG_CARD,
                fg=TEXT_H, font=F_HEADER).pack(anchor="w", padx=14, pady=(10, 4))
        tk.Label(an_card,
                text="Explora el grafo territorial y ejecuta\nalgoritmos de análisis estructural",
                bg=BG_CARD, fg=TEXT_SUB, font=F_SMALL,
                justify="left", anchor="w", wraplength=220).pack(anchor="w", padx=14)
        tk.Button(an_card, text="Explorar Grafo  →",
                command=lambda: _switch("grafo"),
                bg=ACCENT, fg=BG_DARK, font=("Segoe UI", 10, "bold"),
                relief="flat", cursor="hand2",
                activebackground=ACCENT_DIM).pack(
            fill="x", padx=14, pady=10, ipady=6)

        # Top 5 Departamentos
        top5_f = tk.Frame(right, bg=BG_CARD,
                        highlightbackground=BG_HOVER, highlightthickness=1)
        top5_f.grid(row=1, column=0, sticky="nsew")
        tk.Frame(top5_f, bg=BG_HOVER, height=3).pack(fill="x")
        tk.Label(top5_f, text="Top 5 Departamentos", bg=BG_CARD,
                fg=TEXT_H, font=F_HEADER).pack(anchor="w", padx=14, pady=(10, 6))

        for rank, (dept, val) in enumerate(met["top_departamentos"].items(), 1):
            row_f = tk.Frame(top5_f, bg=BG_HOVER, cursor="hand2")
            row_f.pack(fill="x", padx=12, pady=3)
            rank_colors = {1: GOLD, 2: TEXT_H, 3: "#CD7F32", 4: TEXT_SUB, 5: TEXT_DIM}
            tk.Label(row_f, text=f" #{rank}", bg=BG_HOVER,
                    fg=rank_colors.get(rank, TEXT_DIM),
                    font=("Segoe UI", 11, "bold"), width=4).pack(side="left", pady=8)
            tk.Label(row_f, text=dept, bg=BG_HOVER, fg=TEXT_H,
                    font=("Segoe UI", 10, "bold"), anchor="w").pack(
                side="left", fill="x", expand=True)
            tk.Label(row_f, text=_fmt(val), bg=BG_HOVER, fg=ACCENT,
                    font=("Segoe UI", 10, "bold")).pack(side="right", padx=10)

    # ══════════════ VISTA: EXPLORAR GRAFO ═══════════════════════
    def _view_grafo(frame):
        opts = mod_grafo.obtener_opciones_filtros(DF_SIDPOL)
        deptos  = [d.upper() for d in opts["departamentos"]]
        t_opts  = opts["tipo_delito"]
        t_labels= [o["label"] for o in t_opts]
        t_map   = {o["label"]: o["value"] for o in t_opts}
        anios   = opts["anios"]
        c_opts  = opts["color_por"]
        c_labels= [o["label"] for o in c_opts]
        c_map   = {o["label"]: o["value"] for o in c_opts}

        # ── FilterBar ────────────────────────────────────────────
        fb = FilterBar(frame, filters=[
            {"key": "dept",   "label": "Departamento",  "values": deptos,   "default": deptos[0],   "width": 18},
            {"key": "tipo",   "label": "Tipo de delito","values": t_labels,  "default": t_labels[0], "width": 20},
            {"key": "anio",   "label": "Año",           "values": anios,     "default": anios[-1],   "width": 8},
            {"key": "color",  "label": "Colorear por",  "values": c_labels,  "default": c_labels[0], "width": 18},
        ], btn_text="▶  Generar Grafo")
        fb.pack(fill="x", padx=24, pady=(16, 0))

        # ── Cuerpo ───────────────────────────────────────────────
        body = tk.Frame(frame, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=24, pady=12)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)

        # Tarjeta grafo
        g_card = tk.Frame(body, bg=BG_CARD2,
                        highlightbackground=BG_HOVER, highlightthickness=1)
        g_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        g_card.rowconfigure(1, weight=1)

        g_hdr = tk.Frame(g_card, bg=BG_CARD2)
        g_hdr.pack(fill="x", padx=16, pady=(12, 4))
        lbl_g_tit = tk.Label(g_hdr, text="Grafo de Distritos", bg=BG_CARD2,
                            fg=TEXT_H, font=F_HEADER, anchor="w")
        lbl_g_tit.pack(side="left")
        lbl_g_sub = tk.Label(g_hdr, text="", bg=BG_CARD2, fg=TEXT_SUB,
                            font=F_SMALL, anchor="w")
        lbl_g_sub.pack(side="left", padx=14)

        lbl_estado_g = tk.Label(g_card,
            text="Selecciona filtros y presiona ▶ Generar Grafo",
            bg=BG_CARD2, fg=TEXT_DIM, font=("Segoe UI", 9, "italic"))
        lbl_estado_g.pack(anchor="w", padx=16, pady=(0, 4))

        iv = ImageViewer(g_card, bg="#030914", height=380)
        iv.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        iv.coords(iv._txt_id, 500, 190)

        # Leyenda
        leyenda_f = tk.Frame(g_card, bg=BG_CARD2)
        leyenda_f.pack(anchor="w", padx=16, pady=(0, 10))

        def _upd_leyenda(items):
            for w in leyenda_f.winfo_children(): w.destroy()
            for it in items:
                f = tk.Frame(leyenda_f, bg=BG_CARD2)
                f.pack(side="left", padx=10)
                cv = tk.Canvas(f, width=14, height=14, bg=BG_CARD2, highlightthickness=0)
                cv.pack(side="left")
                cv.create_oval(2, 2, 12, 12, fill=it["color"], outline=it["color"])
                tk.Label(f, text=it["label"], bg=BG_CARD2, fg=TEXT_B,
                        font=F_SMALL).pack(side="left", padx=3)

        # Panel estadísticas
        sp = StatsPanel(body, "Estadísticas del Grafo", [
            ("Nodos (distritos)",    "nodos"),
            ("Aristas (conexiones)", "aristas"),
            ("Casos totales",        "casos_totales"),
            ("Extorsión",            "extorsion"),
            ("Homicidio",            "homicidio"),
            ("Densidad del grafo",   "densidad"),
            ("Grado promedio",       "grado_promedio"),
        ])
        sp.grid(row=0, column=1, sticky="nsew")

        def _render_grafo():
            depto = fb.get("dept")
            tipo  = t_map.get(fb.get("tipo"), "TODO")
            anio  = fb.get("anio")
            color = c_map.get(fb.get("color"), "cases")
            if not depto:
                lbl_estado_g.config(text="Selecciona un departamento.", fg=DANGER)
                return
            fb.set_btn_state(False)
            lbl_estado_g.config(text="Generando grafo…", fg=TEXT_DIM)
            iv.reset()
            frame.update_idletasks()
            try:
                r = mod_grafo.generar_grafo_territorial(
                    DF_SIDPOL, GDF_GEO, depto, tipo, anio, color)
            except (ValueError, RuntimeError) as ex:
                lbl_estado_g.config(text=str(ex), fg=DANGER)
                status.set(str(ex), "error")
                fb.set_btn_state(True)
                return
            iv.show_image(r["image_path"])
            lbl_g_tit.config(text=r.get("graph_title", "Grafo"))
            lbl_g_sub.config(text=r.get("graph_subtitle", ""))
            lbl_estado_g.config(text="Grafo generado correctamente.", fg=ACCENT)
            _upd_leyenda(r.get("legend", []))
            sp.update(r.get("stats", {}),
                    ts=datetime.now().strftime("%d/%m/%Y %H:%M"))
            status.set(f"Grafo de {depto} generado.", "ok")
            fb.set_btn_state(True)

        fb.btn.config(command=_render_grafo)
        _upd_leyenda([])

    # ══════════════ VISTA: ALGORITMOS ═══════════════════════════
    def _view_algoritmos(frame):
        opts = mod_grafo.obtener_opciones_filtros(DF_SIDPOL)
        deptos  = [d.upper() for d in opts["departamentos"]]
        t_opts  = opts["tipo_delito"]
        t_labels= [o["label"] for o in t_opts]
        t_map   = {o["label"]: o["value"] for o in t_opts}

        sf = ScrollableFrame(frame, bg=BG_DARK)
        sf.pack(fill="both", expand=True)
        vista = sf.inner

        # ── FilterBar ────────────────────────────────────────────
        fb = FilterBar(vista, filters=[
            {"key": "dept", "label": "Departamento",   "values": deptos,   "default": deptos[0],   "width": 18},
            {"key": "tipo", "label": "Tipo de delito", "values": t_labels, "default": t_labels[0], "width": 22},
        ], btn_text="")  # sin botón principal aquí
        fb.pack(fill="x", padx=0, pady=(16, 0))
        fb.btn.pack_forget()  # lo ocultamos

        # Refrescar distritos cuando cambia depto
        distrito_var = tk.StringVar()
        dist_combo_ref = [None]

        def _refresh_distritos(*_):
            dep = fb.get("dept").strip()
            if not dep: return
            mask = GDF_GEO["NOMBDEP"].str.upper().str.strip() == dep
            distr = sorted(GDF_GEO.loc[mask, "NOMBDIST"].dropna().unique())
            if dist_combo_ref[0]:
                dist_combo_ref[0]["values"] = distr
                if distr: distrito_var.set(distr[0])

        fb.vars["dept"].trace_add("write", _refresh_distritos)

        # ── Tab bar ──────────────────────────────────────────────
        TAB_NAMES = ["BFS / DFS", "Floyd-Warshall", "Kruskal (MST)"]
        tab_content: dict = {}

        tab_host = tk.Frame(vista, bg=BG_DARK)
        tab_host.pack(fill="x", padx=0, pady=(12, 0))
        tab_bar = TabBar(tab_host, TAB_NAMES)
        tab_bar.pack(fill="x")

        ctrl_host = tk.Frame(vista, bg=BG_DARK, height=80)
        ctrl_host.pack(fill="x", padx=4, pady=6)
        ctrl_host.pack_propagate(False)

        # ─ Controles BFS/DFS ─
        f_bfs = tk.Frame(ctrl_host, bg=BG_DARK)
        tab_content["BFS / DFS"] = f_bfs

        metodo_var = tk.StringVar(value="BFS (Por niveles)")
        metodo_map = {"BFS (Por niveles)": "bfs", "DFS (En profundidad)": "dfs"}

        bfs_inner = tk.Frame(f_bfs, bg=BG_DARK)
        bfs_inner.pack(fill="x", pady=8)

        for col, (lbl_t, var, vals, w) in enumerate([
            ("Algoritmo",      metodo_var,  list(metodo_map.keys()), 22),
            ("Distrito inicial",distrito_var, [],                    30),
        ]):
            c = tk.Frame(bfs_inner, bg=BG_DARK)
            c.grid(row=0, column=col, padx=(0 if col==0 else 12, 12), sticky="ew")
            tk.Label(c, text=lbl_t, bg=BG_DARK, fg=TEXT_SUB,
                    font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 3))
            combo = ttk.Combobox(c, textvariable=var, values=vals,
                                state="readonly", style="Dark.TCombobox", width=w)
            combo.pack(fill="x")
            if col == 1: dist_combo_ref[0] = combo

        _refresh_distritos()

        # ─ Controles Floyd ─
        f_fw = tk.Frame(ctrl_host, bg=BG_DARK)
        tab_content["Floyd-Warshall"] = f_fw
        modo_var = tk.StringVar(value="Mayor concentración")
        modo_map = {"Mayor concentración": "volume", "Ruta eficiente": "efficiency"}
        fw_inner = tk.Frame(f_fw, bg=BG_DARK)
        fw_inner.pack(fill="x", pady=8)
        tk.Label(fw_inner, text="Modo de análisis", bg=BG_DARK, fg=TEXT_SUB,
                font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 3))
        ttk.Combobox(fw_inner, textvariable=modo_var, values=list(modo_map.keys()),
                    state="readonly", style="Dark.TCombobox", width=26).pack(anchor="w")

        # ─ Controles Kruskal ─
        f_kr = tk.Frame(ctrl_host, bg=BG_DARK)
        tab_content["Kruskal (MST)"] = f_kr
        k_var = tk.StringVar()
        kr_inner = tk.Frame(f_kr, bg=BG_DARK)
        kr_inner.pack(fill="x", pady=8)
        tk.Label(kr_inner, text="Top K nodos prioritarios (vacío = automático)",
                bg=BG_DARK, fg=TEXT_SUB, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 3))
        tk.Entry(kr_inner, textvariable=k_var, width=12,
                font=F_BODY,
                bg=BG_INPUT, fg=TEXT_H, insertbackground=TEXT_H,
                relief="flat", bd=6).pack(anchor="w")

        # Mostrar/ocultar según tab activo
        current_ctrl = {"w": None}
        def _show_ctrl(tab: str):
            if current_ctrl["w"]: current_ctrl["w"].place_forget()
            w = tab_content.get(tab)
            if w:
                w.place(x=0, y=0, relwidth=1, relheight=1)
                current_ctrl["w"] = w
            btn_exec.config(text=f"▶  Ejecutar {tab}")

        tab_bar._on_change = _show_ctrl
        _show_ctrl(TAB_NAMES[0])

        # Botón ejecutar
        btn_exec = tk.Button(vista, text="▶  Ejecutar BFS / DFS", command=lambda: None, bg=ACCENT, fg=BG_DARK, font=("Segoe UI", 11, "bold"), relief="flat", cursor="hand2", padx=20, pady=8, activebackground=ACCENT_DIM)
        btn_exec.pack(anchor="w", padx=4, pady=(0, 12))

        # ── Resultado visual ─────────────────────────────────────
        res_f = tk.Frame(vista, bg=BG_DARK)
        res_f.pack(fill="both", expand=True)
        res_f.columnconfigure(0, weight=3)
        res_f.columnconfigure(1, weight=1)

        img_card = tk.Frame(res_f, bg=BG_CARD2, highlightbackground=BG_HOVER, highlightthickness=1)
        img_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        tk.Label(img_card, text="Visualización del Algoritmo", bg=BG_CARD2, fg=TEXT_H, font=F_HEADER).pack(anchor="w", padx=14, pady=(12, 4))

        iv2 = ImageViewer(img_card, bg="#030914", height=360)
        iv2.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        estado_var = tk.StringVar(value="Configura los parámetros y ejecuta el algoritmo.")
        tk.Label(img_card, textvariable=estado_var, bg=BG_CARD2, fg=TEXT_DIM, font=("Segoe UI", 9, "italic")).pack(anchor="w", padx=14, pady=(0, 8))

        # Panel de stats del algoritmo
        stats_f = tk.Frame(res_f, bg=BG_CARD, highlightbackground=BG_HOVER, highlightthickness=1)
        stats_f.grid(row=0, column=1, sticky="nsew")
        tk.Frame(stats_f, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(stats_f, text="Análisis Completado", bg=BG_CARD, fg=TEXT_H, font=F_HEADER).pack(anchor="w", padx=14, pady=(12, 8))

        algo_cards: list = []
        for _ in range(4):
            ac = AlgoStatCard(stats_f)
            ac.pack(fill="x", padx=12, pady=5)
            algo_cards.append(ac)

        def _upd_algo_stats(pairs: list):
            for i, ac in enumerate(algo_cards):
                if i < len(pairs): ac.set(pairs[i][0], str(pairs[i][1]))
                else: ac.reset()

        # Detalle scrollado
        det_f = tk.Frame(vista, bg=BG_DARK)
        det_f.pack(fill="both", expand=True, pady=(12, 0))
        det_f.columnconfigure(0, weight=1)
        det_f.columnconfigure(1, weight=1)

        det_titles = {}
        det_txts   = {}

        for col, key in enumerate(["izq", "der"]):
            card = tk.Frame(det_f, bg=BG_CARD2, highlightbackground=BG_HOVER, highlightthickness=1)
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col else 0, 12 if col==0 else 0))
            tit = tk.Label(card, text="—", bg=BG_CARD2, fg=TEXT_H, font=F_HEADER)
            tit.pack(anchor="w", padx=14, pady=(12, 6))
            sep = tk.Frame(card, bg=BG_HOVER, height=1)
            sep.pack(fill="x", padx=14)
            txt = scrolledtext.ScrolledText(card, wrap="word", height=8, font=("Segoe UI", 9), bg=BG_CARD2, fg=TEXT_B, relief="flat", borderwidth=0, insertbackground=TEXT_H)
            txt.pack(fill="both", expand=True, padx=14, pady=(6, 14))
            txt.config(state="disabled")
            det_titles[key] = tit
            det_txts[key]   = txt

        def _set_det(key, title, content):
            det_titles[key].config(text=title)
            t = det_txts[key]
            t.config(state="normal"); t.delete("1.0","end")
            t.insert("1.0", content or "Sin información disponible.")
            t.config(state="disabled")

        # ── Formatters ───────────────────────────────────────────
        def _fmt_levels(lvls, front):
            if not lvls: return "Sin niveles detectados."
            out = []
            for l in lvls:
                nodes_str = ", ".join(l["nodes"])
                out.append(f"Nivel {l['level']} ({len(l['nodes'])} nodos — {_fmt(l['cases'])} casos):\n  {nodes_str}")
            if front: out.append(f"\nFrontera: {', '.join(front)}")
            return "\n\n".join(out)

        def _fmt_clusters(cls):
            if not cls: return "Sin agrupaciones críticas."
            return "\n\n".join(
                f"■ {c['name']}: {_fmt(c['cases'])} casos · {c['connections']} conexiones internas\n  Nodos: {', '.join(c['nodes'])}"
                for c in cls)

        def _fmt_rutas(rutas):
            if not rutas: return "Sin rutas críticas."
            return "\n\n".join(
                f"Ruta {i+1} ({_fmt(r['concentration'])} casos):\n  {' → '.join(r['path'])}"
                for i, r in enumerate(rutas[:8]))

        def _fmt_puentes(br):
            if not br: return "Sin distritos puente identificados."
            return "\n".join(f"● {b['Distrito']}: {b['Frecuencia en Rutas']} apariciones en rutas" for b in br)

        def _fmt_crit(nodes):
            if not nodes: return "Sin nodos críticos."
            return "\n".join(f"● {n['distrito']}: {_fmt(n['casos'])} casos" for n in nodes)

        def _fmt_col(col):
            if not col: return "Sin enlaces."
            return "\n".join(f"● {c['Enlace']}\n  Casos: {_fmt(c['Casos Acumulados'])} · Costo MST: {c['Costo (MST)']}" for c in col)

        # ── Ejecución ────────────────────────────────────────────
        def _ejecutar():
            global ULTIMO_FILTRO
            dept  = fb.get("dept").strip()
            crime = t_map.get(fb.get("tipo"), "TODO")
            if not dept:
                estado_var.set("Selecciona un departamento."); return
            btn_exec.config(state="disabled")
            estado_var.set("Preparando grafo…")
            iv2.reset()
            for ac in algo_cards: ac.reset()
            vista.update_idletasks()
            try:
                G, crime_types = mod_alg.preparar_grafo_para_algoritmos(
                    DF_SIDPOL, GDF_GEO, dept, crime, verbose=False)
            except Exception as ex:
                estado_var.set(f"Error al preparar grafo: {ex}")
                status.set(str(ex), "error")
                btn_exec.config(state="normal"); return

            if not G or not G.nodes:
                estado_var.set("Grafo vacío para los filtros seleccionados.")
                btn_exec.config(state="normal"); return

            ULTIMO_FILTRO.update({"dept": dept, "tipo_lbl": fb.get("tipo"), "tipo_val": crime})
            tab = tab_bar.active

            try:
                estado_var.set(f"Ejecutando {tab}…")
                vista.update_idletasks()

                if tab == "BFS / DFS":
                    inicio = distrito_var.get().strip()
                    if not inicio or inicio not in G:
                        estado_var.set("Distrito inicial no válido."); btn_exec.config(state="normal"); return
                    met = metodo_map.get(metodo_var.get(), "bfs")
                    r = mod_alg.expansion_tree(G, inicio, met, crime_types=crime_types, verbose=False)
                    if not r: estado_var.set("No se generó el árbol."); btn_exec.config(state="normal"); return
                    st = r.get("stats", {})
                    _upd_algo_stats([
                        ("Algoritmo ejecutado", st.get("algoritmo","--")),
                        ("Nodos alcanzados",    st.get("nodos_alcanzados_pct","--")),
                        ("Casos acumulados",    _fmt(st.get("casos_acumulados_ruta",0))),
                        ("Profundidad máxima",  st.get("profundidad_maxima","--")),
                    ])
                    iv2.show_image(r.get("image_path"))
                    _set_det("izq","Árbol de Expansión por Niveles", _fmt_levels(r.get("levels",[]),r.get("frontier_nodes",[])))
                    _set_det("der","Agrupaciones Delictivas Detectadas",_fmt_clusters(r.get("clusters",[])))
                    estado_var.set(f"✓  Árbol {met.upper()} generado desde {inicio}.")
                    status.set(f"BFS/DFS completado — {_fmt(st.get('casos_acumulados_ruta',0))} casos acumulados.", "ok")

                elif tab == "Floyd-Warshall":
                    modo = modo_map.get(modo_var.get(), "volume")
                    r = mod_alg.floyd_warshall_routes(G, crime_types=crime_types, mode=modo, verbose=False)
                    if not r: estado_var.set("No se calcularon rutas."); btn_exec.config(state="normal"); return
                    st = r.get("stats",{})
                    _upd_algo_stats([
                        ("Caminos calculados",   _fmt(st.get("num_caminos_calculados",0))),
                        ("Distritos puente",     st.get("num_distritos_puentes","--")),
                        ("Máx. concentración",   _fmt(st.get("mayor_concentracion_casos",0))),
                        ("Casos ruta eficiente", _fmt(st.get("ruta_mas_eficiente_casos",0))),
                    ])
                    iv2.show_image(r.get("image_path"))
                    _set_det("izq","Rutas Críticas Identificadas",      _fmt_rutas(r.get("critical_paths",[])))
                    _set_det("der","Distritos Puente Estratégicos",     _fmt_puentes(r.get("bridge_report",[])))
                    estado_var.set(f"✓  Floyd-Warshall completado — {_fmt(st.get('num_caminos_calculados',0))} rutas analizadas.")
                    status.set("Floyd-Warshall completado.", "ok")

                else:  # Kruskal
                    kv = k_var.get().strip()
                    k_num = int(kv) if kv.isdigit() else None
                    r = mod_alg.kruskal_mst_analysis(G, k=k_num, crime_types=crime_types, verbose=False)
                    if not r: estado_var.set("No se calculó el MST."); btn_exec.config(state="normal"); return
                    st = r.get("stats",{})
                    _upd_algo_stats([
                        ("Aristas en MST",      st.get("MST_aristas","--")),
                        ("Aristas eliminadas",  st.get("aristas_eliminadas","--")),
                        ("Reducción de peso",   f"{st.get('reduccion_peso_pct',0):.1f}%"),
                        ("Focos detectados",    st.get("focos_del_crimen_detectados","--")),
                    ])
                    iv2.show_image(r.get("image_path"))
                    _set_det("izq","Nodos Críticos",           _fmt_crit(r.get("critical_nodes",[])))
                    _set_det("der","Columna Central (Kruskal)",_fmt_col(r.get("central_column",[])))
                    estado_var.set(f"✓  Kruskal MST — {st.get('MST_aristas','?')} aristas esenciales.")
                    status.set("Kruskal MST completado.", "ok")

            except Exception as ex:
                estado_var.set(f"Error al ejecutar {tab}: {ex}")
                status.set(str(ex), "error")
            finally:
                btn_exec.config(state="normal")

        btn_exec.config(command=_ejecutar)

    # ══════════════ VISTA: RESULTADOS ═══════════════════════════
    def _view_resultados(frame):
        opts = mod_grafo.obtener_opciones_filtros(DF_SIDPOL)
        deptos  = [d.upper() for d in opts["departamentos"]]
        t_opts  = opts["tipo_delito"]
        t_labels= [o["label"] for o in t_opts]
        t_map   = {o["label"]: o["value"] for o in t_opts}

        def_dept = (ULTIMO_FILTRO.get("dept") or deptos[0]).upper()
        def_tipo = ULTIMO_FILTRO.get("tipo_lbl") or t_labels[0]

        # Filtros superiores
        filter_area = tk.Frame(frame, bg="#081629")
        filter_area.pack(fill="x", padx=24, pady=(16, 0))

        tk.Label(filter_area, text="Resultados del Análisis Territorial",
                bg="#081629", fg=TEXT_H, font=("Segoe UI", 14, "bold")).pack(
            anchor="w", padx=14, pady=(12, 2))
        tk.Label(filter_area, text="Consolidado de hallazgos — BFS/DFS · Floyd-Warshall · Kruskal MST",
                bg="#081629", fg=TEXT_SUB, font=F_SMALL).pack(anchor="w", padx=14)

        row_f = tk.Frame(filter_area, bg="#081629")
        row_f.pack(fill="x", padx=14, pady=(10, 14))

        depto_v = tk.StringVar(value=def_dept)
        tipo_v  = tk.StringVar(value=def_tipo)

        for i, (lbl_t, var, vals, w) in enumerate([
            ("Departamento",  depto_v, deptos,   18),
            ("Tipo de delito",tipo_v,  t_labels, 22),
        ]):
            cf = tk.Frame(row_f, bg="#081629")
            cf.grid(row=0, column=i, padx=(0, 20), sticky="ew")
            tk.Label(cf, text=lbl_t, bg="#081629", fg=TEXT_SUB,
                    font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 3))
            ttk.Combobox(cf, textvariable=var, values=vals,
                        state="readonly", style="Dark.TCombobox", width=w).pack(fill="x")

        estado_v = tk.StringVar(value="Selecciona departamento y genera el resumen.")
        tk.Label(filter_area, textvariable=estado_v, bg="#081629",
                fg=TEXT_SUB, font=F_SMALL).pack(anchor="w", padx=14, pady=(0, 8))

        mst_img_cache = {"ph": None}

        # Scroll body
        sf = ScrollableFrame(frame, bg=BG_DARK)
        sf.pack(fill="both", expand=True, padx=24, pady=8)
        body = sf.inner

        def _render(datos: dict):
            for w in body.winfo_children(): w.destroy()
            if not datos:
                tk.Label(body, text="Sin datos disponibles para los filtros seleccionados.",
                    bg=BG_DARK, fg=TEXT_SUB, font=F_BODY).pack(pady=40)
                return

            # Cards
            cards_row = tk.Frame(body, bg=BG_DARK)
            cards_row.pack(fill="x", pady=(8, 6))
            card_icons = ["◈","⬡","⌬","◎","⚡"]
            card_accents = [ACCENT, WARNING, DANGER, BLUE, GOLD]
            for i, c in enumerate(datos.get("cards", [])):
                mc = MetricCard(cards_row, title=c["label"],
                                value=_fmt(c["value"]),
                                icon=card_icons[i] if i<len(card_icons) else "",
                                accent=card_accents[i] if i<len(card_accents) else ACCENT,
                                width=210, height=95)
                mc.grid(row=0, column=i, padx=(0,10), sticky="ew")
                cards_row.columnconfigure(i, weight=1)

            # Nodos estratégicos
            sec_hdr(body, "⬡  Nodos Estratégicos Identificados")
            for nd in datos.get("nodos", []):
                nc = NodoCard(body, nd)
                nc.pack(fill="x", padx=4, pady=5)

            # Rutas críticas
            sec_hdr(body, "⌬  Rutas Críticas de Propagación")
            for rt in datos.get("rutas", []):
                rc = RutaCard(body, rt)
                rc.pack(fill="x", padx=4, pady=5)

            # MST
            sec_hdr(body, "◎  Red Mínima de Intervención — Kruskal MST")
            mst = datos.get("mst", {})
            mst_wrap = tk.Frame(body, bg=BG_DARK)
            mst_wrap.pack(fill="x", padx=4, pady=(0, 20))
            mst_wrap.columnconfigure(0, weight=2)
            mst_wrap.columnconfigure(1, weight=1)

            # Imagen MST
            ml = tk.Frame(mst_wrap, bg=BG_CARD,
                        highlightbackground=BG_HOVER, highlightthickness=1)
            ml.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
            tk.Frame(ml, bg=ACCENT, height=3).pack(fill="x")
            tk.Label(ml, text="Árbol de expansión mínima — Algoritmo Kruskal",
                    bg=BG_CARD, fg=TEXT_H, font=F_HEADER).pack(anchor="w", padx=14, pady=(10, 6))

            cvs_mst = tk.Canvas(ml, width=460, height=260, bg="#051024", highlightthickness=0)
            cvs_mst.pack(padx=14, pady=(0, 10))
            img_path = mst.get("image_path")
            if img_path and os.path.exists(img_path):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(img_path)
                    img.thumbnail((440, 240), Image.Resampling.LANCZOS)
                    ph = ImageTk.PhotoImage(img)
                    mst_img_cache["ph"] = ph
                    cvs_mst.create_image(230, 130, image=ph)
                except Exception:
                    cvs_mst.create_text(230, 130, text="Sin visualización", fill=TEXT_DIM)
            else:
                cvs_mst.create_text(230, 130, text="Sin visualización disponible", fill=TEXT_DIM)

            # Métricas MST
            mets_f = tk.Frame(ml, bg=BG_CARD)
            mets_f.pack(fill="x", padx=14, pady=(0, 12))
            for m in mst.get("metrics", []):
                blk = tk.Frame(mets_f, bg=BG_HOVER, width=140, height=55)
                blk.pack(side="left", padx=(0, 6))
                blk.pack_propagate(False)
                tk.Label(blk, text=m.get("label",""), bg=BG_HOVER,
                        fg=TEXT_SUB, font=F_SMALL).pack(anchor="w", padx=10, pady=(6,0))
                tk.Label(blk, text=_fmt(m.get("value","--")), bg=BG_HOVER,
                        fg=TEXT_H, font=("Segoe UI",13,"bold")).pack(anchor="w", padx=10)

            # Conexiones MST
            mr = tk.Frame(mst_wrap, bg=BG_CARD,
                        highlightbackground=BG_HOVER, highlightthickness=1)
            mr.grid(row=0, column=1, sticky="nsew")
            tk.Frame(mr, bg=GOLD, height=3).pack(fill="x")
            tk.Label(mr, text="Conexiones críticas", bg=BG_CARD,
                    fg=TEXT_H, font=F_HEADER).pack(anchor="w", padx=14, pady=(10, 6))

            for conn in mst.get("conexiones", []):
                rf = tk.Frame(mr, bg=BG_HOVER)
                rf.pack(fill="x", padx=12, pady=3)
                tk.Label(rf, text=str(conn.get("rank","")), bg=BG_INPUT, fg=GOLD,
                        font=("Segoe UI",10,"bold"), width=3).pack(side="left", padx=6, pady=6)
                tk.Label(rf, text=conn.get("enlace","--"), bg=BG_HOVER,
                        fg=TEXT_H, font=("Segoe UI",10,"bold")).pack(side="left")
                tk.Label(rf, text=_fmt(conn.get("casos","--")), bg=BG_HOVER,
                        fg=ACCENT, font=("Segoe UI",10)).pack(side="right", padx=10)

            tk.Label(mr, text="Métricas del MST", bg=BG_CARD, fg=TEXT_SUB,
                    font=("Segoe UI",10,"bold")).pack(anchor="w", padx=14, pady=(14,4))
            for ins in mst.get("insights", []):
                tk.Label(mr, text=f"  {ins.get('label')}: {ins.get('value')}",
                        bg=BG_CARD, fg=TEXT_B, font=F_SMALL).pack(anchor="w", padx=14, pady=2)

        def sec_hdr(parent, text):
            hf = tk.Frame(parent, bg=BG_DARK)
            hf.pack(fill="x", pady=(18, 6))
            tk.Frame(hf, bg=ACCENT, width=4, height=24).pack(side="left")
            tk.Label(hf, text=f"  {text}", bg=BG_DARK, fg=TEXT_H,
                    font=("Segoe UI",13,"bold")).pack(side="left")

        def _generar():
            global ULTIMO_FILTRO
            dept  = depto_v.get().strip()
            crime = t_map.get(tipo_v.get(), "TODO")
            if not dept:
                estado_v.set("Selecciona un departamento."); return
            btn_gen.config(state="disabled")
            estado_v.set("Generando resumen…")
            frame.update_idletasks()
            try:
                datos = mod_res.generar_resumen_ui(DF_SIDPOL, GDF_GEO, dept, crime)
            except Exception as ex:
                estado_v.set(f"Error: {ex}"); status.set(str(ex), "error")
                btn_gen.config(state="normal"); return
            _render(datos)
            estado_v.set(f"Resumen actualizado para {dept}.")
            ULTIMO_FILTRO.update({"dept": dept, "tipo_lbl": tipo_v.get(), "tipo_val": crime})
            status.set(f"Análisis estratégico de {dept} completado.", "ok")
            btn_gen.config(state="normal")

        btn_gen = tk.Button(row_f, text="Generar resumen", command=_generar,
                            bg=ACCENT, fg=BG_DARK, font=("Segoe UI",10,"bold"),
                            relief="flat", cursor="hand2",
                            padx=14, pady=6, activebackground=ACCENT_DIM)
        btn_gen.grid(row=0, column=2, padx=(20, 0), sticky="w")

        if def_dept:
            frame.after(500, _generar)

    # Iniciar con Dashboard
    _switch("dashboard")


if __name__ == "__main__":
    splash()
