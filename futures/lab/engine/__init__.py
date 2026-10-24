"""
Motor de pruebas del laboratorio NQ.

Piezas (todas deterministas, ninguna usa IA):
  config     rutas, costos y reglas congeladas (lee los JSON del repo)
  data       carga de una sesión canónica en hora de Nueva York
  levels     niveles de referencia y umbrales en percentiles (solo pasado)
  sim        simulación de cada operación contra la cinta real, con costos
  rand       bot aleatorio emparejado (RAND)
  topstep    cuentas Topstep $50K que arrancan en fechas distintas
  stats      PSR, DSR, largo mínimo, permutaciones, CPCV, por año
  redteam    placebos y curva de costos
  registry   registro de estudios e intentos (solo agregar)
  report     hoja de resultados (curva, histogramas, drawdowns, calor, duraciones)
  signal_map fase 1: qué hace el precio después de cada señal
  run_test   línea de comandos que une todo y publica
"""
ENGINE_VERSION = "1.1.0"
