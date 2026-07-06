# Transaction Schema

| Field | Type | Description |
|---|---|---|
| transaction_id | STRING | Unique stable ID |
| source_system | STRING | plaid or apple_card |
| transaction_date | DATE | Date of purchase |
| name | STRING | Cleaned merchant name |
| amount | NUMERIC | Standardized transaction amount |
| transaction_type | STRING | purchase, payment, refund, transfer, etc. |
| category | STRING | Cleaned and finalized category |
| subcategory | STRING | Cleaned and finalized subcategory|
| ingested_at | TIMESTAMP | When the row entered the pipeline |

## Amount Convention

All transaction amounts are standardized as:

- Expenses are negative
- Income and refunds are positive
