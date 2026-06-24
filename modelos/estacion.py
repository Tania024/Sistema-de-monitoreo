"""
estacion.py
Clase EstacionAmbiental — genera mediciones simuladas.
"""

import random
import time
from modelos.modelos import Medicion, RANGOS


class EstacionAmbiental:
    """
    Representa una estación de monitoreo ambiental.
    Genera mediciones simuladas para las variables asignadas.
    """

    VARIABLES_POR_DEFECTO = ["Temperatura", "Humedad", "Ruido", "CO2", "PM2.5", "PM10"]

    def __init__(self, estacion_id: int, zona: str, variables: list = None):
        self.estacion_id = estacion_id
        self.zona        = zona
        self.variables   = variables or self.VARIABLES_POR_DEFECTO[:3]
        self.estado      = "inactiva"       # inactiva | activa | procesando | finalizada

    # ── Generación de mediciones ─────────────────────────────────────────────

    def generar_medicion(self, variable: str) -> Medicion:
        """Genera una medición simulada para la variable indicada."""
        rango = RANGOS.get(variable, (0.0, 100.0))
        valor = round(random.uniform(*rango), 2)
        return Medicion(
            estacion_id=self.estacion_id,
            zona=self.zona,
            variable=variable,
            valor=valor,
        )

    def generar_ciclo(self) -> list:
        """Genera una medición por cada variable asignada (un ciclo completo)."""
        self.estado = "activa"
        mediciones = []
        for variable in self.variables:
            # Pequeña pausa para simular tiempo de lectura del sensor
            time.sleep(random.uniform(0.01, 0.05))
            mediciones.append(self.generar_medicion(variable))
        return mediciones

    def __repr__(self):
        return f"EstacionAmbiental(id={self.estacion_id}, zona='{self.zona}', estado='{self.estado}')"
