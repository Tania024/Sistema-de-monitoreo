"""
analizador.py
Clase AnalizadorDatos — procesa mediciones y calcula estadísticas.
Incluye carga computacional deliberada (índice ambiental + media móvil)
para que tenga sentido comparar hilos vs procesos.
"""

import math
import time
from collections import defaultdict
from modelos.modelos import Medicion, AlertaAmbiental, UMBRALES


class AnalizadorDatos:
    """
    Procesa mediciones y calcula estadísticas globales.
    La función de análisis tiene carga CPU intencional para
    evidenciar la diferencia entre threading y multiprocessing.
    """

    def __init__(self):
        # Almacén de mediciones por variable
        self._datos: dict[str, list[float]] = defaultdict(list)
        self.alertas: list[AlertaAmbiental] = []
        self.total_mediciones: int = 0
        self.tiempos_ciclo: list[float] = []

    # ── Análisis principal ───────────────────────────────────────────────────

    def procesar_medicion(self, medicion: Medicion) -> AlertaAmbiental | None:
        """
        Procesa una medición individual.
        Retorna AlertaAmbiental si supera el umbral, o None.
        """
        self._datos[medicion.variable].append(medicion.valor)
        self.total_mediciones += 1

        # Carga computacional: calcular índice ambiental compuesto
        self._calcular_carga_cpu(medicion.valor)

        if medicion.supera_umbral():
            umbral = UMBRALES[medicion.variable]
            alerta = AlertaAmbiental(medicion=medicion, umbral=umbral)
            self.alertas.append(alerta)
            return alerta
        return None

    def _calcular_carga_cpu(self, valor: float):
        """
        Simula carga CPU real: calcula índice ambiental compuesto
        mediante operaciones matemáticas repetidas (media móvil + raíces).
        Esto permite evidenciar el impacto del GIL en hilos vs procesos.
        """
        acumulador = 0.0
        for i in range(1, 500):
            acumulador += math.sqrt(abs(valor * i)) / (i + 1)
            acumulador += math.log(abs(valor) + 1) * math.sin(i * 0.01)
        return acumulador

    def registrar_tiempo_ciclo(self, duracion: float):
        self.tiempos_ciclo.append(duracion)

    # ── Estadísticas ─────────────────────────────────────────────────────────

    def estadisticas(self) -> dict:
        """Calcula y retorna estadísticas completas."""
        stats = {}
        for variable, valores in self._datos.items():
            if valores:
                stats[variable] = {
                    "promedio": round(sum(valores) / len(valores), 2),
                    "maximo":   round(max(valores), 2),
                    "minimo":   round(min(valores), 2),
                    "cantidad": len(valores),
                }
        return stats

    def zona_mayor_riesgo(self, mediciones: list) -> str:
        """Determina la zona con más alertas generadas."""
        conteo = defaultdict(int)
        for alerta in self.alertas:
            conteo[alerta.medicion.zona] += 1
        if not conteo:
            return "Sin alertas"
        return max(conteo, key=conteo.get)

    def tiempo_promedio_ciclo(self) -> float:
        if not self.tiempos_ciclo:
            return 0.0
        return round(sum(self.tiempos_ciclo) / len(self.tiempos_ciclo), 4)

    def resumen(self) -> dict:
        return {
            "total_mediciones":        self.total_mediciones,
            "total_alertas":           len(self.alertas),
            "tiempo_promedio_ciclo_s": self.tiempo_promedio_ciclo(),
            "estadisticas_variables":  self.estadisticas(),
        }
