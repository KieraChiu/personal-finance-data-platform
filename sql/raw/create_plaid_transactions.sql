-- Append-only raw landing table written by ingestion/plaid/main.py.
-- dbt's stg_plaid keeps the latest row per plaid_transaction_id and drops
-- rows whose latest version has is_removed = true.
CREATE TABLE IF NOT EXISTS
  `finance-data-pipeline-500622.finance_raw.plaid_transactions`
(
  plaid_transaction_id STRING NOT NULL,
  plaid_account_id STRING,
  date DATE,
  authorized_date DATE,
  name STRING,
  amount NUMERIC,
  pending BOOL,
  pending_transaction_id STRING,
  category STRING,
  is_removed BOOL,
  loaded_at TIMESTAMP
);
