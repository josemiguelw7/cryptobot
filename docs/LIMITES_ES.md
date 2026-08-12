# Qué limita cada regla, y qué pasa si se quita

Escrito el 2026-08-11 en lenguaje llano, sin fórmulas y sin jerga.
Propósito: que puedas evaluar cualquier propuesta de cambio sin
depender de que quien te la propone tenga razón.

**Cómo usar este documento.** Cuando alguien —yo incluido— proponga
cambiar algo, busca la regla aquí y lee la línea "SI SE QUITA". Si el
que propone el cambio no menciona esa consecuencia, es señal de alarma
por sí sola.

---

# PARTE 1 — Las reglas del dinero (Nivel 1)

Estas no se pueden aflojar. Nunca. Ni con firma, ni con evidencia, ni
con una buena razón. Son las que te protegen de perder dinero de verdad.

### Techo de $3.000 en total

**Qué limita:** la cantidad máxima de dinero real que puede estar en
juego, sumando todos los bots de todas las clases de activo.

**Si se quita:** el peor día posible pasa de costarte $3.000 a costarte
lo que tengas. Todo lo demás en este proyecto —los exámenes, la
estadística, los guardarraíles— sirve para reducir la *probabilidad* de
perder. Solo esta regla limita el *tamaño* de la pérdida. Es la única que
funciona aunque todo lo demás falle a la vez.

### Escalera: $500 → $1.500 → $3.000, un peldaño cada 30 días limpios

**Qué limita:** la velocidad a la que el dinero entra. Aunque una
estrategia sea excelente, no puede recibir $3.000 antes de 60 días.

**Si se quita:** empiezas con el máximo. El problema no es el optimismo,
es el orden: los defectos aparecen con el tiempo, no al principio. Los
cinco bugs de esta semana llevaban días corriendo antes de que alguien
los viera. La escalera existe para que el dinero llegue *después* del
tiempo suficiente para que un defecto se manifieste, no antes.

### Papel antes que dinero real, siempre

**Qué limita:** ninguna estrategia toca dinero sin un PASS registrado y
una ventana de confirmación previa.

**Si se quita:** desaparece la distinción entre "creo que funciona" y
"se demostró que funciona". Es la regla que convierte este proyecto en
un experimento en vez de una apuesta.

### Gemelo en sombra durante todo el periodo en vivo

**Qué limita:** mientras un bot opera con dinero real, una copia sigue
operando en papel. Si las dos se separan, el bot en vivo se para.

**Si se quita:** pierdes la única forma de detectar que la realidad no
coincide con la simulación. Sin gemelo, un fallo de ejecución (precios
peores de los previstos, órdenes que no se llenan) se ve igual que una
mala racha, y esperarías a que pase en lugar de parar.

### Nada de compra-venta el mismo día en acciones

**Qué limita:** no por elección tuya — es regulación de FINRA. Con menos
de $25.000 en la cuenta, más de tres operaciones intradía en cinco días
te congela la cuenta.

**Si se quita:** no es una decisión que puedas tomar. La cuenta se
bloquea y punto.

### Ningún LLM toma ni modifica una decisión de operación real

**Qué limita:** yo puedo escribir el código, analizar resultados y
proponer cambios. No puedo estar en el circuito cuando hay dinero.

**Si se quita:** esta es la que más te conviene entender hoy. Un modelo
de lenguaje suena igual de seguro cuando acierta que cuando se equivoca.
Hace una hora te recomendé un tope de posiciones con total confianza,
basado en un número que yo mismo había medido mal. Lo detecté porque el
resultado era inverosímil y volví a medir — pero pude no haberlo
detectado. Esa regla existe porque mi confianza no es información sobre
si tengo razón.

### Parar es rápido, arrancar es lento

**Qué limita:** puedes detener cualquier cosa en cualquier momento; para
volver a encenderla hay que esperar a una revisión.

**Si se quita:** el sistema se vuelve simétrico, y no debe serlo. Parar
por miedo cuesta poco (esperas). Arrancar por entusiasmo cuesta mucho
(pierdes dinero). Las decisiones asimétricas necesitan frenos
asimétricos.

---

# PARTE 2 — Las reglas del examen (Nivel 2)

Estas sí se pueden cambiar bajo el charter v2, con entrada escrita y una
noche de espera. Son las que deciden si una estrategia merece dinero.
Cada una tapa un agujero concreto por el que se puede colar una
estrategia mala.

Para entender por qué son tantas: cada criterio existe porque alguien,
en algún momento, pasó un examen sin merecerlo de esa manera concreta.

### 1. Muestra mínima: al menos 24 ventanas y 4 monedas

**Qué limita:** que se juzgue con pocos datos.

**Si se quita:** una estrategia puede pasar por suerte en tres semanas
buenas de una sola moneda. Tú mismo mediste esto: con diez bots sin
ninguna ventaja, hay un 99,9% de probabilidad de que al menos uno
parezca ganador después de siete días.

### 2. La caída nunca peor que comprar y esperar

**Qué limita:** en *ninguna* ventana la estrategia puede caer más de lo
que habrías caído comprando y quedándote quieto.

**Si se quita:** admites estrategias que ganan más pero sufren más. Con
$3.000 y un techo de caída del 15%, una estrategia que cae mucho te
saca del juego antes de que su ventaja tenga tiempo de aparecer.

### 3. Caída más suave en al menos el 60% de las ventanas activas

**Qué limita:** que la protección sea habitual, no un golpe de suerte.
La palabra "activas" es nueva y crucial: ahora solo cuentan las ventanas
donde la estrategia realmente operó.

**Si se quita ese "activas":** vuelve el problema que la revisión
encontró. El 96% del crédito que ganaba `d3_trend` en este criterio venía
de ventanas donde no hizo absolutamente nada. Estar en efectivo tiene
caída cero, así que gana siempre. Sin esa palabra, la forma más fácil de
aprobar el criterio de riesgo es no jugar.

### 4. Rendimiento mediano al menos igual que comprar y esperar

**Qué limita:** que la estrategia justifique existir. Si no le ganas a
comprar Bitcoin y dormir, estás pagando comisiones por nada.

**Si se quita:** todo el proyecto pierde el sentido. Es el criterio más
importante y el más incómodo, porque comprar y esperar es un rival muy
duro.

### 5 y 5b. Actividad y cobertura: al menos 4 operaciones, y **ida y vuelta** en la mitad de las ventanas

**Qué limita:** que la estrategia realmente opere. "Ida y vuelta"
significa entrar *y salir* — una operación completa.

**Si se quita el "ida y vuelta":** este es el agujero que la revisión
encontró esta semana. Contar solo entradas hacía que una estrategia que
compró una vez y nunca vendió contara como "activa". Era un clon de
comprar-y-esperar disfrazado de estrategia. La mitad de las ventanas de
`d3_trend` eran exactamente eso.

### 6. Estrés de comisiones: todo lo anterior debe seguir cumpliéndose con costes un 50% más altos

**Qué limita:** que la ventaja sea robusta y no un margen que desaparece
si el mercado se pone caro.

**Si se quita:** apruebas estrategias cuya ventaja entera cabe dentro
del error de tu estimación de comisiones. Tu coste actual de ida y
vuelta es de aproximadamente **1,30%**. Una estrategia que opera mucho
tiene que superar ese peaje cada vez. Tú ya mediste que operar más
empeora los resultados de forma casi mecánica.

### 7. No basta con ganar en gráficos diarios

**Qué limita:** que el resultado dependa de mirar el mercado con una
lupa concreta.

**Si se quita:** apruebas estrategias que funcionan en una resolución
temporal y no en otra, lo cual casi siempre es señal de casualidad.

### 8. Prueba ciega: los últimos 120 días se examinan aparte

**Qué limita:** este es el criterio más importante de todos y el que más
te protege del error fundacional de este proyecto. La estrategia se
diseña y ajusta sobre datos viejos, y luego se prueba sobre un periodo
que nunca se usó para diseñarla.

**Si se quita:** vuelves exactamente al escenario del +354% contra el
−90%. Sin datos apartados, cualquiera puede construir una estrategia que
explique perfectamente el pasado y no sepa nada del futuro.

**Advertencia actual:** con la geometría de hoy, en esos 120 días solo
cabe una ventana por moneda. Ocho observaciones. La revisión señaló que
eso es demasiado poco para ser un filtro serio, y sigue sin resolverse.

### 9. Prueba de suerte: barajar el orden y ver qué pasa

**Qué limita:** se desordena el histórico al azar cientos de veces y se
comprueba si la estrategia sigue ganando. Si gana igual con los datos
barajados, no estaba detectando nada — solo estaba montada encima de la
subida general del mercado.

**Si se quita:** confundes "ganó" con "tenía razón". Es la diferencia
entre una estrategia y una apuesta que salió bien.

### 10. La barrera de suerte, ajustada por cuántas veces lo has intentado

**Qué limita:** este es el más difícil de intuir, y el más importante
que entiendas. Si pruebas 38 estrategias, la mejor de las 38 se ve
buenísima *aunque ninguna tenga ventaja*, simplemente porque es el
máximo de 38 intentos. El criterio 10 sube el listón según cuántos
intentos llevas.

**Si se quita:** cada estrategia nueva parece más prometedora que la
anterior y ninguna lo es. Es la trampa central de este oficio.

**Por qué importa el número K:** hoy tu registro tiene 38 filas. Cada
examen que corres —incluidos los anulados— sube el listón para todos los
futuros. Por eso anular veredictos no te devuelve nada gratis: los
nombres se liberan, pero la barrera no baja.

---

# PARTE 3 — Los parámetros

### MAX_POS: cuántas posiciones puede tener un bot a la vez

**Qué limita:** con $3.000 repartidos, más posiciones significa
porciones más pequeñas y más comisiones.

**Si se sube:** cada posición pesa menos, así que el resultado del bot
se parece más al mercado en general y menos a su estrategia. Un bot con
6 posiciones en un mercado donde todo sube y baja junto no tiene seis
apuestas: tiene una apuesta comprada seis veces, pagando seis peajes.

### MAX_CORR = 0,70: cuánto pueden parecerse dos posiciones

**Qué limita:** dos monedas que suben y bajan juntas no son dos
apuestas. La correlación mide eso: 1,00 es "idénticas", 0,00 es "sin
relación".

**Si se sube:** compras la apariencia de diversificación sin tenerla.

**Lo que mediste hoy:** tus 8 monedas están al **0,81** de correlación en
el último año. Solo un par de veintiocho cumple la regla. Eso no es un
fallo del sistema: es la regla informándote de que estas ocho monedas se
han convertido en una sola apuesta. Subir el número para que "quepan"
más posiciones sería apagar la alarma en vez de atender el incendio.

### Objetivo de volatilidad del 2% diario por posición

**Qué limita:** el tamaño de cada posición se ajusta para que las más
agitadas pesen menos.

**Si se quita:** una moneda muy volátil domina el resultado del bot y
acabas midiendo esa moneda, no la estrategia.

---

# PARTE 4 — Las reglas del método

Estas no son sobre estrategias. Son sobre cómo tomas decisiones.

### Preregistro: los criterios se fijan antes de medir

**Qué limita:** que muevas la portería después de ver dónde cayó el
balón.

**Si se quita:** siempre habrá un criterio que tu semilla favorita
cumple. Con suficientes criterios disponibles, todo pasa.

### Un examen por nombre, por implementación que funcione

**Qué limita:** que repitas un examen hasta que salga bien.

**Si se quita:** basta con reintentar. Diez intentos de la misma
estrategia con semillas distintas producen uno bueno por pura
aritmética.

**Lo que cambió hoy:** ahora un veredicto puede anularse si se demuestra
que un bug lo afectó. Eso es razonable —hoy se anularon trece por bugs
reales y documentados— pero es también la puerta más peligrosa del nuevo
charter. La protección es que anular exige una referencia a un bug que
exista en el repositorio, y que el listón nunca baja.

**Vigila esto:** si dentro de unos meses ves anulaciones cuya
justificación es vaga, o la misma estrategia anulada dos veces, la regla
se está usando mal. El propio charter dice que un patrón de anulaciones
es en sí mismo un hallazgo sobre la plomería.

### El registro solo crece, nunca se reescribe

**Qué limita:** ninguna fila se borra ni se edita. Los errores se
corrigen añadiendo, no tapando.

**Si se quita:** la historia se vuelve editable y no puedes confiar en
tu propio pasado.

### La noche de espera

**Qué limita:** ningún cambio de regla entra en vigor el mismo día que
se escribe.

**Si se quita:** este es el guardarraíl que reemplazó al trinquete, y
por tanto el más importante del charter nuevo. Tú mismo predijiste que
llegaría un momento en que querrías ir más rápido de lo que las reglas
permiten. La noche existe para ese momento: no te impide hacer nada,
solo te obliga a hacerlo mañana. Casi todas las malas decisiones de este
tipo se toman con prisa.

---

# PARTE 5 — La pregunta que hay que hacer siempre

Ante cualquier propuesta de cambio, incluida cualquiera mía:

1. **¿En qué dirección va?** Si hace más fácil que una estrategia llegue
   al dinero, necesita una semana y una explicación de a quién beneficia
   si está mal.

2. **¿Qué agujero tapaba la regla que se quita?** Si quien lo propone no
   lo sabe, no ha entendido la regla lo suficiente para cambiarla.

3. **¿Qué resultado demostraría que este cambio fue un error?** Si no
   hay respuesta, el cambio no es falsable y no debería entrar.

4. **¿Quién lo propone y qué revisó su trabajo?** Un modelo de lenguaje
   revisando código de otro modelo de lenguaje no es una revisión
   independiente. La revisión externa de esta semana lo dice de sí
   misma: encontrar errores en código escrito por un modelo con los
   mismos sesgos es evidencia débil de no compartir los que quedan.

---

*Este documento explica reglas; no las cambia. Si algo aquí contradice
a `docs/intraday_success_criteria.md` o a `docs/charter_v2.md`, mandan
esos y esto está mal escrito.*
