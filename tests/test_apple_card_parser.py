from pathlib import Path

import pandas as pd
import pytest

from ingestion.apple_card.parser import parse_apple_card_csv


def test_valid_csv_is_parsed():
    dataframe = parse_apple_card_csv(
        Path("sample_data/apple_card_sample.csv")
    )

    assert len(dataframe) == 3
    assert "transaction_date" in dataframe.columns
    assert "amount" in dataframe.columns
    assert dataframe["amount"].dtype.kind in {"f", "i"}


def test_missing_required_column_raises_error(tmp_path):
    invalid_file = tmp_path / "invalid.csv"

    pd.DataFrame(
        {
            "Transaction Date": ["06/01/2026"],
            "Description": ["Test Purchase"],
        }
    ).to_csv(invalid_file, index=False)

    with pytest.raises(ValueError, match="missing required columns"):
        parse_apple_card_csv(invalid_file)

def test_transaction_id_is_stable():
    first_dataframe = parse_apple_card_csv(
        Path("sample_data/apple_card_sample.csv")
    )

    second_dataframe = parse_apple_card_csv(
        Path("sample_data/apple_card_sample.csv")
    )

    assert first_dataframe["transaction_id"].tolist() == (
        second_dataframe["transaction_id"].tolist()
    )
