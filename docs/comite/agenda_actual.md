# Comité · agenda del 2026-10-24

_Generada sola. 30 minutos. Un punto por línea; las decisiones se escriben en `docs/decisions.md`._

## 1. Qué corrió esta semana
- P013 · BIG v1 · **error** · neto -13718.04 · p 0.1419 · Topstep 0.0%
- P002 · BIG v1 · **no_pasa** · neto -2120.06 · p 0.4086 · Topstep 0.0%
- P003 · ABS v1 · **no_pasa** · neto 4641.16 · p 0.002 · Topstep 6.4%
- P004 · POC v1 · **no_pasa** · neto -3934.44 · p 0.5794 · Topstep 12.0%
- P005 · ABS v2 · **revisar** · neto 8868.72 · p 0.003 · Topstep 43.5%
- P006 · HVN v1 · **no_pasa** · neto -30238.8 · p 0.5624 · Topstep 0.0%

## 2. Qué murió y por qué
- P013 · BIG v1: umbral de orden grande mal calculado (percentil truncado y sobre todas las órdenes: 15 contratos). Ver strategies/v1_aclaraciones.json
- P002 · BIG v1: pierde con costos base; no gana a RAND (p=0.4086); muere con costos al doble; pierde en 2024, 2025, 2026; pasa Topstep solo 0.0%
- P003 · ABS v1: pierde en 2025 (−$405); pasa Topstep solo 6.4% (128 operaciones en 576 sesiones no alcanzan la meta); 67.7% de la ganancia viene de 5 días
- P004 · POC v1: pierde con costos base; no gana a RAND (p=0.5794); muere con costos al doble; pierde en 2024, 2026; pasa Topstep solo 12.0%
- P006 · HVN v1: pierde con costos base; no gana a RAND (p=0.5624); muere con costos al doble; pierde en 2024, 2025, 2026; pasa Topstep solo 0.0%

## 3. Qué está propuesto (decidir: aprobar / descartar / pedir más datos)
- [ ] **T3-BIG2** BIG v2: seguir a la orden grande con entrada inmediata y objetivo corto — Mapa v3 (precios operables): después de una orden agresiva ≥ p99 que barre ≥ 2 niveles, el precio SIGUE +12 ticks a 5, 15 y 30 min (p bruto 0.0004, estable 2024
- [ ] **T2-ABS-EARLY** ABS con entrada temprana — ABS v1 gana a RAND (p 0.002) y el placebo desplazado 5 min antes gana más: entrar al detectar la absorción (sin esperar la confirmación) debería ganar más con e
- [ ] **T2-ABS-HOURS** ABS v1 en toda la sesión de Nueva York — Las mismas reglas de ABS v1 de 09:30 a 15:30 (cierre 15:45) producen suficientes operaciones para pasar Topstep.
- [ ] **T3-SMT** Divergencia NQ vs ES (SMT) — Cuando NQ hace nuevo extremo y ES no (o al revés), el precio revierte.

## 4. Qué está aprobado y falta congelar

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

## 8. Decisiones tomadas hoy
- 

_Al terminar: pasar lo decidido a `backlog.json` (estados) y a `docs/decisions.md`._
