# Exit autopsy — 12 closed round trips (2026-08-03 15:18 UTC)

Actual net P&L over these trips: **$-345.34**

Per-trade excursions (hourly closes, entry->actual exit):

| bot | pair | hold_h | MFE% | MAE% | net$ | exit |
|---|---|---|---|---|---|---|
| h_macd_12_26 | ADA-USD | 3.1 | -0.47 | -0.89 | -24.94 | signal |
| h_tsmom_72 | DOGE-USD | 1.0 | +0.03 | +0.03 | -16.12 | signal |
| h_trend_168 | XRP-USD | 9.8 | +0.67 | -0.41 | -20.32 | signal |
| h_tsmom_72 | DOGE-USD | 3.6 | -0.33 | -1.40 | -34.30 | signal |
| h_macd_12_26 | SOL-USD | 9.8 | +1.27 | -0.07 | -15.15 | signal |
| h_macd_12_26 | ETH-USD | 7.7 | +0.76 | -0.65 | -21.89 | signal |
| h_volbrk_24_96 | LTC-USD | 8.7 | -0.01 | -1.08 | -30.14 | signal |
| h_donch_48_24 | DOGE-USD | 9.7 | -0.07 | -1.58 | -35.38 | signal |
| h_volbrk_24_96 | DOGE-USD | 8.7 | +0.18 | -1.33 | -31.67 | signal |
| h_donch_48_24 | ADA-USD | 14.8 | -0.36 | -3.52 | -56.90 | signal |
| h_nearhi_168 | DOGE-USD | 15.8 | +0.81 | -1.44 | -36.12 | signal |
| h_tsmom_72 | DOGE-USD | 1.0 | -0.39 | -0.39 | -22.41 | signal |

Counterfactual rules (unfired rules fall back to the actual exit):

| rule | level | fired | net$ | vs actual |
|---|---|---|---|---|
| tp | 2% | 0/12 | -345.34 | +0.00 |
| tp | 3% | 0/12 | -345.34 | +0.00 |
| tp | 5% | 0/12 | -345.34 | +0.00 |
| tp | 10% | 0/12 | -345.34 | +0.00 |
| tp | 20% | 0/12 | -345.34 | +0.00 |
| tp | 30% | 0/12 | -345.34 | +0.00 |
| stop | 3% | 1/12 | -347.35 | -2.01 |
| stop | 5% | 0/12 | -345.34 | +0.00 |
| stop | 10% | 0/12 | -345.34 | +0.00 |
| trail | 3% | 1/12 | -347.35 | -2.01 |
| trail | 5% | 0/12 | -345.34 | +0.00 |
| trail | 8% | 0/12 | -345.34 | +0.00 |
| trail | 10% | 0/12 | -345.34 | +0.00 |

_Sample is 12 trades; treat every row as a hint._
