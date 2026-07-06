import functions_framework
from google.cloud import secretmanager
from google.cloud import bigquery
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_sync_request import TransactionsSyncRequest
import json
import datetime

PROJECT_ID = "finance-data-pipeline-500622"
BQ_DATASET = "finance_raw"
BQ_TABLE = "plaid_transactions"   # <-- fixed to match your actual table name

def get_secret(secret_id, project_id=PROJECT_ID):
    """Pull a secret's latest version from Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def get_plaid_client():
    """Build an authenticated Plaid API client."""
    plaid_client_id = get_secret("plaid-client-id")
    plaid_secret = get_secret("plaid-secret")

    configuration = plaid.Configuration(
        host=plaid.Environment.Production,
        api_key={
            "clientId": plaid_client_id,
            "secret": plaid_secret,
        },
    )
    api_client = plaid.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)


def fetch_transactions():
    """Call Plaid's /transactions/sync endpoint."""
    client = get_plaid_client()
    access_token = get_secret("plaid-access-token")

    request = TransactionsSyncRequest(access_token=access_token)
    response = client.transactions_sync(request)

    return response.to_dict()["added"]  # list of new transactions


def write_to_bigquery(transactions):
    """Insert transaction rows into BigQuery."""
    if not transactions:
        print("No new transactions to write.")
        return

    bq_client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"

    rows_to_insert = []
    for txn in transactions:
        rows_to_insert.append({
            "plaid_transaction_id": txn.get("transaction_id"),
            "plaid_account_id": txn.get("account_id"),
            "date": str(txn.get("date")),
            "authorized_date": str(txn.get("authorized_date")) if txn.get("authorized_date") else None,
            "name": txn.get("name"),
            "amount": txn.get("amount"),
            "pending": txn.get("pending"),
            "category": json.dumps(txn.get("category")),
            "loaded_at": datetime.datetime.utcnow().isoformat(),
        })

    errors = bq_client.insert_rows_json(table_id, rows_to_insert)
    if errors:
        print(f"BigQuery insert errors: {errors}")
    else:
        print(f"Inserted {len(rows_to_insert)} rows into {table_id}")


@functions_framework.http
def main(request):
    """HTTP-triggered entry point for Cloud Functions."""
    try:
        transactions = fetch_transactions()
        write_to_bigquery(transactions)
        return {"status": "success", "rows_written": len(transactions)}, 200
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}, 500