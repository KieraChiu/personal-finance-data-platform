CREATE TABLE IF NOT EXISTS `finance-data-pipeline-500622.finance_core.transactions` (
  transaction_id STRING NOT NULL,
  source_system STRING NOT NULL,
  transaction_date DATE NOT NULL,
        name STRING, 
  amount NUMERIC NOT NULL,
  transaction_type STRING,
  category STRING,
  subcategory STRING,
  ingested_at TIMESTAMP NOT NULL
);

