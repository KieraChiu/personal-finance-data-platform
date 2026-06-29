CREATE TABLE IF NOT EXISTS
  `finance-data-pipeline-500622.finance_core.category_overrides`
(
  transaction_id STRING NOT NULL,
  category STRING NOT NULL,
  subcategory STRING NOT NULL,
  override_note STRING,
  updated_at TIMESTAMP NOT NULL,
  updated_by STRING
);

