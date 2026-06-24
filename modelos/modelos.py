"""
modelos.py
Clases de datos: Medicion y AlertaAmbiental
"""

from dataclasses import dataclass, field
from datetime import datetime


# ─── Umbrales por variable ────────────────────────────────────────────────────
UMBRALES = {
    "Temperatura": 25.0,   # °C
    "Humedad":     85.0,   # %
    "Ruido":       80.0,   # dB
    "CO2":        1000.0,  # ppm
    "PM2.5":       35.0,   # µg/m³
    "PM10":        50.0,   # µg/m³
}

# Rangos de generación simulada (min, max)
RANGOS = {
    "Temperatura": (10.0,  42.0),
    "Humedad":     (30.0,  95.0),
    "Ruido":       (40.0,  95.0),
    "CO2":        (400.0, 1500.0),
    "PM2.5":       ( 5.0,  60.0),
    "PM10":        (10.0,  80.0),
}

UNIDADES = {
    "Temperatura": "°C",
    "Humedad":     "%",
    "Ruido":       "dB",
    "CO2":         "ppm",
    "PM2.5":       "µg/m³",
    "PM10":        "µg/m³",
}


@dataclass
class Medicion:
    """Representa una lectura generada por una estación ambiental."""
    estacion_id: int
    zona:        str
    variable:    str
    valor:       float
    timestamp:   datetime = field(default_factory=datetime.now)

    def __repr__(self):
        unidad = UNIDADES.get(self.variable, "")
        return (f"[{self.timestamp.strftime('%H:%M:%S')}] "
                f"Estación {self.estacion_id} ({self.zona}) | "
                f"{self.variable}: {self.valor:.2f} {unidad}")

    def supera_umbral(self) -> bool:
        umbral = UMBRALES.get(self.variable, float("inf"))
        return self.valor > umbral


@dataclass
class AlertaAmbiental:
    """Alerta generada cuando una medición supera el umbral."""
    medicion:  Medicion
    umbral:    float
    timestamp: datetime = field(default_factory=datetime.now)

    def __repr__(self):
        unidad = UNIDADES.get(self.medicion.variable, "")
        return (f"⚠ ALERTA [{self.timestamp.strftime('%H:%M:%S')}] "
                f"Zona {self.medicion.zona} | "
                f"{self.medicion.variable}: {self.medicion.valor:.2f} {unidad} "
                f"(umbral: {self.umbral} {unidad})")
