CREATE OR REPLACE TABLE
  `finance-data-pipeline-500622.finance_core.cleaned_wells_fargo_historical_06302026`

AS
SELECT
  SAFE.PARSE_DATE('%m/%d/%Y', date_raw) AS date,
  REGEXP_REPLACE(TRIM(name_raw), r'\s+', ' ') AS description,
  SAFE_CAST(
    REPLACE(REPLACE(amount_raw, '$', ''), ',', '')
    AS NUMERIC
  ) AS amount,
  CONCAT(
    'wf_history_',
    TO_HEX(
      SHA256(
        CONCAT(
          COALESCE(date_raw, ''),
          '|',
          COALESCE(name_raw, ''),
          '|',
          COALESCE(amount_raw, ''),
          '|',
          CAST(source_row_number AS STRING)
        )
      )
    )
  ) AS transaction_id
FROM
  `finance-data-pipeline-500622.finance_raw.wells_fargo_historical_06302026`;
