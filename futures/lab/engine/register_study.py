"""Registra un estudio ANTES de correr sus intentos (protocol.json › pruebas_multiples).

  python -m engine.register_study tanda1
  python -m engine.register_study mapa_v1
"""
import sys
from . import registry, config

STUDIES = {
    "abp_v1": {
        "hypothesis": "ABP v1 (placebo de niveles de ABU v2, validación G1: el detector, filtro de día real, confirmación a 60 s, stop 12–32, objetivo 2R, salida a 15 min, 2 contratos y 09:30–15:30 de ABU v2, pero con todos los niveles —ayer, noche, POC/VAH/VAL del día— desplazados 40 ticks, + en fechas de ordinal par y − en impares): si la ventaja de ABU viene de dónde está el nivel, el placebo NO rinde más que un RAND emparejado y RAND2 (p vs RAND > 0.05) y su neto es <= 50% del de ABU v2 (+$11,912 en P031); si lo rinde, la ventaja no es del nivel y el progreso se rebaja.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABP v1"],
        "notes": "1 prueba + 16 de sensibilidad (cercanía 2/3/5/6 ticks, confirmación 40/50/70/80 s, umbral relativo p86/p88/p92/p94, desplazamiento 24/32/48/56 ticks). Una sola definición de placebo (docs/investigacion/placebo_abu.md) y lectura del resultado fijadas antes de correr. Humo: 100 sesiones, solo conteo (ABU v2 33 señales, ABP 33, solo 2 coinciden). Es una validación del criterio de nivel, no una estrategia: se espera no_pasa; un neto positivo y alto sería la señal de alarma. Mismos datos de diseño, NO es evidencia independiente.",
    },
    "opd_v1": {
        "hypothesis": "OPD v1 (apertura impulsiva por flujo: en los primeros 300 s desde las 09:30 el delta agresivo neto es >= 3 % del volumen en una dirección, el precio avanza >= 40 ticks en esa dirección y el mayor retroceso desde el extremo corrido es <= 1.0 x el avance; entrada a mercado a favor a las 09:35, stop en el contra-extremo de la ventana 12–32, objetivo 1.5R, salida a 15 min, 2 contratos, una operación por día): las operaciones rinden más que un RAND emparejado y RAND2 sorteados entre 09:34 y 09:38 con las mismas reglas; gana después de costos, es positiva en 2024, 2025 y 2026 y tiene al menos 100 operaciones.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["OPD v1"],
        "notes": "1 prueba + 16 de sensibilidad (ventana 240/360 s, delta 1/2/4/5 %, avance 30/50 ticks, retroceso 0.6/0.8/1.2/1.4; los pasos del motor son 60 s, 1 %, 10 ticks, 0.2). Una sola definición (docs/investigacion/apertura_impulsiva.md); umbrales fijados mirando solo la distribución de delta, avance y retroceso y el conteo de señales (~135 esperadas en 576 sesiones), sin ganancias. Definición más laxa que la de Dalton (retroceso 1.0), declarada. Antes se descartó PEX (extremo pobre) por tener solo 30–60 señales posibles. Exploratoria, NO es validación independiente. Pregunta única: ¿la iniciativa de apertura medida por delta continúa más que el azar?",
    },
    "abw_v1": {
        "hypothesis": "ABW v1 (absorción en días de apertura ancha: el detector de ABU, confirmado a 60 s, en niveles de ayer, de la noche, POC/VAH/VAL del día y máximo/mínimo de apertura, en los días en que el rango de 09:30–10:00 es >= 0.5 del rango de ayer, sin filtro de apertura dentro del valor; la ventana de absorción empieza después de las 10:00; entrada a mercado contra el lado absorbido, stop 12–32, objetivo 2R, salida a 15 min, 2 contratos, parada tras 2 pérdidas, 10:00–15:30): las operaciones rinden más que un RAND emparejado y RAND2 sorteados en la misma ventana y con las mismas reglas; gana después de costos, es positiva en 2024, 2025 y 2026 y tiene al menos 100 operaciones.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABW v1"],
        "notes": "1 prueba + 16 de sensibilidad (cercanía al nivel 2/3/5/6 ticks, confirmación 40/50/70/80 s, umbral relativo p86/p88/p92/p94, razón de apertura 0.3/0.4/0.6/0.7). Una sola definición (docs/investigacion/apertura_ancha.md); 0.5 fijado como número redondo mirando solo la distribución de la razón, sin ganancias. Humo: 112 sesiones, solo conteo (50 señales; ~257 esperadas). Exploratoria: mismo detector y datos que ABU, NO es evidencia independiente.",
    },
    "vpt_v1": {
        "hypothesis": "VPT v1 (pullback a la VWAP a favor de la tendencia: en días que abren FUERA del valor de ayer y no regresan a él, tras una extensión previa >= 24 ticks de la VWAP, cuando el precio toca la VWAP (<= 4 ticks) y en los 60 s siguientes el delta agresivo va a favor de la tendencia (>= 5 %) y el precio se aleja 4 ticks del extremo del pullback; entrada a mercado a favor, stop 12–32 detrás del extremo, objetivo 2R, salida a 15 min, 2 contratos, parada tras 2 pérdidas, 10:00–15:30): las operaciones rinden más que un RAND emparejado y RAND2 sorteados en la misma ventana y con las mismas reglas; gana después de costos, es positiva en 2024, 2025 y 2026 y tiene al menos 100 operaciones.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["VPT v1"],
        "notes": "1 prueba + 16 de sensibilidad (toque a la VWAP 2/3/5/6 ticks, extensión previa 16/20/28/32 ticks, delta 3/4/6/7 %, alejamiento 2/3/5/6 ticks). Una sola definición (docs/investigacion/vwap_tendencia.md) fijada antes de correr; solo se miró el conteo de señales en humo, ninguna ganancia. Primera prueba de continuación en días de tendencia con VWAP: ABT, ACC, VAR y ABB (días fuera del valor) no pasaron, pero ninguna usó la VWAP como soporte dinámico. Exploratoria, NO es validación independiente. Pregunta única: ¿en días que no regresan al valor de ayer, el pullback a la VWAP con delta a favor continúa más que el azar?",
    },
    "abb_v1": {
        "hypothesis": "ABB v1 (absorción tras re-entrada aceptada: el detector de ABU, confirmado a 60 s, en niveles de ayer, de la noche y POC/VAH/VAL del día, pero en los días que abren FUERA del valor de ayer y solo después de que el precio lleva 600 s seguidos dentro del valor de ayer; entrada a mercado contra el lado absorbido, stop 12–32, objetivo 2R, salida a 15 min, 2 contratos, parada tras 2 pérdidas, 09:30–15:30): las operaciones rinden más que un RAND emparejado y RAND2 sorteados en la misma ventana y con las mismas reglas; gana después de costos, es positiva en 2024, 2025 y 2026 y tiene al menos 100 operaciones.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABB v1"],
        "notes": "1 prueba + 16 de sensibilidad (cercanía al nivel 2/3/5/6 ticks, confirmación 40/50/70/80 s, umbral relativo p86/p88/p92/p94, aceptación 300/450/750/900 s). Una sola definición (docs/investigacion/absorcion_reentrada.md); 600 s elegido por conteo de señales (1,800 s daba ~70 operaciones esperadas), sin mirar ganancias. Exploratoria: mismo detector y datos que ABU, NO es evidencia independiente. Pregunta única: ¿la absorción de ABU también revierte en días que abren fuera del valor una vez aceptado el valor de ayer?",
    },
    "abm_v1": {
        "hypothesis": "ABM v1 (absorción en el valor multi-día: el detector de ABU, confirmado a 60 s, en los niveles del perfil compuesto de los 5 días válidos anteriores (POC, VAH, VAL al 70%, máximo, mínimo) y los POC desnudos de esos días, descartando los niveles a <= 8 ticks de un nivel de ayer o de la noche; solo días cuya apertura de las 09:30 cae dentro del valor compuesto; entrada a mercado contra el lado absorbido, stop 12–32, objetivo 2R, salida a 15 min, 2 contratos, parada tras 2 pérdidas, 09:30–15:30): las operaciones rinden más que un RAND emparejado y RAND2 sorteados en la misma ventana y con las mismas reglas; gana después de costos, es positiva en 2024, 2025 y 2026 y tiene al menos 100 operaciones.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABM v1"],
        "notes": "1 prueba + 16 de sensibilidad (cercanía al nivel 2/3/5/6 ticks, confirmación 40/50/70/80 s, umbral relativo p86/p88/p92/p94, días del compuesto 1/3/7/9). Una sola definición (docs/investigacion/absorcion_multidia.md); 5 días fijado por ser una semana de trading, no por resultados. Humo: 120 sesiones, solo conteo de señales (21; ~100 esperadas en 576). Exploratoria: mismo detector y datos que ABU, NO es evidencia independiente. Riesgo: cerca del mínimo de 100 operaciones ('insuficiente' posible). Pregunta única: ¿los niveles de varios días dan absorciones que revierten donde ABU no mira?",
    },
    "abu_v3": {
        "hypothesis": "ABU v3 (las señales de ABU v2: detector de absorción unificada en niveles de ayer, de la noche y POC/VAH/VAL del día, solo días que abren dentro del valor de ayer, confirmado a 60 s, entrada a mercado contra el lado absorbido, stop 12–32, objetivo 2R, salida a 15 min, 2 contratos, 09:30–15:30; ÚNICO cambio: el día se detiene tras 2 pérdidas seguidas en vez de 3, de modo que el peor día queda en ≈ $660 y no en ≈ $1,000 = límite diario de Topstep): las operaciones rinden más que un RAND emparejado y RAND2 sorteados en la misma ventana y con las mismas reglas; gana después de costos, es positiva en 2024, 2025 y 2026, tiene al menos 100 operaciones y rompe el MLL de Topstep en menos cuentas que ABU v2 (P031: 214 de 517).",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABU v3"],
        "notes": "1 prueba + 16 de sensibilidad (cercanía al nivel, confirmación, umbral relativo y objetivo R, las mismas cuatro perillas de ABU v1/v2). Una sola definición de riesgo (docs/investigacion/riesgo_diario.md): el 2 sale del cálculo con el límite diario de la cuenta, no se probaron otros valores. Exploratoria: mismas señales y datos que ABU v1/v2, NO es evidencia independiente ni nueva de ventaja; solo mide si el cuello de Topstep era el riesgo diario. Última versión de ABU. Pregunta única: ¿limitar a 2 pérdidas seguidas baja las cuentas que rompen el MLL sin matar la ganancia?",
    },
    "abe_v1": {
        "hypothesis": "ABE v1 (absorción de ABU v1 confirmada por ES: el detector de absorción de ABU v1 en niveles de ayer, de la noche y POC/VAH/VAL del día, solo días que abren dentro del valor de ayer, confirmado a 60 s, se opera solo si en los 120 s que terminan en la confirmación ES no avanzó más de 2 ticks en la dirección del flujo absorbido, con al menos 20 llenados de ES; entrada a mercado contra el lado absorbido, stop 12–32, objetivo 2R, salida a 15 min, 1 contrato, 09:30–15:30): las operaciones rinden más que un RAND emparejado y RAND2 sorteados en la misma ventana; gana después de costos, es positiva en 2024, 2025 y 2026 y tiene al menos 100 operaciones.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABE v1"],
        "notes": "1 prueba + 16 de sensibilidad (avance de ES 0/1/3/4 ticks, ventana de ES 90/150/60/180 s, objetivo 1/1.5/2.5/3 R, confirmación 30/45/75/90 s). Una sola definición (docs/investigacion/absorcion_es.md); el escenario espejo (ES avanzó) no se corre. Humo: 120 sesiones, solo conteo de señales (ABU 43, ABE 24; ~115 esperadas). Exploratoria: mismas señales que ABU, NO es evidencia independiente. Riesgo: cerca del mínimo de 100 operaciones. Pregunta única: ¿que ES también se detenga separa las absorciones que revierten?",
    },
    "abr_v1": {
        "hypothesis": "ABR v1 (absorción con reprueba: el detector de ABU v1 en niveles de ayer, de la noche y POC/VAH/VAL del día, solo días que abren dentro del valor de ayer, confirmado a 60 s; en vez de entrar a mercado se deja una orden límite 2 ticks dentro del extremo absorbido, válida 300 s; stop 8 ticks desde el llenado, objetivo 2R, salida a 15 min, 1 contrato, 09:30–15:30): las operaciones que se llenan rinden más que un RAND emparejado y RAND2 sorteados en la misma ventana; gana después de costos, es positiva en 2024, 2025 y 2026 y tiene al menos 100 operaciones.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABR v1"],
        "notes": "1 prueba + 16 de sensibilidad (distancia de la orden 0/1/3/4 ticks, stop 4/6/10/12, objetivo 1/1.5/2.5/3 R, espera 180/240/360/420 s). Una sola definición (docs/investigacion/absorcion_reprueba.md). Humo: 120 sesiones, 57 señales, 28 llenados; se vio el neto de esas 120 sesiones (ruido, 28 operaciones) pero no se ajustó nada. Exploratoria: mismas señales que ABU, NO es evidencia independiente. Riesgo: ~130 operaciones, cerca del mínimo de 100. Pregunta única: ¿entrar pasivamente en la reprueba del extremo absorbido mejora a la entrada a mercado de ABU?",
    },
    "abf_v1": {
        "hypothesis": "ABF v1 (absorción fallida: el detector de absorción de ABU v1 en niveles de ayer, de la noche y POC/VAH/VAL del día, confirmado a 60 s; si en 300 s el precio rompe el extremo absorbido >= 4 ticks con delta de 30 s a favor del lado que agredía, entrada a mercado EN LA DIRECCIÓN de la ruptura, stop 16 ticks, objetivo 2R, salida a 15 min, 1 contrato, 09:30–15:30, todos los días, con guarda de cotización congelada): el precio sigue la ruptura más de lo que lo hace un RAND emparejado y RAND2 sorteados en la misma ventana; gana después de costos, es positiva en 2024, 2025 y 2026 y tiene al menos 100 operaciones.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABF v1"],
        "notes": "1 prueba + 16 de sensibilidad (ruptura 2/3/5/6 ticks, ventana de fallo 180/240/360/420 s, stop 8/12/20/24, objetivo 1/1.5/2.5/3 R). Una sola definición (docs/investigacion/absorcion_fallida.md). Humo: solo señales (9 en 20 sesiones). Exploratoria: sale de ver que ABU pierde el 60% con el stop y que los reversos sin nivel pierden con p~1; NO es evidencia independiente. Pregunta única: ¿una absorción que falla en un nivel produce continuación?",
    },
    "faf_v1": {
        "hypothesis": "FAF v1 (subasta fallida: una celda de 10 s cruza VAH/máximo de ayer/máximo de la noche (o VAL/mínimos) ≥ 2 ticks con flujo agresivo del lado de la salida en 60 s ≥ 0.5 × p95, y en 120 s el precio vuelve al nivel con delta de 30 s contrario; entrada a mercado contra la salida, stop 4 ticks más allá del extremo (12–32), objetivo 2R, salida a 15 min, 1 contrato, 09:30–15:30, un intento por nivel y día): el precio se aleja del lado que falló más de lo que lo hace un RAND emparejado y RAND2 sorteados en la misma ventana; gana después de costos, es positiva en 2024, 2025 y 2026 y tiene al menos 100 operaciones.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["FAF v1"],
        "notes": "1 prueba + 16 de sensibilidad (penetración 0/1/3/4 ticks, ventana de fallo 60/90/150/180 s, stop máximo 24/28/36/40, objetivo 1/1.5/2.5/3 R). Una sola definición (docs/investigacion/subasta_fallida.md). Filtro 'abre dentro del valor' descartado por conteo de señales (~0.12/día) y no por ganancias. Humo: solo señales en 40 días. Exploratoria: no es evidencia independiente. Pregunta única: ¿el intento fallido de salir de un nivel clave con flujo agresivo aleja el precio más que el azar emparejado?",
    },
    "dvg_v1": {
        "hypothesis": "DVG v1 (divergencia de delta acumulado en el extremo del día: nuevo máximo de la sesión con menos delta acumulado que el máximo anterior, marcado hace ≥ 2 min y con retroceso intermedio ≥ 10 ticks, y espejo para mínimos; confirmación: el precio se aleja 3 ticks del extremo en 30 s; entrada a mercado en contra, stop 3 ticks más allá (8–24), objetivo 2R, salida a 5 min, hasta 8 operaciones por día, 09:30–15:30, no antes de 10 min de sesión, 1 contrato): el precio se aleja del extremo agotado más de lo que lo hace un RAND emparejado y RAND2 sorteados en la misma ventana; gana después de costos, es positiva en 2024, 2025 y 2026 y tiene al menos 100 operaciones.",
        "n_declared": 1 + 12,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["DVG v1"],
        "notes": "1 prueba + 12 de sensibilidad (retroceso 6/8/12/14 ticks, alejamiento 1/2/4/5 ticks, objetivo 1/1.5/2.5/3 R). Definición fijada antes de correr (docs/investigacion/divergencia_delta.md) a partir de la regla común de CVD (precio máximo más alto, delta máximo más bajo); no se compararon otras definiciones (pivotes, delta por vela). Humo: solo señales en 3 días (4, 5 y 3), nunca ganancias. Exploratoria: sale de ver que solo la familia de absorción funciona y que depende de niveles de ayer; NO es evidencia independiente. Pregunta única: ¿el agotamiento de delta en el extremo del propio día, que ocurre ~4 veces al día, aleja el precio más que el azar emparejado?",
    },
    "abq_v1": {
        "hypothesis": "ABQ v1 (el detector de absorción de ABU v1 a escala de scalping: ventana de flujo agresivo de 30 s con umbral relativo p90 de la hora anterior, confirmación a 20 s, stop 8–20 ticks, objetivo 2R, salida a 5 min, hasta 12 operaciones por día; mismos niveles de ayer, de la noche y POC/VAH/VAL del día, solo días que abren dentro del valor de ayer, 09:30–15:30, 1 contrato): el precio se aleja del lado absorbido más de lo que lo hace un RAND emparejado y RAND2 sorteados en la misma ventana; gana después de costos, es positiva en 2024, 2025 y 2026 y tiene al menos 100 operaciones.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABQ v1"],
        "notes": "1 prueba + 16 de sensibilidad de señal (cercanía 2/3/5/6 ticks, confirmación 10/15/25/30 s, percentil relativo 86/88/92/94, objetivo 1/1.5/2.5/3 R). Definición fijada antes de correr (docs/investigacion/absorcion_rapida.md); una sola escala (30 s), no se compararon otras como candidatas. Solo se contaron señales (80 sesiones consecutivas: ABQ 32, ABU 33), nunca ganancias. Exploratoria: sale de ver que ABU (P030/P031) es la única con ventaja; NO es evidencia independiente ni resuelve la frecuencia (misma cantidad de señales). Pregunta única: ¿la ventaja de ABU sobrevive a una escala de segundos-minutos con menos riesgo por operación?",
    },
    "abt_v1": {
        "hypothesis": "ABT v1 (absorción de flujo agresivo A FAVOR de la tendencia, solo en días que abren FUERA del valor de ayer: si abre sobre el VAH solo se compra la venta agresiva absorbida, si abre bajo el VAL solo se vende la compra agresiva absorbida; niveles de ayer, de la noche y POC/VAH/VAL del perfil en desarrollo; detector, confirmación a 60 s, stop 12–32, objetivo 2R y salida a 15 min de ABU v1; 1 contrato): el precio se aleja del lado absorbido más de lo que lo hace un RAND emparejado y RAND2 sorteados en la misma ventana; gana después de costos, es positiva en 2024, 2025 y 2026 y tiene al menos 100 operaciones.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABT v1"],
        "notes": "1 prueba + 16 de sensibilidad de señal (cercanía 2/3/5/6 ticks, confirmación 40/50/70/80 s, percentil relativo 86/88/92/94, objetivo 1/1.5/2.5/3 R). Definición fijada antes de correr (docs/investigacion/absorcion_tendencia.md); solo se contaron señales (56 sesiones: 16, unas 165 en todo el periodo), nunca ganancias de esta regla. Los días son los complementarios de ABU/ABD (abren dentro del valor): no hay solapamiento de operaciones. Es exploratoria: la idea sale de ver que la familia de absorción solo ganó en días de balance; esta es la pregunta espejo. Un solo 'sesgo' (lado de la apertura contra el valor de ayer): no se compararon definiciones alternativas de tendencia.",
    },
    "abu_v2": {
        "hypothesis": "ABU v2 (las mismas señales de ABU v1 —absorción de flujo agresivo en niveles de ayer y de la noche y en POC/VAH/VAL del día, solo días que abren dentro del valor de ayer, stop 12–32, objetivo 2R, salida a 15 min— con 2 contratos por operación): conserva la ventaja contra RAND y RAND2 sorteados en la misma ventana y con el mismo tamaño; gana después de costos, es positiva en 2024, 2025 y 2026, tiene al menos 100 operaciones y pasa Topstep en más del 50% de los arranques sin romper el MLL en más del 50%.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABU v2"],
        "notes": "1 prueba + 16 de sensibilidad de señal (las mismas de ABU v1: cercanía 2/3/5/6 ticks, confirmación 40/50/70/80 s, percentil relativo 86/88/92/94, objetivo 1/1.5/2.5/3 R), todas con 2 contratos. El tamaño (2) se fijó por el límite diario de Topstep (3 pérdidas al stop máximo ≈ $1,000), no por resultados; no se probó otro tamaño como candidata. NO es evidencia nueva de ventaja ni validación independiente: mismas señales y mismos datos de diseño que P030. Pregunta única: ¿el cuello de Topstep (9.9%, 0 MLL rotos) era el tamaño? Ver docs/investigacion/tamano_posicion.md.",
    },
    "abu_v1": {
        "hypothesis": "ABU v1 (absorción de flujo agresivo en los niveles de ayer y de la noche y en POC/VAH/VAL del perfil en desarrollo, solo en días que abren dentro del valor de ayer, entradas 09:30–15:30; detector, umbral relativo, confirmación a 60 s, stop 12–32, objetivo 2R y salida a 15 min de ABD v1): el precio se aleja del lado absorbido más de lo que lo hace un RAND emparejado y RAND2 sorteados en la misma ventana; la estrategia gana después de costos, es positiva en 2024, 2025 y 2026, tiene al menos 100 operaciones y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABU v1"],
        "notes": "1 prueba + 16 de sensibilidad (cercanía 2/3/5/6 ticks, confirmación 40/50/70/80 s, percentil relativo 86/88/92/94, objetivo 1/1.5/2.5/3 R). Definición fijada antes de correr (docs/investigacion/absorcion_unificada.md); solo se contaron señales (58 sesiones: ABD 9, ABU 20). Une los niveles de ABD (P027: +$5,720, 111 operaciones, Topstep 0% sin resolver) con el valor en desarrollo de ABI/ABV. Elegida mirando P021/P022/P027 por régimen en los mismos datos de diseño: exploratoria, el DSR la penaliza. Ataca el problema de frecuencia de Topstep.",
    },
    "imb_v1": {
        "hypothesis": "IMB v1 (desequilibrios diagonales apilados): cuando en 60 s hay 3 o más precios seguidos con desequilibrio agresivo diagonal >= 3:1 y >= 10 contratos, y el precio se aleja >= 4 ticks de la zona, una orden límite en el borde cercano de la zona (300 s) gana más de lo que lo hace un RAND emparejado y RAND2 sorteados en la misma ventana (10:00-15:30); la estrategia gana después de costos, es positiva en 2024, 2025 y 2026, tiene al menos 100 operaciones y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["IMB v1"],
        "notes": "1 prueba + 16 de sensibilidad (razon 2/2.5/3.5/4, volumen minimo 6/8/12/14, alejamiento 2/3/5/6 ticks, salida 5/10/20/25 min). Definicion de la literatura de footprint fijada antes de correr (docs/investigacion/desequilibrios_apilados.md); pila minima 3 y ratio 3:1 son el estandar de las fuentes. Solo se corrio el codigo en 60 sesiones para ver que produce operaciones (301); sin ajustes. Sin filtro de regimen. Familia nueva con alta frecuencia.",
    },
    "vbr_v1": {
        "hypothesis": "VBR v1 (reversión a la VWAP desde la banda de 2σ, solo en días que abren dentro del valor de ayer): cuando el precio toca VWAP ± 2σ (ponderada por volumen, desde las 09:30) y en los 60 s siguientes el delta agresivo cambia de signo y el precio se aleja 4 ticks del extremo, vuelve hacia la VWAP más de lo que lo hace un RAND emparejado y RAND2 sorteados en la misma ventana (10:00–15:30); la estrategia gana después de costos, es positiva en 2024, 2025 y 2026, tiene al menos 100 operaciones y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["VBR v1"],
        "notes": "1 prueba + 16 de sensibilidad (k 1.5/1.75/2.25/2.5 σ, alejamiento 2/3/5/6 ticks, salida 10/15/25/30 min, piso de σ 6/8/12/14 ticks). Definición fijada antes de correr (docs/investigacion/vwap_bandas.md). Solo se corrió el código en 60 sesiones para ver que produce señales (73 operaciones); sin ajustes. El filtro de apertura dentro del valor sale de ver P012/P016/P017/P027 por régimen en los mismos datos de diseño: exploratorio, el DSR lo penaliza. Estrategia nueva con más señales que la familia de absorción (ataca el problema de frecuencia de Topstep).",
    },
    "abd_v1": {
        "hypothesis": "ABD v1 (absorción de flujo agresivo en los niveles de ayer y de la noche, solo en días que abren dentro del valor de ayer, entradas 09:30–15:30, umbral = menor entre p95 de 20 sesiones y p90 de la hora anterior; detector, confirmación a 60 s, stop 12–32, objetivo 2R y salida a 15 min de ABS v1): el precio se aleja del lado absorbido más de lo que lo hace un RAND emparejado y RAND2 sorteados en la misma ventana; la estrategia gana después de costos, es positiva en 2024, 2025 y 2026, tiene al menos 100 operaciones y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABD v1"],
        "notes": "1 prueba + 16 de sensibilidad (cercanía 2/3/5/6 ticks, confirmación 40/50/70/80 s, percentil relativo 86/88/92/94, objetivo 1/1.5/2.5/3 R). Definición fijada antes de correr (docs/investigacion/absorcion_dias_balance.md); solo se contaron señales (p95: 70, p90: 115, p85: 137; se eligió p90 por superar 100). El filtro de apertura dentro del valor sale de ver P012/P014 por tipo de apertura en los mismos datos de diseño: exploratorio, el DSR lo penaliza.",
    },
    "abi_v2": {
        "hypothesis": "ABI v2 (misma absorción en los niveles del propio día que ABI v1, pero en la tarde de Nueva York, entradas 11:30–15:30, cierre 15:45, umbral de volumen p95 de la hora anterior): el precio se aleja del lado absorbido más de lo que lo hace un RAND emparejado y RAND2 sorteados en la misma ventana; la estrategia gana después de costos, es positiva en 2024, 2025 y 2026, tiene al menos 100 operaciones y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABI v2"],
        "notes": "1 prueba + 16 de sensibilidad (cercanía 2/3/5/6 ticks, confirmación 40/50/70/80 s, percentil relativo 91/93/97/99, salida 5/10/20/25 min). Definición fijada antes de correr (docs/investigacion/ventana_tarde.md). Solo se contaron señales (≈35 en 143 sesiones con p95, ≈47 con p90); ninguna ganancia. La idea parte de P021 (ABI v1, diseño): exploratorio, el DSR lo penaliza. Operaciones de la tarde, distintas de las de P021.",
    },
    "lvn_v1": {
        "hypothesis": "LVN v1 (travesía de un vacío de volumen del perfil NY de ayer: cubos de 8 ticks, cubo fino ≤ percentil 20, vacío ≥ 16 ticks): cuando el precio cruza por primera vez un vacío con delta agresivo de los últimos 60 s a favor ≥ 10 % del volumen, sigue hasta el borde lejano del vacío más de lo que lo hace un RAND emparejado y RAND2; la estrategia gana después de costos, es positiva en 2024, 2025 y 2026, tiene al menos 100 operaciones y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["LVN v1"],
        "notes": "1 prueba + 16 de sensibilidad (delta 5/10/15/20 %, ancho mínimo 8/12/20/24 ticks, stop detrás 2/6/8 ticks (0 se omite), salida 5/10/20/25 min). Definición fijada antes de correr (docs/investigacion/lvn.md); solo se contó el número de señales (~370 en 576 sesiones), ninguna ganancia. Estrategia nueva, primera prueba de LVN. Asia/Londres no es posible: rand.py solo carga la ventana de Nueva York.",
    },
    "abk_v1": {
        "hypothesis": "ABK v1 (absorción medida con el libro, no solo con el precio): cuando entra ≥ p95 de flujo agresivo de un lado en 60 s, la mejor oferta contraria no retrocede y se repone (tamaño final ≥ 50%), y a los 60 s el delta cambia de signo y el precio se aleja 4 ticks, el precio se aleja del lado absorbido más de lo que lo hace un RAND emparejado y RAND2; la estrategia gana después de costos, es positiva en 2024, 2025 y 2026, tiene al menos 100 operaciones y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABK v1"],
        "notes": "1 prueba + 16 de sensibilidad (reposición 0/25/75/100%, confirmación 40/50/70/80 s, stop mínimo 4/8/16/20, salida 5/10/20/25 min; la reposición 0% es la definición alternativa 'solo aguanta'). Definición fijada antes de correr (docs/investigacion/absorcion_libro.md); solo se contaron señales (~850). Sin filtro de nivel. Salida a 15 min y confirmación vienen de P012 (diseño): exploratorio, el DSR lo penaliza.",
    },
    "hvf_v1": {
        "hypothesis": "HVF v1 (E-HVN-FUERZA, pedido de Oscar): la absorción de flujo agresivo (mismo detector que ABS, confirmación a 60 s, salida a 15 min) en un HVN poderoso del perfil de ayer (grupo de precios ≥ p95 de volumen cuyo pico está a ≤ 8 puntos del POC/VAH/VAL de ayer) hace que el precio se aleje del lado absorbido más que un RAND emparejado y RAND2; la estrategia gana después de costos, es positiva en 2024, 2025 y 2026, tiene al menos 100 operaciones y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["HVF v1"],
        "notes": "1 prueba + 16 de sensibilidad (percentil del HVN 91/93/97/99, confluencia 16/24/40/48 ticks, cercanía 2/3/5/6 ticks, confirmación 40/50/70/80 s). Definiciones 'intacto' y 'llega de lejos' descartadas antes de correr por dar 0-3 señales (solo conteos). Confluencia 4 puntos daba 73 señales; se fijó en 8 (115) mirando solo el conteo. Salida a 15 min sin objetivo viene de P012 (diseño): exploratorio, el DSR lo penaliza. Definición en docs/investigacion/hvn_poderoso.md.",
    },
    "abv_v1": {
        "hypothesis": "ABV v1 (absorción de flujo agresivo en POC, VAH y VAL del perfil en desarrollo del propio día; mismo detector que ABS/ABI con confirmación a 60 s y salida a 15 min; tolerancia de cercanía 8 ticks): el precio se aleja del lado absorbido más de lo que lo hace un RAND emparejado y RAND2; la estrategia gana después de costos, es positiva en 2024, 2025 y 2026, tiene al menos 100 operaciones y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABV v1"],
        "notes": "1 prueba + 16 de sensibilidad (cercanía 4/6/10/12 ticks, confirmación 40/50/70/80 s, stop mínimo 4/8/16/20, salida 5/10/20/25 min). Exploratorio: la partición por nivel (POC/VAH/VAL contra extremos y VWAP) se vio en P021, periodo de diseño; no es validación independiente y el DSR la penaliza. Tolerancia y enfriamiento se fijaron mirando solo el conteo de señales (132). Definición en docs/investigacion/absorcion_valor_desarrollo.md.",
    },
    "abi_v1": {
        "hypothesis": "ABI v1 (absorción en los niveles del propio día: máximo y mínimo de la sesión, VWAP, POC/VAH/VAL del perfil en desarrollo; mismo detector de flujo que ABS v1 con confirmación y salida a 15 min): el precio se aleja del lado absorbido más de lo que lo hace un RAND emparejado; la estrategia gana a RAND y RAND2 después de costos, es positiva en 2024, 2025 y 2026, tiene al menos 100 operaciones y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABI v1"],
        "notes": "1 prueba + 16 de sensibilidad (cercanía 2/3/5/6 ticks, confirmación 40/50/70/80 s, stop mínimo 4/8/16/20, salida 5/10/20/25 min). Definición fijada antes de correr (docs/investigacion/absorcion_intradia.md). Solo se miró el conteo de señales (48 con 3 niveles, 126 con 6 niveles); ninguna ganancia. La elección confirmación + salida por tiempo viene de P012 vs P016 (periodo de diseño): exploratorio, el DSR lo penaliza.",
    },
    "aceptacion_v2": {
        "hypothesis": "ACC v2 (aceptación fuera de los bordes de la subasta anterior: VAH, VAL, máximo y mínimo de ayer, máximo y mínimo de la noche; solo días que abren dentro del valor de ayer): con la misma regla de aceptación de ACC v1 (180 s fuera, delta agresivo a favor ≥ 5%), continúa más de lo que lo hace un RAND emparejado y RAND2 después de costos, es positiva en 2024, 2025 y 2026, tiene al menos 100 operaciones y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ACC v2"],
        "notes": "1 prueba + 16 de sensibilidad (tiempo 90/270/360 s, delta 3/7/9%, stop 2/6/8 ticks, salida 5/15/25 min; los vecinos que dan 0 o negativo se omiten, como en v1). Los dos cambios respecto de ACC v1 (más niveles; filtro 'abre dentro del valor') se fijaron mirando las tablas por régimen de P012, P016 y P017 en el periodo de diseño: es exploratorio y NO cuenta como validación independiente; el DSR lo penaliza con todos los intentos. Antes de fijar la regla solo se contó el número de señales (110 en 556 sesiones), no ganancias. Segunda versión de ACC.",
    },
    "regla80_v1": {
        "hypothesis": "VAR v1 (regla del 80%, pendiente de aceptacion.md): cuando el precio abre fuera del área de valor de ayer (VAH/VAL), vuelve adentro y se queda 180 s seguidos con delta agresivo hacia el interior ≥ 2%, rota hacia el otro lado del valor más de lo que lo hace un RAND emparejado; la estrategia gana a RAND y RAND2 después de costos, es positiva en 2024, 2025 y 2026 y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["VAR v1"],
        "notes": "1 prueba + 16 de sensibilidad (tiempo adentro 60/120/240/300 s, delta 1/3/4%, stop 2/6/8 ticks, salida 10/20/40/50 min). Definición base fijada antes de correr (docs/investigacion/regla80.md). Solo conteo de eventos mirado antes; riesgo declarado: cerca del mínimo de 100 operaciones.",
    },
    "smt_v1": {
        "hypothesis": "T3-SMT (aprobada por Jose Miguel 24/10/2026): cuando NQ barre el máximo (mínimo) de la sesión y ES no lo confirma, y NQ regresa adentro en menos de 120 s con delta agresivo contrario, el barrido es falso y el precio revierte; la estrategia SMT v1 gana a RAND y RAND2 después de costos, es positiva en 2024, 2025 y 2026 y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["SMT v1"],
        "notes": "1 prueba + 16 de sensibilidad (ventana de ES 60/90/150/180 s, plazo del fallo 60/90/150/180 s, stop 0/2/6/8 ticks, salida 5/10/20/25 min). Definición base fijada antes de correr (docs/investigacion/smt.md). Solo NQ→ES (no el espejo ES→NQ). Datos de ES fuera del manifiesto de huellas.",
    },
    "aceptacion_v1": {
        "hypothesis": "Pedido de Oscar (25/10/2026): cuando el precio sale del área de valor de ayer (VAH/VAL) y la acepta (180 s seguidos fuera con delta agresivo a favor ≥ 5%), continúa más de lo que lo hace un RAND emparejado, y la estrategia ACC v1 gana a RAND y RAND2 después de costos, es positiva en 2024, 2025 y 2026 y pasa Topstep.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ACC v1"],
        "notes": "1 prueba + 16 de sensibilidad. Las definiciones alternativas de aceptación (tiempo 90/270/360 s, delta 2/8/11%, stop 2/6/8, salida 10/15/25/30 min) se comparan aquí y cuentan como intentos. Definición base fijada antes de correr (docs/investigacion/aceptacion.md).",
    },
    "abs_v3": {
        "hypothesis": "ABS v3 (absorción con entrada temprana, sin confirmación de 60 s, stop v1, salida por tiempo a 15 min) gana a RAND y RAND2 después de costos, es positiva en 2024, 2025 y 2026, y sube la tasa de Topstep sobre el 41-43% de ABS v2.",
        "n_declared": 1 + 16,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["ABS v3"],
        "notes": "1 prueba + 16 de sensibilidad (4 parámetros x 4 vecinos). Tercera y última versión de ABS. T2-ABS-HOURS descartada (requiere cambio de motor).",
    },
    "salidas_1_1": {"hypothesis": "Repetición del estudio de salidas (pedido de Oscar) con el motor 1.1 y percentiles exactos.", "n_declared": 159, "kill": ["sin meseta"], "strategies": ["BIG v1", "ABS v1", "POC v1 (salidas)"], "notes": "Repite salidas_v1 (motor 1.0, superado)."},
    "mapa_v4": {"hypothesis": "Repetición del mapa v3 con percentiles exactos de órdenes y ventanas (los umbrales de 'órdenes grandes' y 'absorción' cambian).", "n_declared": 72, "kill": ["no sobrevive Holm", "signo distinto 2024/2025"], "strategies": ["12 señales × régimen"], "notes": "Repite mapa_v3 (umbrales del motor 1.0)."},
    "repeticion_1_1": {
        "hypothesis": "Repetición de P002–P008 con el motor 1.1 (llenados corregidos tras la revisión ciega del 24/10/2026). Las reglas selladas no cambian. Se espera que los resultados empeoren.",
        "n_declared": 7 + 112,
        "kill": ["los mismos criterios del protocolo v3"],
        "strategies": ["BIG v1", "ABS v1", "POC v1", "ABS v2", "HVN v1", "BIG v2", "ORB v1"],
        "notes": "7 pruebas + 16 de sensibilidad cada una. Los intentos cuentan igual que cualquier otro.",
    },
    "tanda3": {
        "hypothesis": "BIG v2 (seguir la orden grande con entrada inmediata, objetivo 12, stop 16) y ORB v1 (ruptura del rango inicial, 16/16, 30 min), con premisas del mapa v3 medido desde precios operables, ganan a RAND después de costos y pasan Topstep.",
        "n_declared": 2 + 32,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["BIG v2", "ORB v1"],
        "notes": "Aprobadas por Jose Miguel el 24/10/2026. Corre el orquestador.",
    },
    "proxy_v1": {
        "hypothesis": "Con el rango y el cuerpo de los primeros 15 minutos, la apertura dentro/fuera del valor y la distancia al VWAP a las 09:45 se puede anticipar si el día terminará en balance o tendencia claramente mejor que la base.",
        "n_declared": 1,
        "kill": ["ningún proxy separa más de 15 puntos porcentuales de la base"],
        "strategies": ["proxy de régimen"],
        "notes": "Descriptivo salvo la precisión del mejor proxy (1 intento). Aprobado por Jose Miguel el 23/10/2026.",
    },
    "mapa_v3": {
        "hypothesis": "Repetición del mapa v2 midiendo desde el mid del libro operable (bid/ask antes del primer llenado posterior) en vez del último llenado, que en un barrido queda ~8 ticks atrás del libro real. Se espera que 'desvanecer órdenes grandes' desaparezca y que el resto se corrija en menor medida.",
        "n_declared": 48 + 24,
        "kill": ["no sobrevive Holm", "signo distinto en 2024 y 2025"],
        "strategies": ["12 señales × régimen"],
        "notes": "Corrección metodológica tras el hallazgo del 23/10/2026 (FADE). El mapa v2 queda en signal_map_v2.json como registro del error.",
    },
    "tanda2b": {
        "hypothesis": "FADE v2 (objetivo 8, stop 12, 10 min) y FADEL v1 (entrada pasiva con cola) capturan el efecto de 6–7 ticks contra las órdenes grandes y ganan a RAND después de costos.",
        "n_declared": 2 + 32,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["FADE v2", "FADEL v1"],
        "notes": "Reemplaza a FADE v1 (descartada sin correr tras el humo). Aprobado por Jose Miguel el 23/10/2026.",
    },
    "tanda2": {
        "hypothesis": "FADE v1 (desvanecer órdenes grandes), HVN v1 (rechazo de nodos de ayer) y ABS v2 (dejar correr al ganador), con números medidos en el mapa v1 y el estudio de salidas, ganan a RAND después de costos y pasan Topstep.",
        "n_declared": 3 + 48,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["FADE v1", "HVN v1", "ABS v2"],
        "notes": "3 pruebas + 48 de sensibilidad. Arranca solo cuando el comité pase las pruebas a 'congelada' en el backlog.",
    },
    "mapa_v2": {
        "hypothesis": "Las 12 señales, además del azar de la misma dirección, se comparan contra un azar con dirección aleatoria (¿la dirección es rentable?), se parten por régimen (tendencia/balance) y por media hora, y se exige que el signo del efecto a 15 min sea el mismo en 2024 y en 2025.",
        "n_declared": 48 + 24,
        "kill": ["no sobrevive Holm (48 principales / 24 de régimen)", "signo distinto en 2024 y 2025"],
        "strategies": ["12 señales × régimen"],
        "notes": "Aprobado por Jose Miguel (método, no estrategia). El desglose por media hora es descriptivo: no se cuenta como prueba.",
    },
    "salidas_v1": {
        "hypothesis": "Pedido de Oscar (23/10/2026): con las mismas señales v1, un take profit fijo (20/30/40/50 puntos), otro stop fijo (3/4/6/8 puntos), más tiempo, o agregar contratos a favor, mejoran el resultado neto y forman una meseta (no un pico aislado).",
        "n_declared": 159,
        "kill": ["sin meseta: solo celdas aisladas ganan", "la celda mejor pierde con costos al doble o depende de 5 días"],
        "strategies": ["BIG v1", "ABS v1", "POC v1 (salidas)"],
        "notes": "5 TP × 5 SL × 2 tiempos = 50 celdas por estrategia (menos la base ya publicada) + 4 variantes de piramidar × 3 estrategias. Explora la dimensión de salida, no la señal. Nada se adopta sin versión nueva y protocolo completo.",
    },
    "mapa_v1": {
        "hypothesis": "Alguna de las 12 señales de order flow mueve el precio en la dirección predicha a 1, 5, 15 o 30 min más de lo que lo hacen momentos al azar a la misma hora.",
        "n_declared": 48,
        "kill": ["p de permutación no sobrevive Holm 5% sobre 48 pruebas", "menos de 100 eventos en el periodo de diseño"],
        "strategies": ["12 señales"],
        "notes": "Fase 1 del plan. Sin stops ni objetivos. Mide y publica todo; nada se descarta antes de medir.",
    },
    "tanda1": {
        "hypothesis": "Las estrategias BIG, ABS y POC v1 (reglas de los videos con números propuestos sin medir) ganan a RAND emparejado después de costos.",
        "n_declared": 3 + 48,
        "kill": ["ganancia neta <= 0 con costos base", "p vs RAND > 0.20", "pierde en 2 de 3 años", "rompe MLL en > 50% de arranques"],
        "strategies": ["BIG v1", "ABS v1", "POC v1"],
        "notes": "3 pruebas principales + 48 corridas de sensibilidad (4 parámetros × 4 vecinos × 3 estrategias). Es el 'intento ingenuo': los números no salen de los datos.",
    },
}


def main():
    sid = sys.argv[1]
    s = STUDIES[sid]
    registry.register_study(sid, s["hypothesis"], s["n_declared"], s["kill"], s["strategies"], s["notes"])
    print("estudio registrado:", sid, registry.study_counts(sid))


if __name__ == "__main__":
    main()
