# Reading list — sources that profit from telling the truth

**Curated 2026-08-08.** Filter applied to everything here: does the
source ever publish its own failures? If not, it's marketing and it
didn't make the list. Ordered by value-per-hour for this project.

## Books

1. **Rob Carver — *Leveraged Trading* (2019).** Written for a retail
   trader with a small account. Position sizing, cost budgets, honest
   return expectations. The book version of our charter. Read first.
2. **Rob Carver — *Systematic Trading* (2015).** The framework behind
   pysystemtrade: continuous forecasts, instrument weights, the speed
   limit. Source for roadmap items 2.1–2.3.
3. **Meb Faber — *Global Asset Allocation*** (short; free PDF from his
   site). The published allocation rules behind Wave 4.
4. **Gary Antonacci — *Dual Momentum* (2014).** Source rule for
   `m4_dualmom`.
5. **Marcos López de Prado — *Advances in Financial Machine Learning*
   (2018).** Where our DSR and purged CV come from. Heavy, but chapters
   11–14 (backtesting dangers) are readable and foundational.

## Blogs

- **qoppac.blogspot.com** (Carver). A decade of real results published,
  including the bad years. The best ongoing read.
- **allocatesmartly.com/blog**. Published strategies tested against
  out-of-sample reality — our exam as journalism.
- **Quantocracy** (aggregator). Skim weekly; follow what recurs.

## Papers (free on SSRN)

- Bailey & López de Prado — **"The Deflated Sharpe Ratio"** (2014).
  The math behind criterion 10.
- Bailey, Borwein, López de Prado, Zhu — **"Pseudo-Mathematics and
  Financial Charlatanism"** (2014). Why the +354% backtest lied.
- Harvey & Liu — **"Evaluating Trading Strategies"** (2014). Why most
  published trading results are false.
- Faber — **"A Quantitative Approach to Tactical Asset Allocation"**
  (2007, updated). ~10 pages; the exact rule `m4_faber` tests; the
  most-downloaded paper on SSRN.

## Forums (with the minefield mapped)

- **QuantConnect forum** — best signal-to-noise; real code, real
  criticism.
- **r/algotrading** — read for the FAILURE stories. Treat every "my bot
  makes 5%/week" post as a specimen for the exam, not as advice.
- **Wilmott / QuantNet / Elite Trader** — professional, crusty, useful
  for math questions.
- Standing rule: anyone selling a course, signal group, or Telegram
  channel is monetizing the reader, not the market. The 215%-accuracy
  arithmetic is the vaccine.

## Podcasts

- **Top Traders Unplugged** — real systematic managers; Carver is a
  regular. The weekly "Systematic Investor" series discusses live
  results, wins and losses.
- **Flirting with Models** (Hoffstein) — allocation-heavy methodology;
  Wave 4 territory.
- **Chat With Traders** — mixed; the systematic episodes are honest
  about failure rates.

## Free courses

- **Quantopian lecture series** (archived) — 50+ notebooks, statistics
  to portfolio theory, written for retail algo traders. The platform's
  own death (300k users, ~no durable alpha found) is itself a data
  point supporting this project's null hypothesis.
- **QuantStart** — the backtesting-bias articles in the free tier.

## Meta-note for the weekly review

Most trading content is optimized to make trading feel learnable and
winnable, because that is what sells. This project's premise is the
opposite. When a new source appears, apply the filter at the top before
letting it influence a seed proposal — and cite the source in the
pre-registration so the influence is on the record.
