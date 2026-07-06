from google.cloud import bigquery
import datetime
import json

PROJECT_ID = "finance-data-pipeline-500622"
BQ_DATASET = "finance_raw"
BQ_TABLE = "plaid_transactions"

bq_client = bigquery.Client(project=PROJECT_ID)
table_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"

test_row = [{
    "plaid_transaction_id": "test-123",
    "plaid_account_id": "acct-abc",
    "date": "2026-07-01",
    "authorized_date": "2026-07-01",
    "name": "Test Transaction",
    "amount": 12.34,
    "pending": False,
    "category": json.dumps(["Food and Drink"]),
    "loaded_at": datetime.datetime.utcnow().isoformat(),
}]

errors = bq_client.insert_rows_json(table_id, test_row)
print(errors)
