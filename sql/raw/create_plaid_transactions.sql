CREATE TABLE IF NOT EXISTS
  `finance-data-pipeline-500622.finance_raw.plaid_transactions`
(
  transaction_id STRING NOT NULL,
  account_id STRING,
  date DATE,
  name STRING,
  amount NUMERIC,
  pending BOOL,
  category STRING,
  loaded_at TIMESTAMP
);
