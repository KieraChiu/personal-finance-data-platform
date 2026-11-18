CREATE OR REPLACE TABLE
  `finance-data-pipeline-500622.finance_core.cleaned_plaid`

AS
SELECT
  date,
  REGEXP_REPLACE(
    TRIM(COALESCE(name)),
    r'\s+',
    ' '
  ) AS description,
  Category AS category,
  amount,
  CONCAT('plaid_', plaid_transaction_id) AS transaction_id,
  plaid_transaction_id,
  plaid_account_id,
  pending
FROM (
  -- Raw table is append-only: keep the newest row per transaction first,
  -- then drop removed and pending ones (same logic as dbt's stg_plaid).
  SELECT *
  FROM `finance-data-pipeline-500622.finance_raw.plaid_transactions`
  WHERE TRUE
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY plaid_transaction_id ORDER BY loaded_at DESC
  ) = 1
)
WHERE COALESCE(is_removed, FALSE) = FALSE
  AND pending IS FALSE;

