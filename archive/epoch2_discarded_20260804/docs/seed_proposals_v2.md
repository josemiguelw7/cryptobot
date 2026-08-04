# Propuestas de semillas — Ola 2 (Epoch 2)

ESTADO: **PROPUESTA, SIN FIRMAR.** Ninguna semilla de este documento
esta ARMED. Ninguna ha visto un examen. Este documento se escribe
ANTES de correr un solo backtest, por la misma razon que el anterior:
el pre-registro es lo unico que impide que despues se racionalice el
resultado. Charter s9.3 — la adopcion es decision del owner, no de
ingenieria.

## 1. Por que existe esta ola

Hallazgo del 2026-08-04, verificado sobre estado y logs en vivo:

- Escuadron de acciones: 8 de 10 bots sostenian posiciones IDENTICAS
  (mismas fracciones de TSLA y NVDA, mismo segundo de entrada).
- Log de decisiones del lanzamiento: casi todos los nombres del menu
  (GOOGL, META, AMZN, MSFT, SPY, QQQ) dieron señal de compra en casi
  todos los bots, y quedaron registrados como SKIP-cap.
- Escuadron cripto: mas disperso, pero 4 bots comparten una posicion
  ADA identica y hay dos pares gemelos.

Causa raiz — NO es un bug de ninguna estrategia:

1. `MAX_POS = 2` sobre un menu de 10 nombres fuerza concentracion.
2. El desempate cuando hay mas señales que cupos es UNA sola linea
   compartida por los diez bots: `edge_proxy`, la mediana movil de
   |retorno| sobre el horizonte declarado. Es signal-free por diseño
   (mide si el mercado se mueve lo suficiente para pagar la comision),
   pero como ordenador convierte diez opiniones distintas en una sola
   eleccion: el nombre que mas se mueve. En un menu de 10 megacaps eso
   es TSLA y NVDA, para todos, siempre.
3. Diez opiniones en la puerta, un solo portero.

Diagnostico secundario, tambien verificado: `strategies.py` solo recibe
CIERRES. Los archivos en disco (`data/candles/*_3600s.csv`,
`data/stocks/*_1h.csv`) contienen open, high, low, close Y volume. Dos
dimensiones completas de informacion estan en disco sin usarse. De ahi
que no exista —ni pueda existir con la plumeria actual— ninguna semilla
de patrones de velas ni de volumen.

## 2. Que se cambia en el motor (Epoch 2)

Los cambios de motor alteran el experimento. Se aplican SOLO al abrir
epoch 2, con reloj forward reiniciado, y quedan inertes para epoch 1
(defaults preservan el comportamiento actual byte-for-byte).

- **E2.1 Interfaz de barras completas.** Nuevo contrato opcional
  `step_bars(bars, ctx)` donde bars = [(ts,o,h,l,c,v), ...] de barras
  CERRADAS. El contrato `step(closes, ctx)` no se toca: las semillas
  adoptadas de epoch 1 son inmutables (s9.3) y siguen corriendo con el
  codigo identico.
- **E2.2 Desempate por conviccion propia.** El orden de entrada pasa a
  ser la conviccion de CADA semilla (`conviction()`), no `edge_proxy`.
  La PUERTA de costo (`edge >= 2x round-trip`, s4.3) NO se toca: sigue
  siendo el mismo filtro signal-free. Solo cambia el ORDEN, no el
  permiso.
- **E2.3 `MAX_POS` por roster.** Pasa a leerse del modulo de semillas.
  Propuesta: 4 para acciones (menu de 10), 3 para cripto (menu de 8).
  Numeros del owner, no mios — ver s6.
- **E2.4 Contexto cross-asset.** El motor inyecta en `ctx` las barras
  del proxy de mercado (BTC-USD / SPY) para las semillas que lo pidan.
- **E2.5 Contrato cross-sectional.** Nuevo `step_all(data, ctx) -> dict`
  para semillas que comparan nombres entre si en vez de contra su
  propio pasado.
- **E2.6 Medidor de diversidad.** Solapamiento diario % entre carteras
  de bots, logueado y expuesto en el portal. Si dos bots solapan 90%
  por semanas, se esta pagando dos veces por una sola opinion. Esto se
  puede desplegar en epoch 1 sin tocar el experimento: solo observa.

## 3. Roster propuesto — 11 semillas por clase de activo

Criterio de admision declarado ANTES de escribirlas: cada semilla debe
usar informacion que NINGUNA otra usa. `signal_correlation.py` ya midio
que 20 familias clasicas cargan ~6.24 opiniones independientes; añadir
variantes de media movil suma cero. Una variante mas de SMA no entra.

Prefijos permanentes: `h2_*` cripto, `s2_*` acciones. Un examen por
nombre, para siempre (ledger de multiple testing).

### Familia volumen — informacion nueva: cuanta gente aparecio
| nombre | idea | info que usa |
|---|---|---|
| `*_volconf` | breakout que solo cuenta con expansion de volumen | volume |
| `*_obv` | tendencia de on-balance-volume | volume + direccion |
| `*_dryup` | compresion de volumen seguida de expansion | volume |

### Familia velas — informacion nueva: la FORMA de la barra
| nombre | idea | info que usa |
|---|---|---|
| `*_engulf` | envolvente alcista, permitida solo en regimen alcista | o/h/l/c |
| `*_pin` | martillo / mecha inferior larga en retroceso | o/h/l/c |
| `*_inside` | barra interior (compresion) y ruptura | o/h/l/c |

Expectativa honesta declarada por adelantado: la literatura sobre
patrones de velas aislados en mercados liquidos es debil. Se espera
FAIL. Entran igual — como controles son valiosos, y el examen es quien
juzga, no yo.

### Familia transversal — informacion nueva: los OTROS nombres
| nombre | idea | info que usa |
|---|---|---|
| `*_rs` | fuerza relativa vs pares, pegajosa (sticky) | seccion cruzada |

Precedente que hay que declarar: MOM-ROT fallo. Era rotacion semanal
rapida sobre universo cambiante. Esta version es lenta, pegajosa y
sobre menu fijo. Puede que la distincion no importe; el examen lo dira.

### Familia cross-asset — informacion nueva: OTRO activo
| nombre | idea | info que usa |
|---|---|---|
| `*_regime` | operar solo si el proxy de mercado esta sano | BTC / SPY |

### Familia calendario — informacion nueva: la FECHA
| nombre | idea | info que usa |
|---|---|---|
| `*_cal` | turn-of-month (acciones) / fin de semana (cripto) | fecha |

### Familia comite — la idea original del owner: mezcla
| nombre | idea | info que usa |
|---|---|---|
| `*_vote` | entra si 2 de 3 familias no emparentadas coinciden | mixta |

### Familia reloj lento — informacion nueva: otra escala temporal
| nombre | idea | info que usa |
|---|---|---|
| `*_slow` | misma matematica sobre barras diarias resampleadas | escala |

`move_scale.py` dice que la direccion util es hacia ARRIBA: el
movimiento tipico de 1h (0.31%) no paga un round-trip de 1.60-2.60%;
el de varios dias si. NINGUNA semilla por debajo de 1h. Esa puerta no
se abre.

## 4. Costo de multiple testing — declarado, no escondido

22 examenes nuevos (11 x 2 clases) sobre 20 ya corridos = 42 nombres en
el ledger. Mas billetes de loteria = mas probabilidad de que algo pase
por azar. Consecuencias aceptadas por adelantado:

- El roster completo se congela en este documento ANTES del primer
  examen. Nada se añade despues de ver resultados.
- DSR (deflated Sharpe) se reporta con N=42 y gana peso en la revision
  del sabado. Sigue sin ser puerta en v1.0 del charter; el charter solo
  se endurece, y esto es una recomendacion de endurecerlo.
- Un PASS aislado en una familia donde las otras dos fallaron se trata
  como sospechoso, no como hallazgo.

## 5. Universo de acciones — sesgo de supervivencia

El menu actual (3 ETF + 7 megacaps) esta contaminado por seleccion
retrospectiva y el estandar ya lo pre-registro. Propuesta: universo
point-in-time por volumen en dolares a cada fecha, como
`data/pit_universe.py` hace en cripto. Sin esto, ampliar el menu de 10 a
50 nombres REPITE exactamente la trampa que convirtio +354% en -90%.

Ampliar el menu sin PIT esta explicitamente prohibido por este
documento.

## 6. Lo que NO decido yo

Numeros del owner, charter s2: `MAX_POS` por clase de activo, si epoch
2 reinicia el reloj forward (recomendacion: si, y ahora, con el
escuadron de acciones de 1 dia y el de cripto de 3 — jamas sera mas
barato), y la firma del roster. Recomiendo; no decido.

## 7. Estado de las semillas de epoch 1

Verificado 2026-08-04: las 20 semillas de epoch 1 corren como CONTROL.
0 de 10 PASS en acciones (el estandar predijo cero; megacaps 2024-2026
son cebo de supervivencia). 0 de 10 PASS en cripto (fee-stress, criterio
6). Bajo el charter ningun control es elegible para capital real jamas.
La liga entera es hoy una cohorte de baseline: honesta y util, sin un
solo candidato dentro.

## 8. Firma

Roster congelado arriba. `ARMED` no se toca hasta que exista firma del
owner aqui y un veredicto de examen por cada nombre.

    Owner: ______________________  Fecha: ____________
