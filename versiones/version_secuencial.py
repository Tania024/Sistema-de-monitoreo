"""
version_secuencial.py
Versión SECUENCIAL del sistema de monitoreo ambiental.
Sirve como línea base para comparar rendimiento.
"""

import time
from modelos.estacion import EstacionAmbiental
from modelos.analizador import AnalizadorDatos
from modelos.modelos import UMBRALES


class ControladorSecuencial:
    """
    Controlador secuencial: ejecuta todas las estaciones
    una tras otra en el mismo hilo de ejecución.
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

        self.num_estaciones  = num_estaciones
        self.num_ciclos      = num_ciclos
        self.callback_medicion = callback_medicion
        self.callback_alerta   = callback_alerta
        self.callback_estado   = callback_estado
        self.callback_fin      = callback_fin

        self.estaciones  = self._crear_estaciones()
        self.analizador  = AnalizadorDatos()
        self.mediciones  = []
        self.tiempo_total = 0.0

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

    # ── Ejecución ─────────────────────────────────────────────────────────────

    def ejecutar(self) -> dict:
        """Ejecuta la simulación de forma completamente secuencial."""
        inicio = time.time()

        if self.callback_estado:
            self.callback_estado("▶ Iniciando versión SECUENCIAL...")

        for ciclo in range(1, self.num_ciclos + 1):
            inicio_ciclo = time.time()

            if self.callback_estado:
                self.callback_estado(f"Ciclo {ciclo}/{self.num_ciclos}")

            for estacion in self.estaciones:
                estacion.estado = "activa"
                if self.callback_estado:
                    self.callback_estado(
                        f"Ciclo {ciclo} | Estación {estacion.estacion_id} ({estacion.zona})"
                    )

                mediciones_ciclo = estacion.generar_ciclo()

                for medicion in mediciones_ciclo:
                    self.mediciones.append(medicion)
                    alerta = self.analizador.procesar_medicion(medicion)

                    if self.callback_medicion:
                        self.callback_medicion(medicion)
                    if alerta and self.callback_alerta:
                        self.callback_alerta(alerta)

                estacion.estado = "finalizada"

            fin_ciclo = time.time()
            self.analizador.registrar_tiempo_ciclo(fin_ciclo - inicio_ciclo)

        self.tiempo_total = time.time() - inicio

        resultado = self._construir_resultado()

        if self.callback_fin:
            self.callback_fin(resultado)

        return resultado

    def _construir_resultado(self) -> dict:
        resumen = self.analizador.resumen()
        return {
            "modo":                    "Secuencial",
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
        }
