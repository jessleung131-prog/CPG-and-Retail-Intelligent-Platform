"""
Chronological train / validation / test splitter.

All time-series and modeling workflows MUST use this module.
Random shuffling is explicitly disallowed to prevent data leakage.
"""
from dataclasses import dataclass
import pandas as pd


@dataclass
class ChronologicalSplit:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame
    train_end: str
    val_end: str
    test_end: str

    def summary(self) -> str:
        return (
            f"Train:      {len(self.train):>7,} rows  (up to {self.train_end})\n"
            f"Validation: {len(self.validation):>7,} rows  ({self.train_end} → {self.val_end})\n"
            f"Test:       {len(self.test):>7,} rows  ({self.val_end} → {self.test_end})"
        )


def split(
    df: pd.DataFrame,
    date_col: str,
    train_frac: float = 0.70,
    val_frac: float = 0.15,
) -> ChronologicalSplit:
    """
    Split a time-ordered DataFrame into train / val / test by date.

    Splits are determined by fractional position in the sorted date range,
    not by row count, ensuring clean temporal boundaries.

    Args:
        df:          DataFrame with a date column.
        date_col:    Name of the date/datetime column.
        train_frac:  Fraction of time range assigned to training (default 0.70).
        val_frac:    Fraction assigned to validation (default 0.15).
                     Remainder becomes test.

    Returns:
        ChronologicalSplit with .train, .validation, .test DataFrames.
    """
    if train_frac + val_frac >= 1.0:
        raise ValueError("train_frac + val_frac must be < 1.0")

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col).reset_index(drop=True)

    min_date = df[date_col].min()
    max_date = df[date_col].max()
    total_days = (max_date - min_date).days

    train_cutoff = min_date + pd.Timedelta(days=int(total_days * train_frac))
    val_cutoff   = min_date + pd.Timedelta(days=int(total_days * (train_frac + val_frac)))

    train = df[df[date_col] <= train_cutoff]
    val   = df[(df[date_col] > train_cutoff) & (df[date_col] <= val_cutoff)]
    test  = df[df[date_col] > val_cutoff]

    return ChronologicalSplit(
        train=train.reset_index(drop=True),
        validation=val.reset_index(drop=True),
        test=test.reset_index(drop=True),
        train_end=str(train_cutoff.date()),
        val_end=str(val_cutoff.date()),
        test_end=str(max_date.date()),
    )
