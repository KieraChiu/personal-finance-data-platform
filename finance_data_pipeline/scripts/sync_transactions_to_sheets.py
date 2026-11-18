from google.cloud import bigquery
import gspread
from google.oauth2 import service_account
import pandas as pd
import google.auth
from google.auth import impersonated_credentials
from google.auth.transport.requests import AuthorizedSession
from google.cloud import bigquery

PROJECT_ID   = "finance-data-pipeline-500622"
SHEET_NAME   = "finance-data-pipeline"   
WORKSHEET    = "category_overrides"
SERVICE_ACCOUNT = "dbt-finance@finance-data-pipeline-500622.iam.gserviceaccount.com"
DATA_COLS = [
    "transaction_id", "transaction_date", "merchant_description",
    "amount", "source_account", "raw_category"
]

def get_clients():
    source_credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    impersonated = impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=SERVICE_ACCOUNT,
        target_scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    
    gc = gspread.Client(auth=impersonated)
    gc.session = AuthorizedSession(impersonated)
    bq = bigquery.Client(project=PROJECT_ID)
    sheet = gc.open(SHEET_NAME).worksheet(WORKSHEET)
    return bq, sheet

def fetch_transactions(bq):
    query = """
        SELECT
            transaction_id,
            CAST(transaction_date AS STRING)            AS transaction_date,
            merchant_description,
            CAST(amount_normalized AS STRING)           AS amount,
            source_account,
            raw_category
        FROM (
            SELECT transaction_id, transaction_date, merchant_description,
                   amount                               AS amount_normalized,
                   CAST(NULL AS STRING)                 AS raw_category,
                   source_account
            FROM `finance-data-pipeline-500622.finance_core_staging.stg_wells_fargo`
            WHERE transaction_date < '2026-03-03'

            UNION ALL

            SELECT transaction_id, transaction_date, merchant_description,
                   amount * -1                          AS amount_normalized,
                   apple_category                       AS raw_category,
                   source_account
            FROM `finance-data-pipeline-500622.finance_core_staging.stg_apple_card`
            WHERE purchased_by = 'Kiera Chiu'

            UNION ALL

            SELECT transaction_id, transaction_date, merchant_description,
                   amount                               AS amount_normalized,
                   COALESCE(
                       JSON_VALUE(plaid_category, '$[2]'),
                       JSON_VALUE(plaid_category, '$[1]'),
                       JSON_VALUE(plaid_category, '$[0]')
                   )                                    AS raw_category,
                   source_account
            FROM `finance-data-pipeline-500622.finance_core_staging.stg_plaid`
        )
        ORDER BY transaction_date DESC
    """
    return bq.query(query).to_dataframe()

def existing_ids(sheet):
    rows = sheet.get_all_values()
    if len(rows) <= 1:          
        return set()
    return {row[0] for row in rows[1:] if row[0]}   

def sync():
    bq, sheet = get_clients()

    print("Fetching transactions from BigQuery...")
    df = fetch_transactions(bq)

    print("Reading existing sheet rows...")
    seen = existing_ids(sheet)

    new_rows = df[~df["transaction_id"].isin(seen)]

    if new_rows.empty:
        print("No new transactions to sync.")
        return

   
    new_rows = new_rows[DATA_COLS].fillna("")

    rows_to_append = new_rows.values.tolist()
    sheet.append_rows(rows_to_append, value_input_option="RAW")
    print(f"Synced {len(rows_to_append)} new transactions to sheet.")
if __name__ == "__main__":
    bq, sheet = get_clients()
    if not sheet.get_all_values():
        headers = DATA_COLS + ["override_category", "notes"]
        sheet.append_row(headers)
        print("Created header row.")
    sync()