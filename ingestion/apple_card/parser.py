from pathlib import Path
from decimal import Decimal
import hashlib
import pandas as pd


REQUIRED_COLUMNS = {
    "Transaction Date",
    "Clearing Date",
    "Description",
    "Merchant",
    "Category",
    "Type",
    "Amount (USD)",
}

def create_transaction_id(row: pd.Series) -> str:
    """Create a stable ID from transaction fields."""

    source_value = "|".join(
        [
            str(row["transaction_date"]),
            str(row["clearing_date"]),
            str(row["description"]),
            str(row["merchant"]),
            str(row["amount"]),
        ]
    )

    return hashlib.sha256(source_value.encode("utf-8")).hexdigest()

def parse_apple_card_csv(file_path: Path) -> pd.DataFrame:
    dataframe = pd.read_csv(file_path)

    missing_columns = REQUIRED_COLUMNS - set(dataframe.columns)

    if missing_columns:
        raise ValueError(
            f"CSV is missing required columns: {sorted(missing_columns)}"
        )

    dataframe = dataframe.rename(
        columns={
            "Transaction Date": "transaction_date",
            "Clearing Date": "clearing_date",
            "Description": "description",
            "Merchant": "merchant",
            "Category": "category",
            "Type": "transaction_type",
            "Amount (USD)": "amount",
        }
    )

    dataframe["transaction_date"] = pd.to_datetime(
        dataframe["transaction_date"],
        errors="raise",
    ).dt.date

    dataframe["clearing_date"] = pd.to_datetime(
        dataframe["clearing_date"],
        errors="coerce",
    ).dt.date

    dataframe["amount"] = dataframe["amount"].astype(str).map(Decimal)

    dataframe["transaction_id"] = dataframe.apply(
        create_transaction_id,
        axis=1,
    )		
    return dataframe
