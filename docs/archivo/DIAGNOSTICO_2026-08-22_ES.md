# Qué encontramos el 22 de agosto de 2026

*Escrito en lenguaje llano para que puedas evaluar esto sin depender de
mi lectura. Igual que `LIMITES_ES.md`.*

*Aviso que debes tener presente: este documento lo escribió Claude, que
es también quien hizo las mediciones que describe. No es un control
independiente. Léelo con esa desconfianza puesta.*

---

## 1. Lo que creías que pasaba, y lo que pasaba en realidad

Viste en el dashboard que los bots parecían sostener una sola posición
sin operar, y que todas las curvas se veían iguales.

**Los bots sí operaban.** 319 operaciones en cripto, 361 en acciones.
La última fue el mismo día que preguntaste.

**Las curvas no eran iguales.** Si dos curvas se movieran idénticas, la
correlación sería 1.00. En cripto la mediana fue 0.27, que es bastante
distinto. Entre el mejor y el peor bot había 33 puntos de diferencia.

**Lo que sí viste:** ocho de los once bots de cripto estaban en efectivo,
sin ninguna posición. Una línea de efectivo se ve exactamente igual que
una posición dormida. Tu ojo detectó algo real, pero la causa era otra.

**Y en acciones tenías razón:** seis de once bots tenían TSLA al mismo
tiempo, cinco tenían META. Esa concentración era genuina.

## 2. El problema real, que es peor

Comparamos los bots contra la estrategia más tonta posible: **comprar
todo el día uno y no volver a tocarlo**.

| | Comprar y sostener | Mejor bot | Mediana de bots |
|---|---|---|---|
| Cripto | **+28.6%** | +26.2% | +11.8% |
| Acciones | −1.65% | −0.22% | −2.86% |

**En cripto, cero de once bots le ganan a no hacer nada.**

En acciones, dos de once le ganan al índice, pero los once pierden
dinero en términos absolutos.

**Y el bot que va primero en cripto es el que decide al azar.** Ese bot
existe justamente como control: si las estrategias no le ganan a tirar
una moneda, la lógica no está aportando nada. Hoy no le ganan.

## 3. De dónde sale realmente el dinero en cripto

Los bots salen de una posición por dos motivos: porque la señal les dice
que salgan, o porque salta un stop.

| Tipo de salida | Operaciones | Resultado |
|---|---|---|
| Por señal | 131 | **−102** |
| Por stop | 25 | **+2,436** |

Toda la ganancia de cripto viene de 25 operaciones. Las 131 salidas por
señal, juntas, pierden dinero.

**La pista de acciones no tiene stops.** Ninguno. Las 166 salidas fueron
por señal, y pierde en todos los bots.

## 4. Por qué no toqué nada de eso

Aquí es donde tienes que vigilarme.

Lo obvio sería: "las salidas por señal pierden dinero, quitémoslas". Eso
es exactamente el procedimiento que produjo el **+354% falso** que dio
origen a este proyecto. Miras 17 días, encuentras qué perdió, lo quitas,
y el resultado mejora — pero solo para ese pasado, no para el futuro.

Lo que hicimos fue **escribirlo como predicción** (`decisions.md`,
pre-registro H1): en 90 días, con al menos 150 operaciones nuevas, las
salidas por señal seguirán siendo negativas. Los umbrales quedaron
congelados. Si acierta, es evidencia. Si me dejas cambiarlos cuando
llegue el resultado, no vale nada.

**Esa es la única diferencia entre ciencia y autoengaño: si el criterio
se fijó antes o después de ver el resultado.**

## 5. La fricción de acciones

Descubrimos que la pista de acciones calculaba costes de **cero**.
Comisión cero es realista; spread y deslizamiento cero no lo son.

Calculamos cuánto cambia:

| Fricción | Pérdida ajustada |
|---|---|
| Actual (cero) | −966 |
| 10 bps por pata | −1,229 |
| 20 bps por pata | −1,492 |

**La fricción no era el problema principal.** Aun con costes altos, el
coste es la mitad de la pérdida que ya existía. La pista de acciones
pierde por la estrategia, no por el modelo de costes.

## 6. Dos cosas que se estaban rompiendo en silencio

**Los tests de seguridad llevaban semanas fallando.** Hay pruebas que
verifican que ningún bot exceda el tope de posiciones del charter.
Fallaban, pero nadie las veía porque la herramienta para ejecutarlas no
estaba instalada. Ahora corren cada hora y el fallo se ve.

**El dashboard se murió otra vez.** Segunda vez documentada. Ahora hay
supervisión automática: lo maté a propósito para probarlo, y se relanzó
solo en menos de 40 segundos.

## 7. Lo que decides tú, no yo

1. **Fricción en acciones** — entra mañana si no la cancelas.
2. **La regla §9.6** — si un mecanismo nuevo de salida cuenta como
   "mutación de parámetro". Bloquea trabajar en los stops de acciones.
3. **Topes de posición** — fecha puesta al 21 de septiembre.
4. **Si la pista de acciones sigue viva** — 26% de aciertos con una
   relación riesgo/beneficio de 0.58 pierde en las dos dimensiones a la
   vez. Eso no se arregla con parámetros.

## 8. La cosa más importante de todo este documento

En una sola sesión, Claude midió el sistema, interpretó las mediciones,
redactó las propuestas, te recomendó cuáles aprobar, las implementó, y
escribió tanto la petición de revisión externa como este resumen.

**No queda nadie fuera del circuito.**

Puedo estar equivocado de una manera que ni tú ni yo detectemos, porque
yo soy quien decide qué medir y tú dependes de mí para interpretarlo.
Eso no es un problema de estrategia; es el riesgo más grande que tiene
el proyecto ahora mismo, por encima de cualquier número de arriba.

Está en `docs/REVISION_INDEPENDIENTE.md`, con cinco preguntas para un
revisor que no sea Claude. Conseguir a esa persona es lo único de toda
la lista que no puedo hacer yo.
