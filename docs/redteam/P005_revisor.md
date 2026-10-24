# Auditoría adversarial ciega — P005 · ABS v2 (texto íntegro del revisor, 24/10/2026)

Resultado preliminar: el beneficio contabilizado existe en el CSV, pero no hay evidencia suficiente para considerarlo una ventaja operable y estadísticamente validada.

Beneficio reportado +$8.868,72 (126 operaciones) · DSR reportado 0,001 (mínimo exigido 0,95) · Topstep 43,5% (mínimo exigido 50%).

He comprobado que los 126 registros de trades.csv suman exactamente $8.868,72 netos ($9.345 brutos menos $476,28 de comisiones) y que la curva acumulada del informe coincide con el CSV. Esa conciliación valida la aritmética del informe, no la ejecución real de las operaciones ni la legitimidad de las señales.

## Hallazgos

1. [CRÍTICA] Fuga de futuro: falta precisamente el código que genera las señales ABS. codigo_estrategia.py invoca V1.absorption() desde un módulo v1 que no fue entregado. No encontré fuga directa en codigo_niveles.py (reference() usa el perfil NY anterior y la noche; thresholds() las 20 sesiones previas), pero la parte más importante está sin auditar.

2. [CRÍTICA] Fuga de futuro: el placebo anticipado produce más del triple del beneficio real ($27.241,88 vs $8.868,72; 3,07×). No demuestra fuga por sí solo, pero tampoco permite descartarla. La sospecha sigue abierta.

3. [MEDIA] Percentiles: pooled_quantile() combina solo las 500 ventanas mayores por sesión. Prueba sintética con 20 sesiones de 1.000 ventanas (2 de volumen alto, 18 bajo): percentil 95 verdadero 100, calculado 1, sin excepción. Defecto reproducible.

4. [CRÍTICA] Llenados: operación del 22/02/2024 09:48:30 con entrada 17.896,25, objetivo 17.936,25, +$796,22, duración 0 s, MFE +179 / MAE −179. El primer precio operado estaba ~44,75 puntos sobre la entrada; el objetivo se cobra en el mismo evento. Reproducido con codigo_simulador.py (_best() y simulate()).

5. [CRÍTICA] Llenados: los stops se contabilizan siempre en el precio del stop menos un deslizamiento fijo aunque el mercado salte más allá (entrada 1.000, stop 968, siguiente transacción 940, salida acreditada 967).

6. [MEDIA] La regla through es más exigente que tocar el objetivo, pero no verifica profundidad, cola ni cantidad ejecutable. 27 objetivos de +160 ticks a $796,22 ($21.497,94) contra 90 stops (−$14.945,20). Si 10 de esos 27 objetivos terminaran como stops típicos, el total pasaría a −$781,28.

7. [MEDIA] Selección de datos: la huella de las 576 fechas coincide con la receta, pero no se demuestra la neutralidad del criterio de validez ni que el examen sellado nunca se consultó. La v2 fue seleccionada con datos del mismo periodo.

8. [CRÍTICA] Pruebas múltiples: p nominal 0,003 vs RAND, pero DSR 0,001 frente a 0,95 exigido; backtest de ~2,3 años contra 8,35 años de largo mínimo; 295 intentos no enumerados (faltan trials.jsonl y los estudios).

9. [CRÍTICA] Concentración: 5 mejores días 71,8%; 10 mejores días 116,7%; sin los 10 mejores días −$1.482,14. Por año: 2024 +$8.888,32 (56 op.), 2025 +$139,54 (57), 2026 −$159,14 (13); 2025–2026 combinados −$19,60.

10. [CRÍTICA] Costos y capacidad: $3,78 por round turn coincide con Topstep. El deslizamiento fijo es hipótesis. A 5 contratos pasa 19,9% y 401 de 517 rompen el MLL. Curva: 0 ticks +$10.458,72 · 1 +$8.868,72 · 2 +$6.388,72 · 3 +$3.178,72 · 4 −$500,06.

11. [CRÍTICA] Reproducibilidad: faltan v1, data, config, cintas, estadísticas de umbrales, perfiles, RAND/DSR/CPCV/Topstep, registro y entorno. Dos identificadores de commit sin explicar. La semilla descrita en el protocolo difiere de la registrada. "reproducible: true" es una afirmación, no una reproducción demostrada.

12. [CRÍTICA] Topstep 43,5% < 50% aunque desapareciera la sospecha de fuga; el estado "revisar" no comunica las otras limitaciones.

13. [MEDIA] RAND no conserva stop ni objetivo; p_rand=0,0066 no es obtenible con 1.000 simulaciones; CPCV 14/15 no valida la selección de parámetros.

14. [MEDIA] La descripción de ABS v2 ("objetivo que casi nunca se toca, salida temporal") no corresponde: 90 stops (71,4%), 27 objetivos (21,4%), 9 por tiempo (7,1%).

## Veredicto

No confío — P005 no supera los requisitos de robustez del propio protocolo, presenta una anomalía reproducible de llenado instantáneo, un modelo de stops potencialmente optimista y una concentración extrema. La ausencia del generador original de señales y de la cinta impide descartar fuga de futuro o certificar que los $8.868,72 fueran realmente ejecutables.
