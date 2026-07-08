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
    "Purchased By",        
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
            str(row["purchased_by"]),  
        ]
    )

    return hashlib.sha256(source_value.encode("utf-8")).hexdigest()

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
            "Purchased By": "purchased_by"
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

    def clean_amount(value: str) -> Decimal:
        value = value.strip().replace("$", "").replace(",", "")
        if value.startswith("(") and value.endswith(")"):
            value = "-" + value[1:-1]
        return Decimal(value)

    dataframe["amount"] = dataframe["amount"].astype(str).map(clean_amount)

    dataframe["transaction_id"] = dataframe.apply(
        create_transaction_id,
        axis=1,
    )
    return dataframe