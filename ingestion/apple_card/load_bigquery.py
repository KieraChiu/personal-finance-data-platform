import os
from pathlib import Path

from google.cloud import bigquery

from ingestion.apple_card.parser import parse_apple_card_csv


def load_apple_card_csv(
    file_path: Path,
    project_id: str,
    dataset_id: str = "finance_raw",
    table_name: str = "apple_card_transactions",
) -> None:
    """Load new Apple Card transactions into BigQuery without duplicates."""

    dataframe = parse_apple_card_csv(file_path)

    client = bigquery.Client(project=project_id)

    target_table = f"{project_id}.{dataset_id}.{table_name}"
    staging_table = f"{project_id}.{dataset_id}.{table_name}_staging"

    schema = [
        bigquery.SchemaField("transaction_date", "DATE"),
        bigquery.SchemaField("clearing_date", "DATE"),
        bigquery.SchemaField("description", "STRING"),
        bigquery.SchemaField("merchant", "STRING"),
        bigquery.SchemaField("category", "STRING"),
        bigquery.SchemaField("transaction_type", "STRING"),
        bigquery.SchemaField("amount", "NUMERIC"),
        bigquery.SchemaField("transaction_id", "STRING"),
    ]

    # Replace staging data on every run.
    staging_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = client.load_table_from_dataframe(
        dataframe,
        staging_table,
        job_config=staging_config,
    )
    load_job.result()

    merge_query = f"""
        MERGE `{target_table}` AS target
        USING `{staging_table}` AS source
        ON target.transaction_id = source.transaction_id

        WHEN NOT MATCHED THEN
          INSERT (
            transaction_date,
            clearing_date,
            description,
            merchant,
            category,
            transaction_type,
            amount,
            transaction_id
          )
          VALUES (
            source.transaction_date,
            source.clearing_date,
            source.description,
            source.merchant,
            source.category,
            source.transaction_type,
            source.amount,
            source.transaction_id
          )
    """

    merge_job = client.query(merge_query)
    merge_job.result()

    print(f"Processed {len(dataframe)} rows into {target_table}")


if __name__ == "__main__":
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT environment variable is not set."
        )

    load_apple_card_csv(
        Path("sample_data/apple_card_sample.csv"),
        project_id,
    )


