# Data

No market data is included in this repository. The futures and benchmark
series used in the research are sourced from Bloomberg, whose terms do not
permit redistribution, so raw data files are intentionally excluded from
Git history (see `.gitignore`). This directory documents the expected
schema for anyone reproducing the analysis with their own Bloomberg
licence.

## Market data used in the dissertation

Bloomberg generic first-continuous-futures settlement prices for 19
contracts spanning four asset classes, January 1990 - December 2025:

| Asset class | Contracts |
|---|---|
| Commodity futures (8) | Copper, Corn, Crude Oil, Gold, Natural Gas, Silver, Soybeans, Wheat |
| Equity index futures (4) | EURO STOXX 50, FTSE 100, Nikkei 225, S&P 500 |
| Government bond futures (3) | US 10-Year Note, Euro-Bund, Japan 10-Year Bond |
| Currency futures (4) | AUD/USD, EUR/USD, GBP/USD, JPY/USD |

Two frequencies are used for different purposes:

- **Daily** settlement prices, used only to estimate ex-ante volatility
  (EWMA of squared daily returns).
- **Monthly** settlement prices, used for the momentum signal and all
  strategy/benchmark returns.

Three further Bloomberg-sourced benchmark series are used as regression
controls: the MSCI World index (market factor), the Bloomberg US Aggregate
Bond index (`LBUSTRUU`, BOND factor), and the S&P GSCI Total Return index
(`SPGSCITR`, GSCI factor).

## Expected local layout

`src/tsmom/data.py` reads from this structure by default (override with
your own paths as function arguments):

```
data/raw/
├── monthly_settlement/
│   ├── AD1_Curncy_monthly_settlement.csv
│   ├── ES1_monthly_settlement.csv
│   └── ...                              (one file per contract)
├── daily_settlement/
│   ├── AD1_Curncy_daily_settlement.csv
│   ├── ES1_daily_settlement.csv
│   └── ...
└── benchmarks/
    ├── LBUSTRUU_monthly_TR.csv
    ├── MSCI_INDEX.csv
    └── SPGSCITR_monthly_TR.csv
```

Each settlement CSV is expected in the standard Bloomberg Excel/API export
format: a short metadata block (security, date range, currency) followed
by a `Date, PX_SETTLE` (or `PX_LAST` for the benchmark indices) table. The
loader locates the header row dynamically, so the exact number of metadata
rows does not matter.

`data/raw/` is gitignored in full — nothing placed there will be committed.

## Public factor data

`SMB`, `HML`, `RF`, and the momentum factor (`UMD`) come from the public
Kenneth French Data Library and carry no redistribution restriction.
Rather than shipping local copies, `src/tsmom/data.py` provides
`download_fama_french_factors(dest_dir)`, which fetches them directly from
Dartmouth's public FTP at run time (requires internet access; not used by
the test suite or CI). Point `load_fama_french_factors` /
`load_momentum_factor` at the downloaded files, or at your own copies
placed under `data/raw/benchmarks/`.

## Synthetic data

The test suite (`tests/`) uses seeded synthetic random data and small
hand-built fixtures — never real market data — so it runs without any
Bloomberg licence. Any synthetic series in this repository is labelled as
such and is not used to support a research claim.
