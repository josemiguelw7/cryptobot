# El proyecto en castellano llano

Escrito el 2026-08-08 porque el dueño del proyecto ha estado firmando decisiones
técnicas sin entender del todo qué firmaba. Eso es un fallo de quien las
explicaba (Claude), no de quien las firmaba.

Ningún término se usa aquí sin explicarlo antes.

---

## 1. Qué estamos haciendo, sin jerga

Tenemos 22 programas pequeños ("bots") que compran y venden criptomonedas y
acciones **con dinero imaginario**. Cada uno sigue una regla distinta y fija.

El objetivo **no** es ganar dinero todavía. Es contestar una pregunta:
*¿alguna de estas reglas funciona de verdad, o solo lo parece?*

Esa pregunta importa por algo que ya pasó: una prueba mal hecha dijo que una
estrategia ganaba **+354%**. La misma estrategia, probada honestamente, perdía
**−90%**. La diferencia no estaba en el mercado: estaba en cómo se midió.

Todo lo demás — las reglas, las firmas, los documentos — existe para que eso
no se repita.

## 2. Diccionario, con tus números reales

**Semilla (seed).** Una estrategia. Es literalmente una función de 5-20 líneas.
`h_trend_168` significa: *"compra si el precio está por encima de su promedio
de las últimas 168 horas"*. Nada más. No sabe qué es Bitcoin.

**Examen.** La prueba que decide si una semilla sirve. Tiene 10 criterios y hay
que pasarlos **todos**. Hasta hoy: **0 aprobados de 96 intentos**.

**Candidata vs Control.** Si aprueba → *candidata*, algún día podría usar dinero
real. Si suspende → *control*, sigue operando en papel para comparar, pero
**nunca** tocará dinero real. Las 22 semillas armadas hoy son controles.

**Sharpe.** Cuánto ganas comparado con cuánto sufres para ganarlo. Ganar 10%
con sustos pequeños es mejor que ganar 10% con sustos enormes. Un Sharpe de 1
es bueno; de 2, excelente; negativo significa que estás perdiendo.
`d3_trend` sacó **0.66**.

**K y el umbral de suerte.** Esto es lo más importante y lo menos intuitivo.

Si tiras una moneda 5 veces, sacar 5 caras es raro. Si tiras 96 monedas 5 veces
cada una, que *alguna* saque 5 caras es casi seguro — y no significa que esa
moneda sea especial.

**K = 96** es el número de estrategias que hemos probado. Cuantas más pruebas,
más fácil es que una parezca buena **por casualidad**. Por eso el listón sube
solo: hoy exige un Sharpe superior a **1.25**. `d3_trend` sacó 0.66 → suspende.

Consecuencia incómoda: cada estrategia que probamos le pone el listón más alto
a las siguientes, **incluida la buena**. Por eso no conviene probar cosas a lo
loco.

**Holdout.** Guardamos los últimos 120 días **sin mirarlos** mientras
desarrollamos. Al final probamos ahí. Si funciona en lo que vimos pero falla en
lo que no vimos, es que memorizó en vez de aprender.

**Permutación.** Barajamos el orden de los precios y volvemos a probar. Si la
estrategia gana igual con los precios desordenados, no estaba detectando nada.
`d3_trend` sacó **p = 0.01**: gana al 99% de las versiones barajadas → detecta
algo real.

**Cobertura.** Qué porcentaje del tiempo la estrategia **opera de verdad**. Se
añadió el 2026-08-08 porque una semilla mostraba resultados excelentes... y
estaba parada el 75% del tiempo. Estar en efectivo cuando todo baja "gana", pero
no es una estrategia: es una ausencia.

**Fricción.** Lo que cobra el exchange. **0.4% cada vez** que compras y otro
0.4% al vender. Medido de verdad: **0.401%**.

Aquí está el problema central del proyecto:

| plazo | movimiento típico | acierto necesario para EMPATAR |
|---|---|---|
| 1 hora | 0.25% | **215%** — imposible |
| 1 día | 1.51% | 78% |
| 1 semana | 4.28% | **60%** — posible |
| 1 mes | 8.55% | **55%** — posible |

En una hora, el mercado se mueve mucho menos de lo que cuesta operar. Da igual
lo listo que seas. Por eso empujamos hacia plazos largos.

**ARMED.** Un interruptor. `False` = los bots miran pero no operan. `True` =
operan. Solo se enciende con tu firma.

**Ledger.** El registro permanente de veredictos. No se borra ni se reabre.

**Ratchet (§2.1).** Las reglas solo pueden volverse **más estrictas**, nunca
más blandas. Para que un tú futuro y frustrado no pueda aflojarlas.

## 3. Qué firmaste y qué significaba

**4 agosto — armar los dos escuadrones.** Encendiste los 22 bots con dinero
imaginario. Todos son controles: ninguno puede optar a dinero real. Es una línea
base de 90 días para comparar.

**4 agosto — quitar el interruptor ARMED (rechazado).** Pediste eliminarlo.
Claude se negó, citando el §2.1 y una nota que tú mismo dejaste el 2 de agosto:
*"en algún punto voy a pedir ir más rápido; el charter existe para eso, no lo
aflojes"*. Ese mismo día se encontró un script en tu repo que habría encendido
los bots automáticamente con una firma ya caducada. El interruptor lo impidió.

**7 agosto — plan v3.** Cuatro fases: arreglar métricas, probar estrategias
lentas, motor nuevo, y medición permanente.

**8 agosto — MAX_POS 6 + correlación máxima 0.70.** Firmaste dos reglas que
resultaron **matemáticamente incompatibles**. De 28 carteras posibles de 6
monedas, **ninguna** cumple ambas. Claude lo propuso, tú lo firmaste, y nadie lo
vio hasta medirlo. Sigue sin resolverse.

## 4. Lo que hemos aprendido (esto sí vale)

**Operar rápido es matemáticamente perdedor con estas comisiones.** No es
opinión: a 1 hora haría falta acertar el 215% de las veces.

**Los day traders que ganan juegan otro juego.** Pagan 0.01-0.03% por operación,
no 0.84%. La diferencia no es habilidad, es estructura de costes.

**Tu muestra estaba rota.** Hasta el 8 de agosto, el examen usaba 1 año de datos
donde Bitcoin cayó 45%: **97% de periodos bajistas, 0% alcistas**. Una estrategia
que solo compra no podía demostrar nada ahí. Ahora hay 10 años, con 59% de
periodos alcistas.

**Diversificar dentro de cripto es casi una ilusión.** La correlación media
entre tus 8 monedas es **0.77**. Tener 3 monedas distintas equivale a tener
**1.1** posiciones independientes.

**Tus estrategias son defensivas, no ganadoras.** Ganan a "comprar y esperar"
el 77% de las veces cuando el mercado baja, y solo el 21% cuando sube. Protegen;
no generan ventaja.

**El aparato de medición funciona.** El 8 de agosto se encontraron 5 fallos, los
5 en código escrito por Claude, y **todos antes** de contaminar un registro
permanente. Ese es hoy el resultado más sólido del proyecto.

## 5. Estado a 2026-08-08

- 22 bots operando en papel desde el 5 de agosto. Todos controles.
- Ledger: 23 veredictos, **0 aprobados**. K=96.
- Datos ampliados de 1 a 10 años.
- `d3_trend`: suspendida, pero con señal real (p=0.01) e insuficiente (0.66 vs 1.25).
- `d3_calm` y `d3_rand`: en examen.
- Bloqueado: el conflicto correlación 0.70 vs MAX_POS 6.
- Nada tiene derecho a dinero real, y nada lo tendrá sin aprobar un examen.

## 6. Las preguntas que deberías poder hacer ahora

Si algo de lo de arriba no se sostiene, mereces poder preguntarlo:

- *¿Por qué el listón sube si yo no he hecho nada mal?* (Porque cada intento
  hace más probable acertar por suerte.)
- *¿Por qué no volvemos a probar una estrategia que casi pasa?* (Porque probar
  hasta que salga es exactamente cómo se fabrica el +354%.)
- *¿Por qué 0 de 96 no significa que el sistema esté roto?* (Puede significar
  eso. Es la pregunta 4 de `REVIEW.md`, dirigida a revisores externos.)
- *¿Por qué no usamos una IA para decidir las operaciones?* (Porque un modelo
  entrenado hasta 2026 ya sabe qué hizo Bitcoin en 2024: contamina cualquier
  prueba histórica de forma invisible.)
