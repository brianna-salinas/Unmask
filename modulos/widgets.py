"""
widgets.py — Componentes UI reutilizables para UNMASK v2
Tkinter custom widgets con estética moderna oscura
"""
import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Dict, Optional, Tuple

# ─────────────────────── PALETA ───────────────────────────────────
BG_DARK    = "#060F1E"
BG_PANEL   = "#0D1F38"
BG_CARD    = "#122444"
BG_CARD2   = "#0F1E35"
BG_INPUT   = "#142541"
BG_HOVER   = "#1A2F50"
BG_LIGHT   = "#EEF2F6"

ACCENT     = "#12D0A5"
ACCENT_DIM = "#0CA88A"
DANGER     = "#EF4444"
WARNING    = "#F97316"
BLUE       = "#2563EB"
GOLD       = "#FBBF24"

TEXT_H     = "#F8FAFC"
TEXT_B     = "#CBD5E1"
TEXT_SUB   = "#94A3B8"
TEXT_DIM   = "#475569"

F_TITLE   = ("Segoe UI", 20, "bold")
F_HEADER  = ("Segoe UI", 13, "bold")
F_SUBHEAD = ("Segoe UI", 11, "bold")
F_BODY    = ("Segoe UI", 10)
F_SMALL   = ("Segoe UI", 9)
F_MONO    = ("Consolas", 9)


def configure_styles():
    """Configura ttk styles globales."""
    s = ttk.Style()
    try:
        s.theme_use("default")
    except Exception:
        pass

    s.configure("Dark.TCombobox",
        fieldbackground=BG_INPUT,
        background=BG_INPUT,
        foreground=TEXT_H,
        borderwidth=0,
        relief="flat",
        arrowcolor=ACCENT,
        selectbackground=BG_HOVER,
        selectforeground=TEXT_H,
    )
    s.map("Dark.TCombobox",
        fieldbackground=[("readonly", BG_INPUT), ("focus", BG_HOVER)],
        foreground=[("readonly", TEXT_H)],
        background=[("readonly", BG_INPUT)],
    )

    s.configure("Accent.TProgressbar",
        troughcolor=BG_CARD,
        background=ACCENT,
        thickness=4,
    )


# ─────────────────────── MetricCard ───────────────────────────────
class MetricCard(tk.Frame):
    """Tarjeta de métrica con valor grande, etiqueta y color de acento."""
    def __init__(self, parent, title: str, value: str = "--",
                 icon: str = "", accent: str = ACCENT,
                 width: int = 200, height: int = 100, **kw):
        super().__init__(parent, bg=BG_CARD, width=width, height=height,
                         highlightbackground=accent, highlightthickness=1, **kw)
        self.pack_propagate(False)
        self.grid_propagate(False)

        # Franja superior de color
        bar = tk.Frame(self, bg=accent, height=3)
        bar.pack(fill="x")

        body = tk.Frame(self, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=14, pady=8)

        row = tk.Frame(body, bg=BG_CARD)
        row.pack(fill="x")
        if icon:
            tk.Label(row, text=icon, bg=BG_CARD, fg=accent,
                     font=("Segoe UI", 14)).pack(side="left")

        self._val_lbl = tk.Label(body, text=value, bg=BG_CARD, fg=TEXT_H,
                                  font=("Segoe UI", 22, "bold"), anchor="w")
        self._val_lbl.pack(anchor="w")

        self._title_lbl = tk.Label(body, text=title, bg=BG_CARD, fg=TEXT_SUB,
                                    font=F_SMALL, anchor="w")
        self._title_lbl.pack(anchor="w")

    def set_value(self, value: str):
        self._val_lbl.config(text=str(value))


# ─────────────────────── NavButton ────────────────────────────────
class NavButton(tk.Frame):
    """Botón de navegación lateral con hover y estado activo."""
    def __init__(self, parent, text: str, icon: str = "",
                 command: Callable = None, **kw):
        super().__init__(parent, bg=BG_PANEL, cursor="hand2", **kw)
        self._cmd = command
        self._active = False

        self._bar = tk.Frame(self, bg=BG_PANEL, width=3)
        self._bar.pack(side="left", fill="y")

        content = tk.Frame(self, bg=BG_PANEL)
        content.pack(side="left", fill="both", expand=True, padx=8, pady=10)

        self._icon_lbl = tk.Label(content, text=icon, bg=BG_PANEL,
                                   fg=TEXT_SUB, font=("Segoe UI", 13))
        self._icon_lbl.pack(side="left", padx=(0, 8))

        self._text_lbl = tk.Label(content, text=text, bg=BG_PANEL,
                                   fg=TEXT_SUB, font=F_BODY, anchor="w")
        self._text_lbl.pack(side="left", fill="x", expand=True)

        for w in (self, content, self._icon_lbl, self._text_lbl):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _on_click(self, _=None):
        if self._cmd:
            self._cmd()

    def _on_enter(self, _=None):
        if not self._active:
            for w in (self, self._text_lbl, self._icon_lbl):
                w.config(bg=BG_HOVER)

    def _on_leave(self, _=None):
        if not self._active:
            for w in (self, self._text_lbl, self._icon_lbl):
                w.config(bg=BG_PANEL)

    def set_active(self, active: bool):
        self._active = active
        if active:
            bg = BG_CARD
            fg = ACCENT
            bar_bg = ACCENT
        else:
            bg = BG_PANEL
            fg = TEXT_SUB
            bar_bg = BG_PANEL
        for w in (self, self._text_lbl, self._icon_lbl):
            w.config(bg=bg)
        self._text_lbl.config(fg=fg, font=("Segoe UI", 10, "bold") if active else F_BODY)
        self._icon_lbl.config(fg=fg)
        self._bar.config(bg=bar_bg)


# ─────────────────────── FilterBar ────────────────────────────────
class FilterBar(tk.Frame):
    """Barra de filtros con combos estilizados."""
    def __init__(self, parent, filters: List[Dict], btn_text: str = "▶  Generar",
                 btn_cmd: Callable = None, **kw):
        super().__init__(parent, bg="#081629", **kw)
        self.vars: Dict[str, tk.StringVar] = {}
        self.combos: Dict[str, ttk.Combobox] = {}

        for i, f in enumerate(filters):
            key = f["key"]
            var = tk.StringVar(value=f.get("default", ""))
            self.vars[key] = var

            col_frame = tk.Frame(self, bg="#081629")
            col_frame.grid(row=0, column=i, padx=12, pady=14, sticky="ew")
            self.columnconfigure(i, weight=1)

            tk.Label(col_frame, text=f["label"], bg="#081629", fg=TEXT_SUB,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))

            combo = ttk.Combobox(col_frame, textvariable=var,
                                  values=f.get("values", []),
                                  state="readonly",
                                  style="Dark.TCombobox",
                                  width=f.get("width", 18))
            combo.pack(fill="x")
            self.combos[key] = combo

            if f.get("trace"):
                var.trace_add("write", f["trace"])

        # Botón ejecutar
        btn_frame = tk.Frame(self, bg="#081629")
        btn_frame.grid(row=0, column=len(filters), padx=(8, 14), pady=14, sticky="ew")

        self.btn = tk.Button(
            btn_frame, text=btn_text, command=btn_cmd or (lambda: None),
            bg=ACCENT, fg=BG_DARK, font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", padx=16, pady=8,
            activebackground=ACCENT_DIM, activeforeground=BG_DARK,
        )
        self.btn.pack(fill="both", expand=True)

    def get(self, key: str) -> str:
        return self.vars[key].get()

    def set_btn_state(self, enabled: bool):
        self.btn.config(state="normal" if enabled else "disabled")


# ─────────────────────── StatsPanel ───────────────────────────────
class StatsPanel(tk.Frame):
    """Panel lateral de estadísticas con filas clave-valor."""
    def __init__(self, parent, title: str, fields: List[Tuple[str, str]], **kw):
        super().__init__(parent, bg=BG_CARD, **kw)
        self._labels: Dict[str, tk.Label] = {}

        tk.Label(self, text=title, bg=BG_CARD, fg=TEXT_H,
                 font=F_HEADER).pack(anchor="w", padx=14, pady=(14, 10))

        sep = tk.Frame(self, bg=BG_HOVER, height=1)
        sep.pack(fill="x", padx=14, pady=(0, 8))

        for label, key in fields:
            row = tk.Frame(self, bg=BG_CARD)
            row.pack(fill="x", padx=14, pady=3)
            tk.Label(row, text=label, bg=BG_CARD, fg=TEXT_SUB,
                     font=F_SMALL).pack(side="left")
            lbl = tk.Label(row, text="—", bg=BG_CARD, fg=TEXT_H,
                           font=("Segoe UI", 10, "bold"))
            lbl.pack(side="right")
            self._labels[key] = lbl

        self._ts = tk.Label(self, text="", bg=BG_CARD, fg=TEXT_DIM, font=F_SMALL)
        self._ts.pack(anchor="w", padx=14, pady=(8, 14))

    def update(self, data: Dict, ts: str = ""):
        for key, lbl in self._labels.items():
            val = data.get(key)
            if val is None:
                lbl.config(text="—")
            elif isinstance(val, float):
                lbl.config(text=f"{val:.2f}")
            elif isinstance(val, int):
                lbl.config(text=f"{val:,}".replace(",", "."))
            else:
                lbl.config(text=str(val))
        if ts:
            self._ts.config(text=f"Actualizado: {ts}")

    def reset(self):
        for lbl in self._labels.values():
            lbl.config(text="—")
        self._ts.config(text="")


# ─────────────────────── AlgoStatCard ─────────────────────────────
class AlgoStatCard(tk.Frame):
    """Mini tarjeta para mostrar un resultado de algoritmo."""
    def __init__(self, parent, **kw):
        super().__init__(parent, bg="#0B1C32", **kw)
        self._title = tk.Label(self, text="—", bg="#0B1C32", fg=TEXT_SUB, font=F_SMALL)
        self._title.pack(anchor="w", padx=12, pady=(8, 0))
        self._value = tk.Label(self, text="—", bg="#0B1C32", fg=TEXT_H,
                                font=("Segoe UI", 16, "bold"))
        self._value.pack(anchor="w", padx=12, pady=(0, 8))

    def set(self, title: str, value: str):
        self._title.config(text=title)
        self._value.config(text=str(value))

    def reset(self):
        self._title.config(text="—")
        self._value.config(text="—")


# ─────────────────────── ImageViewer ──────────────────────────────
class ImageViewer(tk.Canvas):
    """Canvas con placeholder, centrado automático y zoom."""
    PLACEHOLDER = "Imagen generada aquí"

    def __init__(self, parent, bg: str = "#030914", **kw):
        super().__init__(parent, bg=bg, highlightthickness=0, **kw)
        self._ph = None
        self._img_id = None
        self._txt_id = self.create_text(
            400, 200,
            text=self.PLACEHOLDER,
            fill=TEXT_DIM, font=("Segoe UI", 11),
            width=700,
        )

    def show_image(self, path: str):
        from PIL import Image, ImageTk
        import os
        if not path or not os.path.exists(path):
            self._show_placeholder("Imagen no encontrada")
            return
        try:
            img = Image.open(path)
            self.update_idletasks()
            w = self.winfo_width() or 700
            h = self.winfo_height() or 380
            img.thumbnail((w - 10, h - 10), Image.Resampling.LANCZOS)
            ph = ImageTk.PhotoImage(img)
            self._ph = ph
            if self._img_id:
                self.delete(self._img_id)
            self._img_id = self.create_image(w // 2, h // 2, image=ph, anchor="center")
            self.itemconfig(self._txt_id, state="hidden")
        except Exception as e:
            self._show_placeholder(f"Error: {e}")

    def _show_placeholder(self, msg: str = ""):
        if self._img_id:
            self.delete(self._img_id)
            self._img_id = None
        self._ph = None
        self.itemconfig(self._txt_id, text=msg or self.PLACEHOLDER, state="normal")

    def reset(self):
        self._show_placeholder()


# ─────────────────────── ScrollableFrame ──────────────────────────
class ScrollableFrame(tk.Frame):
    """Frame con scroll vertical que se adapta al ancho."""
    def __init__(self, parent, bg: str = BG_DARK, **kw):
        super().__init__(parent, bg=bg, **kw)

        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self._sb = tk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._sb.set)

        self._sb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self._canvas, bg=bg)
        self._win_id = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_inner_cfg)
        self._canvas.bind("<Configure>", self._on_canvas_cfg)
        self._canvas.bind_all("<MouseWheel>", self._on_scroll)

    def _on_inner_cfg(self, _):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_cfg(self, e):
        self._canvas.itemconfig(self._win_id, width=e.width)

    def _on_scroll(self, e):
        self._canvas.yview_scroll(-1 * int(e.delta / 120), "units")


# ─────────────────────── TabBar ───────────────────────────────────
class TabBar(tk.Frame):
    """Barra de pestañas con indicador activo y callbacks."""
    def __init__(self, parent, tabs: List[str], on_change: Callable = None, **kw):
        super().__init__(parent, bg=BG_DARK, **kw)
        self._on_change = on_change
        self._btns: Dict[str, tk.Label] = {}
        self._active: str = tabs[0] if tabs else ""

        for i, tab in enumerate(tabs):
            b = tk.Label(self, text=tab, cursor="hand2",
                         font=("Segoe UI", 10, "bold"),
                         padx=20, pady=9)
            b.grid(row=0, column=i, sticky="nsew")
            self.columnconfigure(i, weight=1)
            b.bind("<Button-1>", lambda e, t=tab: self.select(t))
            self._btns[tab] = b
        self._refresh()

    def select(self, tab: str):
        self._active = tab
        self._refresh()
        if self._on_change:
            self._on_change(tab)

    def _refresh(self):
        for tab, btn in self._btns.items():
            if tab == self._active:
                btn.config(bg=BG_CARD, fg=ACCENT,
                           font=("Segoe UI", 10, "bold"),
                           relief="flat")
            else:
                btn.config(bg="#1A2A40", fg=TEXT_SUB,
                           font=("Segoe UI", 10),
                           relief="flat")

    @property
    def active(self) -> str:
        return self._active


# ─────────────────────── StatusBar ────────────────────────────────
class StatusBar(tk.Frame):
    """Barra de estado inferior con indicador de color."""
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG_CARD2, height=28, **kw)
        self.pack_propagate(False)
        self._dot = tk.Label(self, text="●", bg=BG_CARD2, fg=TEXT_DIM, font=F_SMALL)
        self._dot.pack(side="left", padx=(10, 4), pady=5)
        self._lbl = tk.Label(self, text="Listo.", bg=BG_CARD2, fg=TEXT_SUB, font=F_SMALL)
        self._lbl.pack(side="left", pady=5)

    def set(self, msg: str, kind: str = "info"):
        colors = {"info": TEXT_SUB, "ok": ACCENT, "error": DANGER, "warn": WARNING}
        dot_c  = {"info": TEXT_DIM, "ok": ACCENT, "error": DANGER, "warn": WARNING}
        self._lbl.config(text=msg, fg=colors.get(kind, TEXT_SUB))
        self._dot.config(fg=dot_c.get(kind, TEXT_DIM))


# ─────────────────────── NodoCard ─────────────────────────────────
class NodoCard(tk.Frame):
    """Tarjeta de nodo estratégico para la vista Resultados."""
    NIVEL_COLORS = {"Crítico": DANGER, "Alto": WARNING, "Medio": ACCENT}

    def __init__(self, parent, data: Dict, **kw):
        super().__init__(parent, bg=BG_CARD,
                         highlightbackground=BG_HOVER, highlightthickness=1, **kw)
        nivel = data.get("nivel", "Medio")
        color = self.NIVEL_COLORS.get(nivel, ACCENT)

        # Franja lateral de color
        tk.Frame(self, bg=color, width=4).pack(side="left", fill="y")

        body = tk.Frame(self, bg=BG_CARD)
        body.pack(side="left", fill="both", expand=True, padx=14, pady=12)

        # Header
        hdr = tk.Frame(body, bg=BG_CARD)
        hdr.pack(fill="x")

        # Badge sigla
        badge = tk.Frame(hdr, bg=BG_HOVER, width=46, height=46)
        badge.pack(side="left")
        badge.pack_propagate(False)
        tk.Label(badge, text=data.get("sigla", "??"), bg=BG_HOVER,
                 fg=color, font=("Segoe UI", 11, "bold")).pack(expand=True)

        # Info
        info = tk.Frame(hdr, bg=BG_CARD)
        info.pack(side="left", padx=12, fill="x", expand=True)
        tk.Label(info, text=data.get("nombre", "--"), bg=BG_CARD, fg=TEXT_H,
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(anchor="w")
        tk.Label(info, text=data.get("rol", ""), bg=BG_CARD, fg=TEXT_SUB,
                 font=F_SMALL, anchor="w").pack(anchor="w", pady=(2, 0))

        # Chip nivel
        chip = tk.Label(hdr, text=f"  {nivel}  ", bg=color, fg="white",
                        font=("Segoe UI", 8, "bold"), padx=4, pady=2)
        chip.pack(side="right", anchor="n")

        # Métricas
        mf = tk.Frame(body, bg=BG_CARD)
        mf.pack(fill="x", pady=(8, 0))
        for lbl, val in [
            ("Extorsión",  data.get("extorsion", 0)),
            ("Homicidio",  data.get("sicariato", 0)),
            ("Total casos", data.get("total", 0)),
        ]:
            it = tk.Frame(mf, bg=BG_HOVER, width=150, height=46)
            it.pack(side="left", padx=(0, 6))
            it.pack_propagate(False)
            tk.Label(it, text=lbl, bg=BG_HOVER, fg=TEXT_SUB,
                     font=F_SMALL).pack(anchor="w", padx=10, pady=(5, 0))
            tk.Label(it, text=f"{val:,}".replace(",", ".") if isinstance(val, int) else str(val),
                     bg=BG_HOVER, fg=TEXT_H,
                     font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10)

        # Tags algoritmos
        tags_f = tk.Frame(body, bg=BG_CARD)
        tags_f.pack(fill="x", pady=(8, 0))
        tk.Label(tags_f, text="Detectado por:", bg=BG_CARD, fg=TEXT_DIM,
                 font=F_SMALL).pack(side="left", padx=(0, 6))
        for alg in data.get("algoritmos", []):
            tk.Label(tags_f, text=alg, bg=BG_HOVER, fg=ACCENT,
                     font=("Segoe UI", 8, "bold"), padx=8, pady=2).pack(side="left", padx=3)

        # Recomendación
        tk.Label(body, text=data.get("recomendacion", ""),
                 bg=BG_CARD, fg=TEXT_B, font=F_SMALL,
                 wraplength=820, justify="left", anchor="w").pack(
            fill="x", pady=(8, 0))


# ─────────────────────── RutaCard ─────────────────────────────────
class RutaCard(tk.Frame):
    """Tarjeta de ruta crítica."""
    RISK_COLORS = {
        "Riesgo crítico": DANGER,
        "Riesgo alto": WARNING,
        "Riesgo medio": GOLD,
        "Riesgo bajo": ACCENT,
    }

    def __init__(self, parent, data: Dict, **kw):
        super().__init__(parent, bg="#111E37",
                         highlightbackground="#242F4A", highlightthickness=1, **kw)
        riesgo = data.get("riesgo", "Riesgo medio")
        color  = self.RISK_COLORS.get(riesgo, BLUE)

        hdr = tk.Frame(self, bg="#111E37")
        hdr.pack(fill="x", padx=14, pady=10)

        tk.Label(hdr, text=data.get("id", "R"), bg=BG_HOVER, fg="white",
                 font=("Segoe UI", 10, "bold"), width=4, pady=3).pack(side="left")

        tk.Label(hdr, text=data.get("descripcion", "Corredor"), bg="#111E37",
                 fg=TEXT_H, font=("Segoe UI", 11, "bold")).pack(side="left", padx=12)

        tk.Label(hdr, text=f"  {riesgo}  ", bg=color, fg="white",
                 font=("Segoe UI", 8, "bold"), padx=4, pady=3).pack(side="right")

        tk.Label(self, text=data.get("path", ""), bg="#111E37",
                 fg=TEXT_SUB, font=("Segoe UI", 9, "italic"),
                 wraplength=860, justify="left", anchor="w").pack(
            anchor="w", padx=14, pady=(0, 6))

        sf = tk.Frame(self, bg="#0D1627")
        sf.pack(fill="x")
        for lt, vl in [("Casos acumulados", data.get("casos", 0)),
                       ("Distancia (saltos)", data.get("distancia", 0))]:
            sub = tk.Frame(sf, bg="#0D1627")
            sub.pack(side="left", padx=18, pady=10)
            tk.Label(sub, text=lt, bg="#0D1627", fg=TEXT_SUB, font=F_SMALL).pack(anchor="w")
            tk.Label(sub,
                     text=f"{vl:,}".replace(",", ".") if isinstance(vl, int) else str(vl),
                     bg="#0D1627", fg=TEXT_H,
                     font=("Segoe UI", 13, "bold")).pack(anchor="w")

        if data.get("estrategia"):
            tk.Label(self, text=f"⚡  {data['estrategia']}",
                     bg="#111E37", fg=TEXT_B, font=F_SMALL,
                     wraplength=860, justify="left").pack(
                fill="x", padx=14, pady=(0, 10))
