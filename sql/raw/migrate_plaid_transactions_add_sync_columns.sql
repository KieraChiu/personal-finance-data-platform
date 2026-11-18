-- One-time migration: run before deploying the cursor-based ingestion function.
ALTER TABLE `finance-data-pipeline-500622.finance_raw.plaid_transactions`
  ADD COLUMN IF NOT EXISTS pending_transaction_id STRING,
  ADD COLUMN IF NOT EXISTS is_removed BOOL;

-- Make sure the sync-state table exists (cursor storage).
CREATE SCHEMA IF NOT EXISTS `finance-data-pipeline-500622.finance_metadata`;

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
