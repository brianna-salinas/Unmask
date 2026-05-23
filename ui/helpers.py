import tkinter as tk

from PIL import Image, ImageTk


def centrar(ventana, ancho, alto):
    ventana.update_idletasks()
    w = ventana.winfo_screenwidth()
    h = ventana.winfo_screenheight()
    x = (w // 2) - (ancho // 2)
    y = (h // 2) - (alto // 2)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


def aplicar_icono(ventana):
    try:
        icono = tk.PhotoImage(file="img/logo.png")
        ventana.iconphoto(False, icono)
        ventana.icono_lumi = icono
    except Exception as exc:
        print("No se pudo cargar el icono:", exc)
