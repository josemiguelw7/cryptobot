# Tamaño de posición: ABU v2 (las mismas señales de ABU v1 con 2 contratos)

## Por qué esta prueba
- P030 (ABU v1): +$5,956 en 181 operaciones, p 0.001 contra RAND, positiva en 2024, 2025 y 2026 (+$2,358, +$3,277, +$321). Pero Topstep **9.9%**.
- Ese 9.9% no viene de pérdidas: **0 de 517 cuentas rompieron el MLL** y el peor drawdown fue −$1,356. Viene de lentitud: 466 cuentas quedaron "sin resolver" porque 1 contrato junta unos $33 por operación (~$10 por día) y el límite es 120 sesiones para llegar a $3,000.
- Overnight/Londres (la idea que dejé en la corrida anterior) **no se puede probar con el motor actual**: `run_test.py` y `rand.py` cargan solo la ventana de Nueva York (`ny_only=True`), los umbrales de volumen son de NY y `rand.py` no se puede tocar. Un RAND sorteado en NY sería un control inválido. Queda anotado como hueco de infraestructura, no como hipótesis descartada.
- Lo que sí está en nuestras manos: el tamaño. El tamaño es parte de la regla de una estrategia (máx. 5 contratos en la cuenta de $50K, `topstep_rules.json`).

## Qué dicen las reglas (fuentes ya verificadas en `futures/topstep_rules.json`, 22/10/2026)
- Límite diario (DLL): $1,000. Pérdida máxima (MLL): $2,000, sigue al balance al cierre del día y se vigila con P&L no realizado.
- Máximo 5 contratos.
- Práctica común de trading con cuentas de fondeo: dimensionar para que el peor día posible quede dentro del límite diario, no para maximizar ganancia.

## Definición fijada (antes de correr)
- Señales, detector, niveles, filtro de apertura, stop 12–32 ticks, objetivo 2R, salida 15 min, ventana 09:30–15:30: **idénticos a ABU v1** (mismo código).
- Único cambio: **2 contratos** por operación.
- Por qué 2 y no otro número: reglas del sistema = máximo 6 operaciones por día y se detiene tras 3 pérdidas seguidas. Tres pérdidas al stop máximo (32 ticks = $160 por contrato + $3.78 de comisión) con 2 contratos suman ≈ $1,000 = el DLL. Con 3 contratos un solo día malo ya podría pasar el DLL. Es un tope por regla, no una cifra buscada sobre resultados.
- No se probó 3, 4 ni 5 contratos como candidatas. P030 ya mostró a 5 contratos (46% pasan pero 260 de 517 cuentas rompen el MLL): demasiado riesgo. No se vuelve a mirar esa tabla para elegir otro número.

## Qué NO es esta prueba
- **No es evidencia nueva de ventaja.** Con las mismas señales, el p contra RAND será casi el mismo que P030. Solo mide si, con tamaño permitido, el Topstep deja de ser el problema.
- No es validación independiente: las señales salen de los mismos datos de diseño (2024-01 a 2026-04) que ABU v1, ABD, ABI y ABV.
- ABU v1 quedó en "revisar" con placebo desplazado sospechoso (revisión de código pendiente): si la revisión encuentra una fuga, esto también cae.
- Limitación del motor: en el informe, "cinco_contratos" multiplica por 5 encima de los 2 contratos reales (serían 10): ignorar ese campo en esta prueba.
- El DSR sigue penalizado (893+ intentos en el registro): el criterio (b) no cambia con el tamaño.

## Cómo se lee el resultado
- Topstep ≥ 50% con rompe-MLL bajo → el cuello era el tamaño; sigue pendiente la revisión del placebo y el examen sellado.
- Topstep < 50% o rompe-MLL > 50% → con 1 a 2 contratos la familia de absorción no alcanza Topstep; dejar de buscar frecuencia en NY y construir soporte de overnight en el motor (cambio que debe pedir un humano porque toca `rand.py`).
