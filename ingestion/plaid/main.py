import functions_framework
from google.cloud import secretmanager
from google.cloud import bigquery
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_sync_request import TransactionsSyncRequest
import datetime
import hashlib
import json

PROJECT_ID = "finance-data-pipeline-500622"
BQ_DATASET = "finance_raw"
BQ_TABLE = "plaid_transactions"
SYNC_STATE_TABLE = f"{PROJECT_ID}.finance_metadata.plaid_sync_state"

# Plaid asks clients to restart the whole pagination loop from the original
# cursor when this happens.
MUTATION_DURING_PAGINATION = "TRANSACTIONS_SYNC_MUTATION_DURING_PAGINATION"
MAX_PAGINATION_RESTARTS = 3


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


def item_key(access_token):
    """Stable, non-secret key for the sync-state row of this Plaid item."""
    return hashlib.sha256(access_token.encode("utf-8")).hexdigest()


def load_cursor(bq_client, key):
    """Return the cursor saved by the last successful sync, or None."""
    query = f"""
        SELECT cursor
        FROM `{SYNC_STATE_TABLE}`
        WHERE item_id_hash = @key AND sync_status = 'success'
        ORDER BY last_sync_completed_at DESC
        LIMIT 1
    """
    job = bq_client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("key", "STRING", key)]
        ),
    )
    rows = list(job.result())
    return rows[0]["cursor"] if rows else None


def save_sync_state(bq_client, key, started_at, status, cursor=None, error=None):
    """Upsert the sync-state row. The cursor is only replaced on success."""
    query = f"""
        MERGE `{SYNC_STATE_TABLE}` t
        USING (SELECT @key AS item_id_hash) s
        ON t.item_id_hash = s.item_id_hash
        WHEN MATCHED THEN UPDATE SET
            cursor = IF(@status = 'success', @cursor, t.cursor),
            last_sync_started_at = @started_at,
            last_sync_completed_at = IF(@status = 'success', CURRENT_TIMESTAMP(), t.last_sync_completed_at),
            sync_status = @status,
            error_message = @error
        WHEN NOT MATCHED THEN INSERT
            (item_id_hash, cursor, last_sync_started_at, last_sync_completed_at, sync_status, error_message)
        VALUES (
            @key,
            IF(@status = 'success', @cursor, NULL),
            @started_at,
            IF(@status = 'success', CURRENT_TIMESTAMP(), NULL),
            @status,
            @error
        )
    """
    params = [
        bigquery.ScalarQueryParameter("key", "STRING", key),
        bigquery.ScalarQueryParameter("cursor", "STRING", cursor),
        bigquery.ScalarQueryParameter("started_at", "TIMESTAMP", started_at),
        bigquery.ScalarQueryParameter("status", "STRING", status),
        bigquery.ScalarQueryParameter("error", "STRING", error),
    ]
    bq_client.query(
        query, job_config=bigquery.QueryJobConfig(query_parameters=params)
    ).result()


def fetch_transactions(client, access_token, cursor):
    """Page through /transactions/sync starting at `cursor`.

    Returns (added, modified, removed, next_cursor). Only changes since
    `cursor` are returned, so re-running does not re-download history.
    """
    for _attempt in range(MAX_PAGINATION_RESTARTS):
        added, modified, removed = [], [], []
        page_cursor = cursor
        try:
            while True:
                kwargs = {"access_token": access_token}
                if page_cursor:
                    kwargs["cursor"] = page_cursor
                response = client.transactions_sync(
                    TransactionsSyncRequest(**kwargs)
                ).to_dict()

                added.extend(response["added"])
                modified.extend(response["modified"])
                removed.extend(response["removed"])
                page_cursor = response["next_cursor"]

                if not response["has_more"]:
                    return added, modified, removed, page_cursor
        except plaid.ApiException as e:
            body = json.loads(e.body) if e.body else {}
            if body.get("error_code") != MUTATION_DURING_PAGINATION:
                raise
            print("Plaid data changed during pagination; restarting from saved cursor.")
    raise RuntimeError("Plaid sync kept changing during pagination; try again later.")


def transaction_row(txn, loaded_at):
    return {
        "plaid_transaction_id": txn.get("transaction_id"),
        "plaid_account_id": txn.get("account_id"),
        "date": str(txn.get("date")),
        "authorized_date": str(txn.get("authorized_date")) if txn.get("authorized_date") else None,
        "name": txn.get("name"),
        "amount": txn.get("amount"),
        "pending": txn.get("pending"),
        "pending_transaction_id": txn.get("pending_transaction_id"),
        "category": json.dumps(txn.get("category")),
        "is_removed": False,
        "loaded_at": loaded_at,
    }


def removed_row(txn, loaded_at):
    """Tombstone row: marks a transaction Plaid has deleted (e.g. a pending
    transaction that has since posted under a new transaction_id)."""
    return {
        "plaid_transaction_id": txn.get("transaction_id"),
        "plaid_account_id": txn.get("account_id"),
        "is_removed": True,
        "loaded_at": loaded_at,
    }


def write_to_bigquery(bq_client, added, modified, removed, cursor):
    """Append changes to the raw table. The table stays append-only; dbt
    (stg_plaid) keeps the latest version of each transaction and drops
    removed ones."""
    loaded_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rows = [transaction_row(t, loaded_at) for t in added + modified]
    rows += [removed_row(t, loaded_at) for t in removed]
    if not rows:
        print("No transaction changes to write.")
        return 0

    table_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
    # row_ids let BigQuery drop duplicate rows if this same batch is retried.
    row_ids = [
        f"{r['plaid_transaction_id']}:{'removed' if r['is_removed'] else 'upsert'}:{cursor}"
        for r in rows
    ]
    errors = bq_client.insert_rows_json(table_id, rows, row_ids=row_ids)
    if errors:
        # Raise so the cursor is NOT advanced; the next run retries this batch.
        raise RuntimeError(f"BigQuery insert errors: {errors}")
    print(
        f"Wrote {len(added)} added, {len(modified)} modified, "
        f"{len(removed)} removed rows into {table_id}"
    )
    return len(rows)


@functions_framework.http
def main(request):
    """HTTP-triggered entry point for Cloud Functions."""
    started_at = datetime.datetime.now(datetime.timezone.utc)
    bq_client = bigquery.Client(project=PROJECT_ID)
    key = None
    try:
        access_token = get_secret("plaid-access-token")
        key = item_key(access_token)
        cursor = load_cursor(bq_client, key)

        added, modified, removed, next_cursor = fetch_transactions(
            get_plaid_client(), access_token, cursor
        )
        rows_written = write_to_bigquery(bq_client, added, modified, removed, next_cursor)

        # Only advance the cursor after the rows are safely in BigQuery.
        save_sync_state(bq_client, key, started_at, "success", cursor=next_cursor)
        return {"status": "success", "rows_written": rows_written}, 200
    except Exception as e:
        print(f"Error: {e}")
        if key:
            try:
                save_sync_state(bq_client, key, started_at, "error", error=str(e)[:1000])
            except Exception as state_error:
                print(f"Could not record sync error: {state_error}")
        return {"status": "error", "message": str(e)}, 500
