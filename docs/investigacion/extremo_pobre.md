# Extremo pobre de ayer como imán (PEX) · idea descartada por vacía

Investigado el 26/10/2026. No se corrió ninguna ganancia: solo conteos de señales.

## Qué encontré
- Market Profile: un máximo o mínimo "pobre" es plano, con dos o más TPO en el mismo precio extremo y sin cola de rechazo. La subasta quedó sin terminar y se espera que el mercado vuelva a repararlo, pero es una tendencia, no una regla; algunos nunca se reparan. Fuentes: https://www.luxalgo.com/library/concept/poor-high-poor-low/ · https://nexusfi.com/a/concepts/poor-highs-and-poor-lows · https://nexusfi.com/a/market-structure/single-prints-poor-highs-poor-lows-market-profile
- La literatura habla de reparación en días o sesiones, no en minutos.

## Definición operable que probé
Extremo pobre = volumen medio de los 4 ticks de la punta del perfil NY de ayer ≥ 5 % del volumen medio por tick (≈ percentil 75 de esa razón en 396 extremos). Si hoy no se ha reparado (ni de noche ni en el día) y el precio está a 12–80 ticks, entrada a favor con delta de 60 s a favor y avance.

## Conteo
- 85 extremos pobres de 398 en 199 sesiones; 45 siguen sin reparar al abrir; solo en 11 días el precio entra a la zona antes de repararlo.
- Señales esperadas en 576 sesiones: 30–60, con cualquier combinación de umbrales de flujo (el filtro de flujo no es el cuello de botella; lo es la estructura).
- El protocolo exige ≥ 100 operaciones: saldría "insuficiente" siempre. **Descartada por vacía, no por resultado.** No se registró estudio ni intentos.
