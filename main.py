"""
main.py
Punto de entrada del Sistema de Monitoreo Ambiental Urbano — Cuenca.

Estructura del proyecto:
  main.py
  modelos/
    modelos.py      ← Medicion, AlertaAmbiental, constantes
    estacion.py     ← EstacionAmbiental
    analizador.py   ← AnalizadorDatos
  versiones/
    version_secuencial.py  ← ControladorSecuencial
    version_hilos.py       ← ControladorHilos  (Lock + Barrier)
    version_procesos.py    ← ControladorProcesos (Queue + Pipe)
  gui/
    gui.py          ← InterfazMonitoreo (Tkinter)


"""

import sys
import os

# Asegurar que el directorio del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    import tkinter as tk
    from tkinter import ttk
    from gui.gui import InterfazMonitoreo

    # ── Estilo ttk ────────────────────────────────────────────────────────────
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure("Treeview",
                    background="#1a1a2e",
                    foreground="#e2e8f0",
                    rowheight=22,
                    fieldbackground="#1a1a2e",
                    font=("Consolas", 9))
    style.configure("Treeview.Heading",
                    background="#3f3f5a",
                    foreground="#e2e8f0",
                    font=("Consolas", 9, "bold"))
    style.map("Treeview", background=[("selected", "#7c3aed")])

    style.configure("TSpinbox",
                    fieldbackground="#2a2a3d",
                    foreground="#e2e8f0",
                    background="#2a2a3d")

    # ── Lanzar GUI ────────────────────────────────────────────────────────────
    app = InterfazMonitoreo(root)
    root.mainloop()


if __name__ == "__main__":
    # OBLIGATORIO para multiprocessing
    import multiprocessing
    multiprocessing.freeze_support()
    main()
