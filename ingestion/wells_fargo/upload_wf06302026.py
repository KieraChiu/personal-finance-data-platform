import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery


load_dotenv()

PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
DATASET_ID = os.getenv("BIGQUERY_DATASET", "finance_raw")
TABLE_ID = os.getenv(
    "WELLS_FARGO_TABLE",
    "wells_fargo_historical_06_30_2026",
)
CSV_PATH = Path(os.environ["WELLS_FARGO_CSV_PATH"])


def upload_wells_fargo_csv() -> None:
    """Upload a private Wells Fargo CSV into BigQuery."""

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV file was not found at: {CSV_PATH}"
        )

    client = bigquery.Client(project=PROJECT_ID)

    full_table_id = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        allow_quoted_newlines=True,
    )

    with CSV_PATH.open("rb") as csv_file:
        load_job = client.load_table_from_file(
            csv_file,
            full_table_id,
            job_config=job_config,
        )

    print("Uploading CSV to BigQuery...")

    load_job.result()

    table = client.get_table(full_table_id)

    print(
        f"Successfully loaded {table.num_rows} rows "
        f"into {full_table_id}"
    )


if __name__ == "__main__":
    upload_wells_fargo_csv()
