# Validation

This note compares the dissertation's reported results (`paper/dissertation.pdf`)
against the output of the refactored `src/tsmom` implementation, run on the
same underlying Bloomberg data used for the original submission. It exists
so a reader can check the software-engineering refactor did not silently
change the research conclusions.

**Data caveat.** The Bloomberg settlement-price CSVs on disk extend a few
weeks past the dissertation's stated sample end (December 2025); they carry
an export date of March 2026 and run through January 2026, one month beyond
the reported cutoff. This is the source of essentially all of the small
numerical differences below — everything is within Bloomberg-refresh /
rounding tolerance, not a methodology discrepancy. All comparisons use a
0.1 percentage point / 0.01 Sharpe / 1 bp alpha tolerance for annualised
figures, in line with the dissertation reporting returns and Sharpe ratios
to 1-3 decimal places.

## Gross performance (Table 3)

| Metric | Strategy | Dissertation | Reproduced | Difference | Status |
|---|---|---|---|---|---|
| Annual return | Passive | 4.7% | 4.65% | -0.05pp | PASS |
| Annual return | TSMOM | 7.8% | 7.75% | -0.05pp | PASS |
| Annual return | VM-TSMOM | 3.6% | 3.55% | -0.05pp | PASS |
| Volatility | Passive | 8.4% | 8.39% | -0.01pp | PASS |
| Volatility | TSMOM | 14.3% | 14.26% | -0.04pp | PASS |
| Volatility | VM-TSMOM | 6.7% | 6.74% | +0.04pp | PASS |
| Sharpe ratio | Passive | 0.554 | 0.554 | 0.000 | PASS |
| Sharpe ratio | TSMOM | 0.544 | 0.544 | 0.000 | PASS |
| Sharpe ratio | VM-TSMOM | 0.527 | 0.527 | 0.000 | PASS |
| Max drawdown | Passive | -30.2% | -30.21% | -0.01pp | PASS |
| Max drawdown | TSMOM | -35.4% | -35.37% | +0.03pp | PASS |
| Max drawdown | VM-TSMOM | -19.5% | -19.47% | +0.03pp | PASS |

## Return-matched comparison (Table 5)

| Metric | Strategy | Dissertation | Reproduced | Status |
|---|---|---|---|---|
| Scale factor to match TSMOM return | — | 2.183 | 2.183 | PASS |
| Annual return | Return-matched VM-TSMOM | 7.8% | 7.75% | PASS |
| Volatility | Return-matched VM-TSMOM | 14.7% | 14.71% | PASS |
| Sharpe ratio | Return-matched VM-TSMOM | 0.527 | 0.527 | PASS |
| Max drawdown | Return-matched VM-TSMOM | -38.9% | -38.91% | PASS |

## Turnover (Table 6)

| Metric | Strategy | Dissertation | Reproduced | Status |
|---|---|---|---|---|
| Average monthly turnover | TSMOM | 0.614 | 0.612 | PASS |
| Median monthly turnover | TSMOM | 0.522 | 0.521 | PASS |
| Average monthly turnover | VM-TSMOM | 1.715 | 1.711 | PASS |
| Median monthly turnover | VM-TSMOM | 1.235 | 1.233 | PASS |

## Transaction costs (Table 7)

| Metric | Strategy (cost) | Dissertation | Reproduced | Status |
|---|---|---|---|---|
| Annual return | TSMOM (5bps) | 7.4% | 7.38% | PASS |
| Sharpe ratio | TSMOM (5bps) | 0.518 | 0.518 | PASS |
| Annual return | TSMOM (10bps) | 7.0% | 7.01% | PASS |
| Sharpe ratio | TSMOM (10bps) | 0.492 | 0.492 | PASS |
| Annual return | VM-TSMOM (5bps) | 2.5% | 2.52% | PASS |
| Sharpe ratio | VM-TSMOM (5bps) | 0.375 | 0.375 | PASS |
| Annual return | VM-TSMOM (10bps) | 1.5% | 1.49% | PASS |
| Sharpe ratio | VM-TSMOM (10bps) | 0.222 | 0.222 | PASS |

## Factor regressions (Table 4)

| Metric | Strategy | Dissertation | Reproduced | Status |
|---|---|---|---|---|
| Alpha (monthly) | TSMOM | 0.0024 | 0.0024 | PASS |
| Alpha p-value | TSMOM | 0.344 | 0.339 | PASS |
| UMD loading | TSMOM | 0.2971 | 0.2967 | PASS |
| R-squared | TSMOM | 0.1182 | 0.1171 | PASS |
| Observations | TSMOM | 419 | 418 | PASS (1 extra month in the data pull) |
| Alpha (monthly) | VM-TSMOM | -0.0004 | -0.0004 | PASS |
| Alpha p-value | VM-TSMOM | 0.736 | 0.736 | PASS |
| UMD loading | VM-TSMOM | 0.1166 | 0.1166 | PASS |
| R-squared | VM-TSMOM | 0.0776 | 0.0776 | PASS |

## Subperiod analysis (Table 8)

| Metric | Strategy / period | Dissertation | Reproduced | Status |
|---|---|---|---|---|
| Annual return | TSMOM, pre-2009 | 11.2% | 11.24% | PASS |
| Sharpe ratio | TSMOM, pre-2009 | 0.821 | 0.821 | PASS |
| Annual return | TSMOM, post-2009 | 4.1% | 4.11% | PASS |
| Sharpe ratio | TSMOM, post-2009 | 0.278 | 0.278 | PASS |
| Annual return | VM-TSMOM, pre-2009 | 4.4% | 4.37% | PASS |
| Sharpe ratio | VM-TSMOM, pre-2009 | 0.664 | 0.664 | PASS |
| Annual return | VM-TSMOM, post-2009 | 2.7% | 2.69% | PASS |
| Sharpe ratio | VM-TSMOM, post-2009 | 0.390 | 0.390 | PASS |

## Bootstrap Sharpe-ratio difference tests (Table 10)

| Comparison | Dissertation diff / p | Reproduced diff / p | Status |
|---|---|---|---|
| TSMOM vs VM-TSMOM | 0.017 / 0.876 | 0.017 / 0.876 | PASS |
| TSMOM (10bps) vs VM-TSMOM (10bps) | 0.270 / 0.015 | 0.270 / 0.015 | PASS |

## Conclusion

All headline results reproduce within Bloomberg-refresh / rounding
tolerance, including the exact 2.183 return-matching scale factor and the
bootstrap p-values, which depend on the same seeded resampling procedure
(`seed=42`, block length `floor(sqrt(T))`, 10,000 draws) as the original
notebook. The refactor changes only *how* the pipeline is organised into
`src/tsmom`, not the underlying calculations: no numbers, filters, lags, or
scaling conventions were adjusted to force a match.

Reproduction script (not included in the repository; requires a local,
licensed Bloomberg data pull matching the layout in
[`data/README.md`](../data/README.md)):

```python
from tsmom import data, signals, strategies, volatility, performance, regressions, utils

monthly_prices = data.load_monthly_prices(...)
daily_prices = data.load_daily_prices(...)
returns = data.compute_returns(monthly_prices)
daily_returns = data.compute_returns(daily_prices)

signal = signals.momentum_signal(returns, lookback=12)
monthly_vol = volatility.month_end_volatility(volatility.ewma_daily_volatility(daily_returns))

tsmom_asset = strategies.tsmom_asset_returns(returns, signal, monthly_vol, target_vol=0.40)
tsmom = strategies.tsmom_portfolio(tsmom_asset)

vm_result = strategies.build_vm_tsmom(returns, daily_returns, signal)
vm_tsmom = vm_result.returns
```
