# Comité · agenda del 2026-10-25

_Generada sola. 30 minutos. Un punto por línea; las decisiones se escriben en `docs/decisions.md`._

## 1. Qué corrió esta semana
- P013 · POC v1 · **error** · neto -3934.44 · p 0.5804 · Topstep 12.0%
- P002 · BIG v1 · **superada** · neto -2120.06 · p 0.4086 · Topstep 0.0%
- P003 · ABS v1 · **superada** · neto 4641.16 · p 0.002 · Topstep 6.4%
- P004 · POC v1 · **superada** · neto -3934.44 · p 0.5794 · Topstep 12.0%
- P005 · ABS v2 · **superada** · neto 8868.72 · p 0.003 · Topstep 43.5%
- P006 · HVN v1 · **superada** · neto -30238.8 · p 0.5624 · Topstep 0.0%
- P007 · BIG v2 · **superada** · neto -72186.72 · p 0.8052 · Topstep 0.0%
- P008 · ORB v1 · **superada** · neto -15143.54 · p 0.5005 · Topstep 0.0%
- P009 · ORB v1 · **no_pasa** · neto -19063.54 · p 0.5455 · Topstep 0.0%
- P010 · BIG v2 · **no_pasa** · neto -102617.7 · p 0.95 · Topstep 0.0%
- P011 · HVN v1 · **no_pasa** · neto -87676.24 · p 0.999 · Topstep 0.0%
- P012 · ABS v2 · **revisar** · neto 7873.72 · p 0.005 · Topstep 41.4%
- P014 · ABS v1 · **revisar** · neto 4319.94 · p 0.003 · Topstep 3.7%
- P015 · BIG v1 · **no_pasa** · neto -2235.06 · p 0.4845 · Topstep 0.0%

## 2. Qué murió y por qué
- P013 · POC v1: umbral de orden grande mal calculado (percentil truncado y sobre todas las órdenes: 15 contratos). Ver strategies/v1_aclaraciones.json
- P009 · ORB v1: pierde con costos base; no gana a RAND (p=0.5455); no gana a RAND2 con las mismas salidas (p=0.5614); DSR 0.0 < 0.95 con 552 intentos; muere con costos al doble; pierde en 2024, 2025, 2026; pasa Topstep solo 0.0%
- P010 · BIG v2: pierde con costos base; no gana a RAND (p=0.95); no gana a RAND2 con las mismas salidas (p=0.9391); DSR 0.0 < 0.95 con 569 intentos; muere con costos al doble; pierde en 2024, 2025, 2026; pasa Topstep solo 0.0%
- P011 · HVN v1: pierde con costos base; no gana a RAND (p=0.999); no gana a RAND2 con las mismas salidas (p=1.0); DSR 0.0 < 0.95 con 584 intentos; muere con costos al doble; pierde en 2024, 2025, 2026; pasa Topstep solo 0.0%
- P015 · BIG v1: pierde con costos base; no gana a RAND (p=0.4845); no gana a RAND2 con las mismas salidas (p=0.4675); DSR 0.0 < 0.95 con 651 intentos; muere con costos al doble; pierde en 2024, 2025, 2026; pasa Topstep solo 0.0%

## 3. Qué está propuesto (decidir: aprobar / descartar / pedir más datos)
- [ ] **T3-SMT** Divergencia NQ vs ES (SMT) — Cuando NQ hace nuevo extremo y ES no (o al revés), el precio revierte.

## 4. Qué está aprobado y falta congelar
- E-HVN-FUERZA Estudio: qué hace poderoso a un HVN (base del indicador para ATAS) · falta: estudio registrado antes de correr (fases y umbrales); definición de 'HVN poderoso' congelada con huella y sello; chequeo cruzado en ES y YM sin abrir el examen de NQ; indicador C# para ATAS
- E-ACEPTACION-VA Estudio: aceptación vs rechazo en VAL, VAH y HVN · falta: 

## 5. Respuestas que faltan de Oscar
- 1. ¿Los niveles que tú miras son los del perfil de Nueva York del día anterior (09:30–16:00) o del día completo (incluida la noche)? Hoy usamos Nueva York.
- 2. Para una 'orden grande', ¿te importa más el tamaño absoluto (70–100 contratos) o lo raro que es ese tamaño para esa hora? La v1 usa percentil 99 de las 20 sesiones anteriores.
- 3. Cuando ves absorción, ¿cuánto tiempo esperas la confirmación antes de descartarla? La v1 espera 60 s.
- 4. ¿Operas después de las 11:30? La v1 cierra todo a las 11:45. Si tú operas la tarde, vale la pena una variante.
- 5. ¿Qué stop usas en puntos para un scalp normal y cuánto máximo aguantas en tu peor operación? Lo necesito para comparar con los 24 ticks (6 puntos) de BIG.

## 6. Muestras pendientes de marcar en ATAS (los ojos de Oscar)
- P003: 30 operaciones en la pestaña Pruebas › hoja completa
- P005: 30 operaciones en la pestaña Pruebas › hoja completa

## 7. Lo más fuerte del mapa (para decidir la siguiente tanda)
- Momentum primera → última media hora: -5.87 ticks a 30 min · mixto · 554 eventos
- Absorción: 7.98 ticks a 30 min · contraria · 5,784 eventos
- Divergencia de delta: -0.66 ticks a 30 min · a favor · 33,785 eventos

## 7b. Buzón de Oscar (notas nuevas)
- 2026-10-25_0230_has-probado-aceptacion.md
- 2026-10-24_1645_sugerencia-o-pedido-aparte-de-las-pruebas-que-estas-haciendo.md

## 8. Decisiones tomadas hoy
- 

_Al terminar: pasar lo decidido a `backlog.json` (estados) y a `docs/decisions.md`._
