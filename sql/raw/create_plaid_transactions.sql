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
  category STRING,
  );

