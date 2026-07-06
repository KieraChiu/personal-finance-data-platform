CREATE TABLE IF NOT EXISTS
  `finance-data-pipeline-500622.finance_metadata.plaid_sync_state`
(
  item_id_hash STRING NOT NULL,
  cursor STRING,
  last_sync_started_at TIMESTAMP,
  last_sync_completed_at TIMESTAMP,
  sync_status STRING,
  error_message STRING
);

