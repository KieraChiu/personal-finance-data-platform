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
FROM
  `finance-data-pipeline-500622.finance_raw.plaid_transactions`
WHERE pending IS FALSE;

