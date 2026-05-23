import tkinter as tk
from tkinter import Canvas, Entry, messagebox

from ui.dashboard import dashboard
from ui.helpers import aplicar_icono, centrar
from ui.config import ANCHO, ALTO, COLOR_FONDO, COLOR_UNMASK, FUENTE_LABEL

ventana = None


def abrir_login():
    global ventana
    ventana.destroy()

    login = tk.Tk()
    aplicar_icono(login)
    login.title("Acceder a UNMASK")
    centrar(login, ANCHO, ALTO)

    canvas = Canvas(login, width=ANCHO, height=ALTO, highlightthickness=0)
    canvas.place(x=0, y=0)

    try:
        fondo = tk.PhotoImage(file="img/fondo_acceder.png")
        canvas.fondo_img = fondo
        canvas.create_image(0, 0, image=fondo, anchor="nw")
    except Exception:
        canvas.create_rectangle(0, 0, ANCHO, ALTO, fill=COLOR_FONDO)

    canvas.create_text(
        430, 220,
        text="Nombre de usuario (Usuario):",
        fill="#1E3A5F",
        font=FUENTE_LABEL,
        anchor="nw"
    )

    canvas.create_text(
        430, 320,
        text="Contraseña (1234):",
        fill="#1E3A5F",
        font=FUENTE_LABEL,
        anchor="nw"
    )

    canvas.create_rectangle(430, 250, 750, 300, fill="#ffffff", outline="")
    usuario_entry = Entry(login, width=25, font=("Segoe UI", 18), bd=0, bg="#ffffff")
    canvas.create_window(590, 275, window=usuario_entry)

    canvas.create_rectangle(430, 370, 750, 420, fill="#ffffff", outline="")
    password_entry = Entry(login, width=25, font=("Segoe UI", 18), bd=0, bg="#ffffff", show="*")
    canvas.create_window(590, 395, window=password_entry)

    usuarios_validos = {
        "Admin": "1234",
    }

    def validar_login():
        usuario = usuario_entry.get().strip()
        clave = password_entry.get().strip()

        if usuario in usuarios_validos and usuarios_validos[usuario] == clave:
            login.destroy()
            dashboard(usuario)
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

    try:
        boton_ingresar = tk.PhotoImage(file="img/boton_ingresar.png")
        canvas.boton_ingresar = boton_ingresar
        btn = canvas.create_image(600, 498, image=boton_ingresar)
        canvas.tag_bind(btn, "<Button-1>", lambda e: validar_login())
    except Exception as e:
        print("Error cargando botón:", e)
        tk.Button(login, text="Ingresar", command=validar_login).place(x=550, y=500, width=100, height=40)

    login.mainloop()


def ventana_bienvenida():
    global ventana
    ventana = tk.Tk()
    aplicar_icono(ventana)
    ventana.title("UNMASK")
    centrar(ventana, ANCHO, ALTO)

    canvas = Canvas(ventana, width=ANCHO, height=ALTO, highlightthickness=0)
    canvas.place(x=0, y=0)

    try:
        fondo = tk.PhotoImage(file="img/fondo_inicio.png")
        canvas.fondo_img = fondo
        canvas.create_image(0, 0, image=fondo, anchor="nw")
    except Exception:
        canvas.create_rectangle(0, 0, ANCHO, ALTO, fill=COLOR_FONDO)

    try:
        boton_img = tk.PhotoImage(file="img/boton_iniciar.png")
        canvas.boton_img = boton_img

        boton = canvas.create_image(ANCHO // 2, ALTO // 2 + 50, image=boton_img)
        canvas.tag_bind(boton, "<Button-1>", lambda e: abrir_login())
    except Exception:
        print("Error cargando botón.")
        tk.Button(ventana, text="Iniciar", command=abrir_login).place(x=ANCHO // 2 - 40, y=ALTO // 2 + 40, width=80, height=35)

    ventana.mainloop()


def splash_screen():
    splash = tk.Tk()
    splash.overrideredirect(True)
    centrar(splash, 600, 350)

    canvas = Canvas(splash, width=600, height=350, bg=COLOR_UNMASK, highlightthickness=0)
    canvas.pack()

    canvas.create_oval(-200, -150, 800, 500, fill=COLOR_UNMASK, outline="")

    try:
        logo = tk.PhotoImage(file="img/unmask.png")
        canvas.create_image(300, 170, image=logo)
        canvas.logo = logo
    except Exception:
        canvas.create_text(
            300, 170,
            text="UNMASK",
            fill="#1E3A5F",
            font=("Segoe UI", 60, "bold")
        )

    splash.after(2500, lambda: (splash.destroy(), ventana_bienvenida()))
    splash.mainloop()
