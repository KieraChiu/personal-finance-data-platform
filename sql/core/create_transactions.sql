CREATE TABLE IF NOT EXISTS `finance-data-pipeline-500622.finance_core.transactions` (
  transaction_date DATE NOT NULL,
  transaction_id STRING NOT NULL,
  name STRING, 
  amount NUMERIC NOT NULL,
  category STRING,
  subcategory STRING,
  source_system STRING NOT NULL,
  ingested_at TIMESTAMP NOT NULL
);

