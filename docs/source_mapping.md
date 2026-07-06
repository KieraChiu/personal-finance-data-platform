# Source-to-Core Mapping

## Wells Fargo / Plaid

| Source field | Core field | Transformation |
|---|---|---|
| transaction_id | source_transaction_id | Keep original Plaid ID |
| account_name | account_name | Standardize account name |
| date | transaction_date | Convert to DATE |
| name | description | Keep original description |
| amount | amount | Apply project amount convention |
| category | source_main_category | Map later |
| subcategory | source_subcategory | Map later |

## Apple Card

| Source field | Core field | Transformation |
|---|---|---|
| generated hash | source_transaction_id | Stable hash from source fields |
| account label | account_name | Use Apple Card |
| Transaction Date | transaction_date | Convert to DATE |
| Description | description | Keep original description |
| Amount (USD) | amount | Apply project amount convention |
| Type | transaction_type | Normalize values |
| Category | source_main_category | Map source category |
| blank or mapped value | source_subcategory | Add later if unavailable |

