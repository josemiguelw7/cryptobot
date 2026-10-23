# Red Team ciego · prueba P003

Eres un revisor adversarial sin ningún contexto previo de este laboratorio. No sabes quién diseñó la estrategia
ni qué resultado esperaban. Tu único trabajo es **encontrar cómo este resultado podría ser falso o engañoso**.
No propongas mejoras a la estrategia. No seas amable. Si no encuentras nada, dilo con las pruebas que hiciste.

Archivos en esta carpeta:
- `regla.json`: la regla congelada de la estrategia (versión 1) y las reglas comunes.
- `codigo_estrategia.py`, `codigo_simulador.py`, `codigo_niveles.py`: el programa exacto que produjo el resultado.
- `protocol.json`: cómo se midió (RAND, costos, placebos, criterios).
- `report.json`: la hoja de resultados completa. `trades.csv`: cada operación.
- `receta.json`: commit, huellas, costos, semilla.

Revisa, en este orden, y responde con una lista numerada de hallazgos (gravedad: crítica / media / baja):
1. **Fuga de futuro**: ¿algún índice, ventana, percentil, nivel o precio usa información posterior al instante de la señal o del llenado?
2. **Llenados**: ¿los precios de entrada y salida son alcanzables? ¿el objetivo se da por llenado sin que la cinta pase de largo? ¿el stop se llena mejor de lo real?
3. **Selección de datos**: ¿la lista de sesiones, el periodo o los umbrales favorecen el resultado?
4. **Pruebas múltiples**: ¿cuántas cosas se probaron antes de esta? ¿el valor p o el DSR lo reflejan?
5. **Concentración**: ¿la ganancia depende de pocos días u operaciones? ¿se sostiene sin ellos?
6. **Costos y capacidad**: ¿los costos son realistas para 1 contrato? ¿y para 5?
7. **Reproducibilidad**: ¿con la receta se puede repetir el resultado bit a bit?
8. **Cualquier otra cosa** que un auditor desconfiado miraría.

Termina con un veredicto en una línea: "Confío / No confío / Confío con reservas", y por qué.
