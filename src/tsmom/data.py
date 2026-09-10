"""Loaders for Bloomberg-format settlement price series and public factor data.

None of the functions here ship with data. Users point them at their own
locally licensed Bloomberg exports; see ``data/README.md`` for the expected
layout. No network access is required except for
:func:`download_fama_french_factors`, which is a convenience wrapper around
the public Kenneth French Data Library.
"""

from __future__ import annotations

import io
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "raw"

FAMA_FRENCH_FACTORS_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_Factors_CSV.zip"
)
FAMA_FRENCH_MOMENTUM_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Momentum_Factor_CSV.zip"
)


def _read_bloomberg_csv(path: Path) -> pd.DataFrame:
    """Read a Bloomberg-exported settlement/index CSV.

    Bloomberg's export format prefixes the data with a variable number of
    metadata rows (security, date range, currency, ...) before the actual
    ``Date, PX_...`` header. The header row is located dynamically rather
    than assuming a fixed number of rows to skip, since the metadata block
    length varies by security type.
    """
    with open(path, encoding="utf-8-sig") as f:
        lines = f.readlines()
    header_row = next(i for i, line in enumerate(lines) if line.startswith("Date"))
    df = pd.read_csv(path, skiprows=header_row, encoding="utf-8-sig")
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    return df.dropna(subset=["Date"]).sort_values("Date")


def load_settlement_series(path: Path, ticker: str) -> pd.DataFrame:
    """Load a single Bloomberg settlement-price CSV as a two-column frame."""
    df = _read_bloomberg_csv(path)
    df = df[["Date", "PX_SETTLE"]].rename(columns={"PX_SETTLE": ticker})
    return df.drop_duplicates(subset=["Date"], keep="last")


def load_settlement_universe(data_dir: Path, suffix: str) -> pd.DataFrame:
    """Merge all settlement-price CSVs in ``data_dir`` into one wide frame.

    Parameters
    ----------
    data_dir : directory containing one CSV per contract.
    suffix : filename suffix identifying the frequency, e.g.
        ``"_daily_settlement.csv"`` or ``"_monthly_settlement.csv"``. The
        ticker for each contract is the filename with this suffix removed.
    """
    files = sorted(Path(data_dir).glob(f"*{suffix}"))
    if not files:
        raise FileNotFoundError(f"No files matching '*{suffix}' found in {data_dir}")

    frames = [load_settlement_series(fp, fp.name[: -len(suffix)]) for fp in files]
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="Date", how="outer")
    return merged.sort_values("Date").set_index("Date")


def load_monthly_prices(data_dir: Path = DEFAULT_DATA_DIR / "monthly_settlement", start: str = "1990") -> pd.DataFrame:
    """Load the monthly settlement-price universe, one column per contract."""
    return load_settlement_universe(data_dir, "_monthly_settlement.csv").loc[start:]


def load_daily_prices(data_dir: Path = DEFAULT_DATA_DIR / "daily_settlement", start: str = "1990") -> pd.DataFrame:
    """Load the daily settlement-price universe, one column per contract."""
    return load_settlement_universe(data_dir, "_daily_settlement.csv").loc[start:]


def compute_returns(prices: pd.DataFrame, clip: float = 0.8) -> pd.DataFrame:
    """Simple percentage returns with contract-roll outliers set to missing.

    Observations with ``|return| >= clip`` are treated as data artefacts
    (commonly from futures roll mechanics) rather than genuine price moves.
    """
    returns = prices.pct_change(fill_method=None)
    return returns.where(returns.abs() < clip)


def load_bloomberg_index_monthly_return(path: Path) -> pd.Series:
    """Load a Bloomberg index/benchmark export and return its monthly return series.

    Used for the MSCI World (market factor), Bloomberg US Aggregate Bond
    (BOND), and S&P GSCI (GSCI) benchmark series.
    """
    df = _read_bloomberg_csv(path).sort_values("Date")
    ret = df["PX_LAST"].pct_change()
    out = pd.DataFrame({"Date": df["Date"], "value": ret}).dropna()
    out["Date"] = out["Date"].dt.to_period("M").dt.to_timestamp()
    return out.set_index("Date")["value"]


def load_fama_french_factors(path: Path) -> pd.DataFrame:
    """Load the Ken French ``F-F_Research_Data_Factors`` monthly CSV.

    The published file appends an annual-frequency data block after the
    monthly rows. Rather than hard-coding how many monthly rows precede it
    (which shifts whenever French updates the file), rows that don't parse
    as a ``YYYYMM`` monthly date are dropped automatically.
    """
    df = pd.read_csv(path, skiprows=4)
    df = df.rename(columns={df.columns[0]: "Date"})
    df["Date"] = pd.to_datetime(df["Date"], format="%Y%m", errors="coerce")
    df = df.dropna(subset=["Date"])
    cols = ["Mkt-RF", "SMB", "HML", "RF"]
    df[cols] = df[cols].apply(pd.to_numeric, errors="coerce") / 100
    return df.dropna(subset=cols).set_index("Date")[cols]


def load_momentum_factor(path: Path) -> pd.DataFrame:
    """Load the Ken French ``F-F_Momentum_Factor`` monthly CSV, renamed to UMD."""
    df = pd.read_csv(path, skiprows=13)
    df = df.rename(columns={df.columns[0]: "Date"})
    df["Date"] = pd.to_datetime(df["Date"], format="%Y%m", errors="coerce")
    df = df.dropna(subset=["Date"])
    df["UMD"] = pd.to_numeric(df["Mom"], errors="coerce") / 100
    return df.dropna(subset=["UMD"])[["Date", "UMD"]].set_index("Date")


def _download_and_extract_first_csv(url: str, dest: Path) -> Path:
    with urllib.request.urlopen(url) as response:
        archive_bytes = response.read()
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        member = archive.namelist()[0]
        dest.write_bytes(archive.read(member))
    return dest


def download_fama_french_factors(dest_dir: Path) -> tuple[Path, Path]:
    """Download the public Fama-French factor files into ``dest_dir``.

    Requires internet access; not used by the test suite or CI. Bloomberg
    market and benchmark data cannot be fetched this way and must be
    supplied by the user under their own Bloomberg licence.
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    factors_path = _download_and_extract_first_csv(
        FAMA_FRENCH_FACTORS_URL, dest_dir / "F-F_Research_Data_Factors.csv"
    )
    momentum_path = _download_and_extract_first_csv(
        FAMA_FRENCH_MOMENTUM_URL, dest_dir / "F-F_Momentum_Factor.csv"
    )
    return factors_path, momentum_path
