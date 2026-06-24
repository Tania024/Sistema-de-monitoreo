"""
gui.py
Interfaz gráfica con Tkinter para el Sistema de Monitoreo Ambiental.
Muestra: estaciones, mediciones, alertas, estadísticas y métricas.
"""

import sys
import os
import platform
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime


# ── Paleta de colores ──────────────────────────────────────────────────────────
COLOR_BG       = "#1e1e2e"
COLOR_PANEL    = "#2a2a3d"
COLOR_ACCENT   = "#7c3aed"
COLOR_VERDE    = "#22c55e"
COLOR_ROJO     = "#ef4444"
COLOR_AMARILLO = "#f59e0b"
COLOR_TEXTO    = "#e2e8f0"
COLOR_SUBTEXTO = "#94a3b8"
COLOR_BORDE    = "#3f3f5a"


class InterfazMonitoreo:
    """
    Interfaz gráfica principal del sistema de monitoreo ambiental.
    La GUI corre en el proceso principal (hilo principal de Tkinter).
    Los controladores se ejecutan en hilos daemon para no bloquear la GUI.
    Todas las actualizaciones de widgets se hacen con root.after() para
    garantizar thread-safety (patrón seguro de Tkinter).
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(" Sistema de Monitoreo Ambiental — Cuenca")
        self.root.geometry("1280x820")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(True, True)

        # Estado
        self._ejecutando   = False
        self._resultado    = None
        self._resultados   = {}          # {modo: resultado}

        # Configuración de simulación
        self._num_estaciones = tk.IntVar(value=6)
        self._num_ciclos     = tk.IntVar(value=10)
        self._modo           = tk.StringVar(value="Secuencial")

        self._construir_ui()

    # ──────────────────────────────────────────────────────────────────────────
    # Construcción de la UI
    # ──────────────────────────────────────────────────────────────────────────

    def _construir_ui(self):
        # Barra superior
        self._barra_superior()
        # Marco principal con paneles
        contenedor = tk.Frame(self.root, bg=COLOR_BG)
        contenedor.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        contenedor.columnconfigure(0, weight=2)
        contenedor.columnconfigure(1, weight=3)
        contenedor.rowconfigure(0, weight=1)

        # Panel izquierdo
        izq = tk.Frame(contenedor, bg=COLOR_BG)
        izq.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self._panel_control(izq)
        self._panel_estaciones(izq)
        self._panel_entorno(izq)

        # Panel derecho
        der = tk.Frame(contenedor, bg=COLOR_BG)
        der.grid(row=0, column=1, sticky="nsew")
        self._panel_log(der)
        self._panel_estadisticas(der)
        self._panel_metricas(der)

    def _barra_superior(self):
        barra = tk.Frame(self.root, bg=COLOR_ACCENT, height=50)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        tk.Label(barra, text=" Sistema de Monitoreo Ambiental Urbano — Cuenca, Ecuador",
                 font=("Consolas", 14, "bold"), bg=COLOR_ACCENT, fg="white"
                 ).pack(side="left", padx=15, pady=10)

        self._lbl_tiempo = tk.Label(barra, text="⏱ 00:00:00",
                                    font=("Consolas", 12), bg=COLOR_ACCENT, fg="white")
        self._lbl_tiempo.pack(side="right", padx=15)

    def _panel_control(self, padre):
        frame = self._crear_panel(padre, "⚙ Control de Simulación")

        # Modo
        fila = tk.Frame(frame, bg=COLOR_PANEL)
        fila.pack(fill="x", padx=8, pady=4)
        tk.Label(fila, text="Modo:", bg=COLOR_PANEL, fg=COLOR_SUBTEXTO,
                 font=("Consolas", 10)).pack(side="left")
        for texto, val in [("Secuencial", "Secuencial"),
                           ("Hilos", "Hilos"),
                           ("Procesos", "Procesos"),
                           ("Todos", "Todos")]:
            tk.Radiobutton(fila, text=texto, variable=self._modo, value=val,
                           bg=COLOR_PANEL, fg=COLOR_TEXTO, selectcolor=COLOR_ACCENT,
                           activebackground=COLOR_PANEL, font=("Consolas", 10)
                           ).pack(side="left", padx=6)

        # Estaciones y ciclos
        fila2 = tk.Frame(frame, bg=COLOR_PANEL)
        fila2.pack(fill="x", padx=8, pady=4)

        tk.Label(fila2, text="Estaciones:", bg=COLOR_PANEL, fg=COLOR_SUBTEXTO,
                 font=("Consolas", 10)).pack(side="left")
        ttk.Spinbox(fila2, from_=4, to=12, textvariable=self._num_estaciones,
                    width=4, font=("Consolas", 10)).pack(side="left", padx=6)

        tk.Label(fila2, text="Ciclos:", bg=COLOR_PANEL, fg=COLOR_SUBTEXTO,
                 font=("Consolas", 10)).pack(side="left", padx=(10, 0))
        ttk.Spinbox(fila2, from_=10, to=30, textvariable=self._num_ciclos,
                    width=4, font=("Consolas", 10)).pack(side="left", padx=6)

        # Botones
        fila3 = tk.Frame(frame, bg=COLOR_PANEL)
        fila3.pack(fill="x", padx=8, pady=6)

        self._btn_iniciar = tk.Button(
            fila3, text="▶ INICIAR", command=self._iniciar,
            bg=COLOR_VERDE, fg="white", font=("Consolas", 11, "bold"),
            relief="flat", padx=14, cursor="hand2"
        )
        self._btn_iniciar.pack(side="left", padx=(0, 8))

        self._btn_limpiar = tk.Button(
            fila3, text="🗑 Limpiar", command=self._limpiar,
            bg=COLOR_PANEL, fg=COLOR_TEXTO, font=("Consolas", 10),
            relief="flat", padx=10, cursor="hand2",
            highlightbackground=COLOR_BORDE, highlightthickness=1
        )
        self._btn_limpiar.pack(side="left")

        self._lbl_estado = tk.Label(frame, text="● En espera",
                                    font=("Consolas", 10), bg=COLOR_PANEL,
                                    fg=COLOR_SUBTEXTO)
        self._lbl_estado.pack(anchor="w", padx=8, pady=(0, 6))

    def _panel_estaciones(self, padre):
        frame = self._crear_panel(padre, " Estado de Estaciones")
        frame.pack(fill="both", expand=True, pady=(5, 0))

        cols = ("ID", "Zona", "Estado", "Última medición")
        self._tree_est = ttk.Treeview(frame, columns=cols, show="headings",
                                      height=6)
        anchors = [40, 130, 90, 200]
        for col, ancho in zip(cols, anchors):
            self._tree_est.heading(col, text=col)
            self._tree_est.column(col, width=ancho, anchor="center")

        self._tree_est.pack(fill="both", expand=True, padx=6, pady=6)

        # Estilo de filas por estado
        self._tree_est.tag_configure("activa",    foreground=COLOR_VERDE)
        self._tree_est.tag_configure("esperando", foreground=COLOR_AMARILLO)
        self._tree_est.tag_configure("finalizada",foreground=COLOR_SUBTEXTO)
        self._tree_est.tag_configure("inactiva",  foreground=COLOR_SUBTEXTO)

    def _panel_entorno(self, padre):
        frame = self._crear_panel(padre, " Información del Entorno")

        try:
            import sys as _sys
            gil_info = "Activo (CPython)"
        except Exception:
            gil_info = "Desconocido"

        datos = [
            ("Python",    platform.python_version()),
            ("SO",        f"{platform.system()} {platform.release()}"),
            ("CPU cores", str(os.cpu_count())),
            ("GIL",       gil_info),
        ]
        for etiq, val in datos:
            fila = tk.Frame(frame, bg=COLOR_PANEL)
            fila.pack(fill="x", padx=8, pady=1)
            tk.Label(fila, text=f"{etiq}:", width=10, anchor="w",
                     bg=COLOR_PANEL, fg=COLOR_SUBTEXTO,
                     font=("Consolas", 9)).pack(side="left")
            tk.Label(fila, text=val, bg=COLOR_PANEL, fg=COLOR_TEXTO,
                     font=("Consolas", 9, "bold")).pack(side="left")

        tk.Frame(frame, bg=COLOR_PANEL, height=4).pack()

    def _panel_log(self, padre):
        frame = self._crear_panel(padre, " Registro de Mediciones y Alertas")
        frame.pack(fill="both", expand=True)

        self._txt_log = scrolledtext.ScrolledText(
            frame, bg="#0f0f1a", fg=COLOR_TEXTO,
            font=("Consolas", 9), wrap="word",
            insertbackground=COLOR_TEXTO, relief="flat"
        )
        self._txt_log.pack(fill="both", expand=True, padx=6, pady=6)
        self._txt_log.tag_config("alerta",  foreground=COLOR_ROJO)
        self._txt_log.tag_config("info",    foreground=COLOR_VERDE)
        self._txt_log.tag_config("sistema", foreground=COLOR_ACCENT)
        self._txt_log.tag_config("ciclo",   foreground=COLOR_AMARILLO)

    def _panel_estadisticas(self, padre):
        frame = self._crear_panel(padre, "Estadísticas por Variable")
        frame.pack(fill="x", pady=(5, 0))

        cols = ("Variable", "Promedio", "Máximo", "Mínimo", "Mediciones")
        self._tree_stats = ttk.Treeview(frame, columns=cols, show="headings", height=4)
        anchors = [90, 80, 80, 80, 90]
        for col, ancho in zip(cols, anchors):
            self._tree_stats.heading(col, text=col)
            self._tree_stats.column(col, width=ancho, anchor="center")
        self._tree_stats.pack(fill="x", padx=6, pady=6)

    def _panel_metricas(self, padre):
        frame = self._crear_panel(padre, " Métricas de Rendimiento")
        frame.pack(fill="x", pady=(5, 0))

        self._frame_metricas_contenido = tk.Frame(frame, bg=COLOR_PANEL)
        self._frame_metricas_contenido.pack(fill="x", padx=8, pady=6)

        self._lbl_metricas = {}
        claves = [
            ("modo",        "Modo"),
            ("tiempo",      "Tiempo total"),
            ("mediciones",  "Mediciones"),
            ("alertas",     "Alertas"),
            ("med_seg",     "Med./segundo"),
            ("zona_riesgo", "Zona riesgo"),
            ("aceleramiento","Aceleramiento"),
        ]
        for i, (key, etiq) in enumerate(claves):
            col_frame = tk.Frame(self._frame_metricas_contenido, bg=COLOR_PANEL)
            col_frame.grid(row=0, column=i, padx=10, sticky="w")
            tk.Label(col_frame, text=etiq, bg=COLOR_PANEL, fg=COLOR_SUBTEXTO,
                     font=("Consolas", 8)).pack(anchor="w")
            lbl = tk.Label(col_frame, text="—", bg=COLOR_PANEL, fg=COLOR_TEXTO,
                           font=("Consolas", 10, "bold"))
            lbl.pack(anchor="w")
            self._lbl_metricas[key] = lbl

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers UI
    # ──────────────────────────────────────────────────────────────────────────

    def _crear_panel(self, padre, titulo: str) -> tk.Frame:
        wrapper = tk.Frame(padre, bg=COLOR_BORDE, bd=1, relief="flat")
        wrapper.pack(fill="x", pady=3)

        tk.Label(wrapper, text=titulo, bg=COLOR_BORDE, fg=COLOR_SUBTEXTO,
                 font=("Consolas", 9, "bold")).pack(anchor="w", padx=8, pady=(4, 0))

        frame = tk.Frame(wrapper, bg=COLOR_PANEL)
        frame.pack(fill="both", expand=True, padx=1, pady=(0, 1))
        return frame

    def _log(self, texto: str, tag: str = "info"):
        def _hacer():
            self._txt_log.insert("end", f"{texto}\n", tag)
            self._txt_log.see("end")
        self.root.after(0, _hacer)

    def _actualizar_estado(self, texto: str):
        def _hacer():
            self._lbl_estado.config(text=f"● {texto}", fg=COLOR_AMARILLO)
        self.root.after(0, _hacer)

    def _actualizar_estacion_tree(self, est_id, zona, estado, ultima_med=""):
        def _hacer():
            for item in self._tree_est.get_children():
                vals = self._tree_est.item(item, "values")
                if str(vals[0]) == str(est_id):
                    self._tree_est.item(item, values=(est_id, zona, estado, ultima_med),
                                        tags=(estado,))
                    return
            self._tree_est.insert("", "end",
                                  values=(est_id, zona, estado, ultima_med),
                                  tags=(estado,))
        self.root.after(0, _hacer)

    def _actualizar_estadisticas(self, stats: dict):
        def _hacer():
            for item in self._tree_stats.get_children():
                self._tree_stats.delete(item)
            for var, datos in stats.items():
                self._tree_stats.insert("", "end", values=(
                    var,
                    f"{datos['promedio']:.2f}",
                    f"{datos['maximo']:.2f}",
                    f"{datos['minimo']:.2f}",
                    datos["cantidad"],
                ))
        self.root.after(0, _hacer)

    def _actualizar_metricas(self, resultado: dict, tiempo_sec: float = None):
        def _hacer():
            self._lbl_metricas["modo"].config(text=resultado.get("modo", "—"))
            self._lbl_metricas["tiempo"].config(
                text=f"{resultado.get('tiempo_total_s', 0):.3f} s"
            )
            self._lbl_metricas["mediciones"].config(
                text=str(resultado.get("total_mediciones", "—"))
            )
            self._lbl_metricas["alertas"].config(
                text=str(resultado.get("total_alertas", "—")),
                fg=COLOR_ROJO if resultado.get("total_alertas", 0) > 0 else COLOR_TEXTO
            )
            self._lbl_metricas["med_seg"].config(
                text=str(resultado.get("mediciones_por_segundo", "—"))
            )
            self._lbl_metricas["zona_riesgo"].config(
                text=resultado.get("zona_mayor_riesgo", "—")
            )
            # Aceleramiento respecto a secuencial
            if "Secuencial" in self._resultados and resultado.get("modo") != "Secuencial":
                ts  = self._resultados["Secuencial"]["tiempo_total_s"]
                tt  = resultado.get("tiempo_total_s", ts)
                acel = round(ts / max(tt, 0.001), 2)
                self._lbl_metricas["aceleramiento"].config(
                    text=f"×{acel}",
                    fg=COLOR_VERDE if acel >= 1.0 else COLOR_ROJO
                )
            else:
                self._lbl_metricas["aceleramiento"].config(text="base", fg=COLOR_SUBTEXTO)
        self.root.after(0, _hacer)

    # ──────────────────────────────────────────────────────────────────────────
    # Lógica de simulación
    # ──────────────────────────────────────────────────────────────────────────

    def _iniciar(self):
        if self._ejecutando:
            messagebox.showwarning("En ejecución", "Ya hay una simulación en curso.")
            return

        self._ejecutando = True
        self._btn_iniciar.config(state="disabled")
        self._limpiar_resultados()

        modo = self._modo.get()

        # Lanzar en hilo daemon para no bloquear Tkinter
        hilo = threading.Thread(target=self._correr_simulacion,
                                args=(modo,), daemon=True)
        hilo.start()
        self._cronometro()

    def _correr_simulacion(self, modo: str):
        num_est    = self._num_estaciones.get()
        num_ciclos = self._num_ciclos.get()

        modos = (["Secuencial", "Hilos", "Procesos"]
                 if modo == "Todos" else [modo])

        for m in modos:
            self._log(f"\n{'='*55}", "sistema")
            self._log(f"  MODO: {m.upper()}", "sistema")
            self._log(f"{'='*55}", "sistema")
            self._actualizar_estado(f"Ejecutando {m}...")
            self._inicializar_estaciones_tree(num_est, m)

            controlador = self._crear_controlador(
                m, num_est, num_ciclos
            )
            resultado = controlador.ejecutar()

            self._resultados[m] = resultado
            self._actualizar_estadisticas(resultado.get("estadisticas_variables", {}))
            self._actualizar_metricas(resultado)
            self._mostrar_resumen(resultado)

        self._finalizar()

    def _crear_controlador(self, modo: str, num_est: int, num_ciclos: int):
        kwargs = dict(
            num_estaciones=num_est,
            num_ciclos=num_ciclos,
            callback_medicion=self._on_medicion,
            callback_alerta=self._on_alerta,
            callback_estado=self._actualizar_estado,
        )
        if modo == "Secuencial":
            from versiones.version_secuencial import ControladorSecuencial
            return ControladorSecuencial(**kwargs)
        elif modo == "Hilos":
            from versiones.version_hilos import ControladorHilos
            return ControladorHilos(**kwargs)
        else:
            from versiones.version_procesos import ControladorProcesos
            return ControladorProcesos(**kwargs)

    def _on_medicion(self, medicion):
        from modelos.modelos import UNIDADES
        unidad = UNIDADES.get(medicion.variable, "")
        self._log(
            f"  [{medicion.timestamp.strftime('%H:%M:%S')}] "
            f"Est.{medicion.estacion_id} {medicion.zona[:12]:12} | "
            f"{medicion.variable:12} {medicion.valor:.2f} {unidad}",
            "info"
        )
        self._actualizar_estacion_tree(
            medicion.estacion_id, medicion.zona, "activa",
            f"{medicion.variable}: {medicion.valor:.2f} {unidad}"
        )

    def _on_alerta(self, alerta):
        self._log(f"  ⚠ ALERTA — {alerta}", "alerta")
        self._actualizar_estacion_tree(
            alerta.medicion.estacion_id,
            alerta.medicion.zona,
            "ALERTA",
            f"⚠ {alerta.medicion.variable}: {alerta.medicion.valor:.2f}"
        )

    def _mostrar_resumen(self, resultado: dict):
        self._log(f"\n  ✅ {resultado['modo']} COMPLETADO", "sistema")
        self._log(f"     Tiempo total:    {resultado['tiempo_total_s']} s", "sistema")
        self._log(f"     Mediciones:      {resultado['total_mediciones']}", "sistema")
        self._log(f"     Alertas:         {resultado['total_alertas']}", "sistema")
        self._log(f"     Med./segundo:    {resultado['mediciones_por_segundo']}", "sistema")
        self._log(f"     Zona de riesgo:  {resultado['zona_mayor_riesgo']}", "sistema")

        # Aceleramiento
        if "Secuencial" in self._resultados and resultado["modo"] != "Secuencial":
            ts   = self._resultados["Secuencial"]["tiempo_total_s"]
            tt   = resultado["tiempo_total_s"]
            acel = round(ts / max(tt, 0.001), 2)
            self._log(f"     Aceleramiento:   ×{acel} vs secuencial", "sistema")

    def _inicializar_estaciones_tree(self, num_est: int, modo: str):
        def _hacer():
            for item in self._tree_est.get_children():
                self._tree_est.delete(item)
        self.root.after(0, _hacer)

    def _finalizar(self):
        self._ejecutando = False

        def _hacer():
            self._btn_iniciar.config(state="normal")
            self._lbl_estado.config(text="● Simulación finalizada ✓", fg=COLOR_VERDE)
        self.root.after(0, _hacer)

        self._log("\n  ✅ Simulación completa.", "sistema")

        # Tabla comparativa si se ejecutaron los 3 modos
        if all(m in self._resultados for m in ["Secuencial", "Hilos", "Procesos"]):
            self._log("\n  TABLA COMPARATIVA", "ciclo")
            self._log(f"  {'Modo':<20} {'Tiempo(s)':<12} {'Med/s':<12} {'Alertas':<10} {'Aceler.'}", "ciclo")
            self._log("  " + "-"*62, "ciclo")
            ts = self._resultados["Secuencial"]["tiempo_total_s"]
            for m in ["Secuencial", "Hilos", "Procesos"]:
                r = self._resultados[m]
                acel = round(ts / max(r["tiempo_total_s"], 0.001), 2) if m != "Secuencial" else "—"
                self._log(
                    f"  {m:<20} {r['tiempo_total_s']:<12} "
                    f"{r['mediciones_por_segundo']:<12} {r['total_alertas']:<10} {acel}",
                    "ciclo"
                )

    def _limpiar(self):
        if self._ejecutando:
            return
        self._limpiar_resultados()

    def _limpiar_resultados(self):
        self._resultados = {}
        self._txt_log.delete("1.0", "end")
        for item in self._tree_est.get_children():
            self._tree_est.delete(item)
        for item in self._tree_stats.get_children():
            self._tree_stats.delete(item)
        for lbl in self._lbl_metricas.values():
            lbl.config(text="—", fg=COLOR_TEXTO)
        self._lbl_estado.config(text="● En espera", fg=COLOR_SUBTEXTO)

    def _cronometro(self):
        """Actualiza el reloj de la barra superior cada segundo."""
        if self._ejecutando:
            ahora = datetime.now().strftime("%H:%M:%S")
            self._lbl_tiempo.config(text=f"⏱ {ahora}")
            self.root.after(1000, self._cronometro)
        else:
            ahora = datetime.now().strftime("%H:%M:%S")
            self._lbl_tiempo.config(text=f"⏱ {ahora}")
