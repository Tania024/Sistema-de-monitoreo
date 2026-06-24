"""
version_procesos.py
Versión BASADA EN PROCESOS del sistema de monitoreo ambiental.

Mecanismos de comunicación/sincronización :
  1. multiprocessing.Queue → cada proceso estación envía mediciones al controlador
  2. multiprocessing.Pipe  → el controlador envía comandos (start/stop) a cada estación
"""

import time
import multiprocessing
from modelos.estacion import EstacionAmbiental
from modelos.analizador import AnalizadorDatos
from modelos.modelos import Medicion, UMBRALES, AlertaAmbiental


# ── Función ejecutada en cada proceso hijo ────────────────────────────────────
# DEBE estar a nivel de módulo (no dentro de clase) para poder ser serializada
# por multiprocessing (requisito del material del docente: requiere __main__)

def _proceso_estacion(estacion_id: int, zona: str, variables: list,
                      num_ciclos: int,
                      queue: multiprocessing.Queue,
                      pipe_conn):
    """
    Proceso hijo que representa una estación ambiental.

    Flujo:
      1. Espera comando 'start' del controlador via Pipe
      2. Genera mediciones y las envía por Queue
      3. Envía señal 'done' al finalizar
    """
    # Esperar comando de inicio por Pipe
    comando = pipe_conn.recv()
    if comando != "start":
        pipe_conn.close()
        return

    estacion = EstacionAmbiental(estacion_id=estacion_id, zona=zona, variables=variables)

    for ciclo in range(1, num_ciclos + 1):
        mediciones = estacion.generar_ciclo()
        for medicion in mediciones:
            # ── QUEUE: enviar medición al controlador ──────────────────────
            queue.put({
                "estacion_id": medicion.estacion_id,
                "zona":        medicion.zona,
                "variable":    medicion.variable,
                "valor":       medicion.valor,
                "timestamp":   medicion.timestamp,
                "ciclo":       ciclo,
            })

    # Señal de finalización
    queue.put({"sentinel": True, "estacion_id": estacion_id})
    pipe_conn.send("done")
    pipe_conn.close()


class ControladorProcesos:
    """
    Controlador basado en procesos.
    Cada estación corre en su propio multiprocessing.Process.
    El controlador recibe mediciones por Queue y envía comandos por Pipe.
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

        self.analizador   = AnalizadorDatos()
        self.mediciones   = []
        self.tiempo_total = 0.0

    # ── Ejecución ─────────────────────────────────────────────────────────────

    def ejecutar(self) -> dict:
        """
        Lanza un proceso por estación.
        Usa Queue para recibir mediciones y Pipe para enviar comandos.
        """
        inicio = time.time()

        if self.callback_estado:
            self.callback_estado("▶ Iniciando versión PROCESOS (Queue + Pipe)...")

        # ── Crear Queue compartida y Pipes ────────────────────────────────────
        queue    = multiprocessing.Queue()           # Mecanismo 1: Queue
        procesos = []
        pipes_padre = []

        for i in range(self.num_estaciones):
            # Mecanismo 2: Pipe — canal de comandos controlador → estación
            conn_padre, conn_hijo = multiprocessing.Pipe(duplex=True)
            pipes_padre.append(conn_padre)

            p = multiprocessing.Process(
                target=_proceso_estacion,
                name=f"Proceso-Estacion-{i+1}",
                args=(
                    i + 1,
                    self.ZONAS[i % len(self.ZONAS)],
                    self.VARIABLES_POR_ESTACION[i % len(self.VARIABLES_POR_ESTACION)],
                    self.num_ciclos,
                    queue,
                    conn_hijo,
                ),
            )
            procesos.append(p)

        # Iniciar todos los procesos
        for p in procesos:
            p.start()

        # ── Enviar comando 'start' a cada proceso via Pipe ────────────────────
        for conn in pipes_padre:
            conn.send("start")

        if self.callback_estado:
            self.callback_estado(
                f"[PIPE] Comandos 'start' enviados a {self.num_estaciones} procesos"
            )

        # ── Recibir mediciones desde la Queue hasta que todos terminen ────────
        finalizados = 0
        while finalizados < self.num_estaciones:
            item = queue.get()

            if item.get("sentinel"):
                finalizados += 1
                if self.callback_estado:
                    self.callback_estado(
                        f"[QUEUE] Proceso estación {item['estacion_id']} finalizado "
                        f"({finalizados}/{self.num_estaciones})"
                    )
                continue

            # Reconstruir objeto Medicion
            medicion = Medicion(
                estacion_id=item["estacion_id"],
                zona=item["zona"],
                variable=item["variable"],
                valor=item["valor"],
                timestamp=item["timestamp"],
            )
            self.mediciones.append(medicion)
            alerta = self.analizador.procesar_medicion(medicion)

            if self.callback_medicion:
                self.callback_medicion(medicion)
            if alerta and self.callback_alerta:
                self.callback_alerta(alerta)

        # ── Esperar que todos los procesos terminen ────────────────────────────
        for p in procesos:
            p.join()

        # Cerrar conexiones del padre
        for conn in pipes_padre:
            conn.close()

        self.tiempo_total = time.time() - inicio
        resultado = self._construir_resultado()

        if self.callback_fin:
            self.callback_fin(resultado)

        return resultado

    def _construir_resultado(self) -> dict:
        resumen = self.analizador.resumen()
        return {
            "modo":                    "Procesos (Queue + Pipe)",
            "num_estaciones":          self.num_estaciones,
            "num_ciclos":              self.num_ciclos,
            "tiempo_total_s":          round(self.tiempo_total, 4),
            "total_mediciones":        resumen["total_mediciones"],
            "total_alertas":           resumen["total_alertas"],
            "mediciones_por_segundo":  round(
                resumen["total_mediciones"] / max(self.tiempo_total, 0.001), 2
            ),
            "tiempo_promedio_ciclo_s": resumen["tiempo_promedio_ciclo_s"],
            "zona_mayor_riesgo":       self.analizador.zona_mayor_riesgo(self.mediciones),
            "estadisticas_variables":  resumen["estadisticas_variables"],
            "alertas":                 self.analizador.alertas,
            "mecanismos_comm":         ["multiprocessing.Queue", "multiprocessing.Pipe"],
        }
