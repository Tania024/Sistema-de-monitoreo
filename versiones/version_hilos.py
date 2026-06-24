"""
version_hilos.py
Versión BASADA EN HILOS del sistema de monitoreo ambiental.

Mecanismos de sincronización utilizados :
  1. threading.Lock   → protege el buffer compartido de mediciones y estadísticas
  2. threading.Barrier → espera a que TODAS las estaciones terminen un ciclo
                         antes de que el analizador calcule estadísticas
"""

import time
import threading
from modelos.estacion import EstacionAmbiental
from modelos.analizador import AnalizadorDatos


class HiloEstacion(threading.Thread):
    """
    Hilo dedicado a una estación ambiental.
    Genera mediciones por ciclo y las deposita en el buffer compartido.
    """

    def __init__(self, estacion: EstacionAmbiental, num_ciclos: int,
                 buffer: list, lock: threading.Lock,
                 barrier: threading.Barrier,
                 callback_medicion=None, callback_alerta=None,
                 callback_estado=None, analizador: AnalizadorDatos = None):

        super().__init__(name=f"Hilo-Estacion-{estacion.estacion_id}", daemon=True)
        self.estacion          = estacion
        self.num_ciclos        = num_ciclos
        self.buffer            = buffer           # recurso compartido
        self.lock              = lock             # Lock para proteger el buffer
        self.barrier           = barrier          # Barrier para sincronizar ciclos
        self.callback_medicion = callback_medicion
        self.callback_alerta   = callback_alerta
        self.callback_estado   = callback_estado
        self.analizador        = analizador

    def run(self):
        for ciclo in range(1, self.num_ciclos + 1):
            self.estacion.estado = "activa"

            if self.callback_estado:
                self.callback_estado(
                    f"[HILO] Ciclo {ciclo} | {self.estacion.zona} iniciando"
                )

            mediciones_ciclo = self.estacion.generar_ciclo()

            # ── LOCK: acceso exclusivo al buffer compartido ──────────────────
            self.lock.acquire()
            try:
                for medicion in mediciones_ciclo:
                    self.buffer.append(medicion)

                    # El analizador también se protege con el mismo lock
                    alerta = self.analizador.procesar_medicion(medicion)

                    if self.callback_medicion:
                        self.callback_medicion(medicion)
                    if alerta and self.callback_alerta:
                        self.callback_alerta(alerta)
            finally:
                self.lock.release()
            # ─────────────────────────────────────────────────────────────────

            self.estacion.estado = "esperando"

            # ── BARRIER: esperar a que TODAS las estaciones terminen el ciclo ─
            # Ninguna estación avanza al siguiente ciclo hasta que todas lleguen
            self.barrier.wait()
            # ─────────────────────────────────────────────────────────────────

        self.estacion.estado = "finalizada"


class ControladorHilos:
    """
    Controlador basado en hilos.
    Cada estación corre en su propio threading.Thread.
    """

    ZONAS = [
        "Centro Histórico",
        "El Vergel",
        "Totoracocha",
        "Yanuncay",
        "Monay",
        "Ricaurte",
    ]

    VARIABLES_POR_ESTACION = [
        ["Temperatura", "Humedad", "Ruido"],
        ["CO2", "PM2.5", "PM10"],
        ["Temperatura", "CO2", "Ruido"],
        ["Humedad", "PM2.5", "Temperatura"],
        ["Ruido", "CO2", "PM10"],
        ["Temperatura", "Humedad", "PM2.5"],
    ]

    def __init__(self, num_estaciones: int = 6, num_ciclos: int = 10,
                 callback_medicion=None, callback_alerta=None,
                 callback_estado=None, callback_fin=None):

        self.num_estaciones    = num_estaciones
        self.num_ciclos        = num_ciclos
        self.callback_medicion = callback_medicion
        self.callback_alerta   = callback_alerta
        self.callback_estado   = callback_estado
        self.callback_fin      = callback_fin

        self.estaciones   = self._crear_estaciones()
        self.analizador   = AnalizadorDatos()
        self.buffer       = []                          # buffer compartido
        self.lock         = threading.Lock()            # Mecanismo 1: Lock
        self.barrier      = threading.Barrier(          # Mecanismo 2: Barrier
            num_estaciones,
            action=self._accion_barrier                 # se ejecuta al romper la barrera
        )
        self.tiempo_total = 0.0
        self._ciclo_actual = 0

    def _crear_estaciones(self) -> list:
        estaciones = []
        for i in range(self.num_estaciones):
            est = EstacionAmbiental(
                estacion_id=i + 1,
                zona=self.ZONAS[i % len(self.ZONAS)],
                variables=self.VARIABLES_POR_ESTACION[i % len(self.VARIABLES_POR_ESTACION)],
            )
            estaciones.append(est)
        return estaciones

    def _accion_barrier(self):
        """
        Callback que se ejecuta automáticamente cuando todos los hilos
        llegan a la barrera (fin de ciclo). Registra el tiempo del ciclo.
        """
        self._ciclo_actual += 1
        if self.callback_estado:
            self.callback_estado(
                f"[BARRIER] Ciclo {self._ciclo_actual} completado — todas las estaciones sincronizadas"
            )

    # ── Ejecución ─────────────────────────────────────────────────────────────

    def ejecutar(self) -> dict:
        """Lanza un hilo por estación y espera a que todos terminen."""
        inicio = time.time()

        if self.callback_estado:
            self.callback_estado("▶ Iniciando versión HILOS (Lock + Barrier)...")

        hilos = []
        for estacion in self.estaciones:
            hilo = HiloEstacion(
                estacion=estacion,
                num_ciclos=self.num_ciclos,
                buffer=self.buffer,
                lock=self.lock,
                barrier=self.barrier,
                callback_medicion=self.callback_medicion,
                callback_alerta=self.callback_alerta,
                callback_estado=self.callback_estado,
                analizador=self.analizador,
            )
            hilos.append(hilo)

        # Iniciar todos los hilos
        for hilo in hilos:
            hilo.start()

        # Esperar a que todos los hilos finalicen
        for hilo in hilos:
            hilo.join()

        self.tiempo_total = time.time() - inicio
        resultado = self._construir_resultado()

        if self.callback_fin:
            self.callback_fin(resultado)

        return resultado

    def _construir_resultado(self) -> dict:
        resumen = self.analizador.resumen()
        return {
            "modo":                    "Hilos (Lock + Barrier)",
            "num_estaciones":          self.num_estaciones,
            "num_ciclos":              self.num_ciclos,
            "tiempo_total_s":          round(self.tiempo_total, 4),
            "total_mediciones":        resumen["total_mediciones"],
            "total_alertas":           resumen["total_alertas"],
            "mediciones_por_segundo":  round(
                resumen["total_mediciones"] / max(self.tiempo_total, 0.001), 2
            ),
            "tiempo_promedio_ciclo_s": resumen["tiempo_promedio_ciclo_s"],
            "zona_mayor_riesgo":       self.analizador.zona_mayor_riesgo(self.buffer),
            "estadisticas_variables":  resumen["estadisticas_variables"],
            "alertas":                 self.analizador.alertas,
            "mecanismos_sync":         ["threading.Lock", "threading.Barrier"],
        }
