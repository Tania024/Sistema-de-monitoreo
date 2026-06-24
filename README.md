# 🌿 Sistema de Monitoreo Ambiental Urbano — Cuenca

Práctica de Cómputo Paralelo — Universidad Politécnica Salesiana  
Materia: Computación Paralela | Dr. Gabriel León Paredes

---

## Descripción

Simulación de un sistema urbano de monitoreo ambiental para la ciudad de Cuenca.  
Implementa **tres versiones** de ejecución concurrente:

| Versión | Módulo Python | Mecanismos |
|---------|--------------|------------|
| Secuencial | — | Línea base |
| Hilos | `threading` | `Lock` + `Barrier` |
| Procesos | `multiprocessing` | `Queue` + `Pipe` |

---

## Requisitos

- Python 3.10 o superior
- Tkinter (incluido con Python estándar)
- Sin dependencias externas adicionales

---

## Instalación y Ejecución

```bash
# Clonar o descomprimir el proyecto
cd monitoreo_ambiental

# Ejecutar
python main.py
```

---

## Estructura del Proyecto

```
monitoreo_ambiental/
├── main.py                        ← Punto de entrada
├── README.md
├── modelos/
│   ├── modelos.py                 ← Medicion, AlertaAmbiental, constantes
│   ├── estacion.py                ← EstacionAmbiental
│   └── analizador.py              ← AnalizadorDatos
├── versiones/
│   ├── version_secuencial.py      ← ControladorSecuencial
│   ├── version_hilos.py           ← ControladorHilos (Lock + Barrier)
│   └── version_procesos.py        ← ControladorProcesos (Queue + Pipe)
└── gui/
    └── gui.py                     ← InterfazMonitoreo (Tkinter)
```

---

## Variables Ambientales Monitoreadas

| Variable | Umbral de Alerta | Unidad |
|----------|-----------------|--------|
| Temperatura | 35.0 | °C |
| Humedad | 85.0 | % |
| Ruido | 80.0 | dB |
| CO₂ | 1000.0 | ppm |
| PM2.5 | 35.0 | µg/m³ |
| PM10 | 50.0 | µg/m³ |

---

## Estaciones Ambientales (Zonas de Cuenca)

1. Centro Histórico  
2. El Vergel  
3. Totoracocha  
4. Yanuncay  
5. Monay  
6. Ricaurte  

---

## Mecanismos de Sincronización

### Versión Hilos (`threading`)
- **`threading.Lock`**: protege el buffer compartido de mediciones. Solo un hilo puede escribir a la vez, evitando condiciones de carrera.
- **`threading.Barrier`**: sincroniza el fin de cada ciclo. Ninguna estación avanza al siguiente ciclo hasta que **todas** hayan terminado el actual.

### Versión Procesos (`multiprocessing`)
- **`multiprocessing.Queue`**: canal de comunicación principal. Cada proceso estación envía sus mediciones al controlador central.
- **`multiprocessing.Pipe`**: canal de comandos. El controlador envía `"start"` a cada proceso y recibe confirmación `"done"`.

---

## Métricas Calculadas

- Tiempo total de ejecución (Ts, Tthread, Tprocess)
- Mediciones procesadas por segundo
- Aceleramiento: `S = Ts / T`
- Promedio, máximo y mínimo por variable
- Total de alertas generadas
- Zona con mayor nivel de riesgo
- Tiempo promedio por ciclo

---

## Uso de la GUI

1. Seleccionar el **modo** (Secuencial / Hilos / Procesos / Todos)
2. Ajustar número de **estaciones** (4–12) y **ciclos** (10–30)
3. Presionar **▶ INICIAR**
4. Observar el registro en tiempo real, estadísticas y métricas
5. Al ejecutar **"Todos"**, se muestra tabla comparativa automática
