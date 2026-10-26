# Regla de riesgo diario: ABU v3 (ABU v2 con parada tras 2 pérdidas)

_Corrida del investigador, 25/10/2026. Nadie le preguntó a Oscar cómo definirla._

## Por qué esta prueba
- P038 (ABE v1, filtro de ES): +$1,181, p 0.05, 0 de 0 cuentas Topstep. El filtro de ES **no** mejora a ABU. Se cierra esa línea.
- Revisé el mapa de señales v3 (`futures/signal_map.json`) buscando algo sin probar: Agotamiento (p bruto 0.70 a 30 min), Momentum primera→última media hora (0.55), Ráfagas (la dirección real es la contraria y mide ~2 ticks, menos que la fricción), Desequilibrio de la mejor compra/venta (no es flujo agresivo). **Nada con ventaja sin probar.** Overnight/Londres sigue sin poder probarse (`rand.py` solo sortea en NY y no se toca).
- Lo que sí tiene ventaja es ABU (P030/P031: +$6.0k / +$11.9k, p 0.001, positiva 3 años). Lo que le falla es **Topstep**: P031 pasa 41.2%, pero 214 de 517 cuentas rompen el MLL.
- En P031 casi todas las cuentas que arrancan en enero-febrero de 2024 terminan con el mismo balance (≈ $48,322): rompen por el mismo racimo de pérdidas, no por falta de señal.

## Qué dicen las reglas y la práctica (fuentes ya verificadas)
- Topstep $50K (`futures/topstep_rules.json`, verificado 22/10/2026): límite diario $1,000, MLL $2,000 que sube con el balance, máximo 5 contratos.
- Práctica común con cuentas de fondeo: dimensionar y limitar para que el peor día quede lejos del límite diario. (Fuente interna: `docs/investigacion/tamano_posicion.md`; no hice búsqueda web nueva, la regla sale de las cifras de la cuenta.)

## Definición fijada (antes de correr)
- Señales, niveles, detector, stop 12–32, objetivo 2R, salida a 15 min, 2 contratos, ventana 09:30–15:30: **idénticos a ABU v2** (mismo código `v17.py`).
- Único cambio: el día se detiene tras **2 pérdidas seguidas** (v2: 3). Los otros límites (6 operaciones por día) no cambian.
- Por qué 2: con 2 contratos, una pérdida al stop máximo (32 ticks = $160 por contrato + comisión) cuesta ≈ $330. Tres = ≈ $1,000 = justo el límite diario. Dos = ≈ $660: queda dentro del límite con margen. Sale de las reglas de la cuenta, no de probar valores.
- Lo único que miré: P031 (resultado ya publicado) para ver qué cuentas rompían. No probé 1 ni otros valores para elegir.

## Qué NO es esta prueba
- **No es evidencia nueva de ventaja ni validación independiente.** Mismas señales, mismos datos de diseño. El p contra RAND será parecido a P031.
- Puede **bajar** la ganancia (menos operaciones). Si Topstep no sube de 41.2% o la ganancia cae, la regla de riesgo no sirve y ABU queda sin versiones (v3 es la última).
- El DSR sigue penalizado (más de 1,000 intentos): el criterio (b) no cambia.
- Es la **última versión de ABU**. ABU v1/v2 siguen en "revisar" por el placebo desplazado.

## Intentos (MISMO estudio `abu_v3`)
1 base + 16 sensibilidades de las cuatro perillas del detector (cercanía al nivel, confirmación, umbral relativo, objetivo R), iguales a las de ABU v1/v2. 17 en total. La base queda fijada; no se elige la mejor.

## Cómo se lee
- Topstep > 50% con rompe-MLL bajo y ganancia positiva en 2024/2025/2026 → el cuello era el riesgo diario; queda pendiente la revisión del placebo y el examen sellado.
- Si no → con tamaño y riesgo razonables ABU no alcanza Topstep; la familia de absorción queda cerrada en NY con 2 contratos.
