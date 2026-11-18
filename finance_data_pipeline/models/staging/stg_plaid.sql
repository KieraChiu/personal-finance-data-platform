-- finance_raw.plaid_transactions is append-only: each sync appends the
-- current version of every added/modified transaction, plus a tombstone row
-- (is_removed = true) for each transaction Plaid removed.
with source as (
    select * from {{ source('finance_raw', 'plaid_transactions') }}
),

-- Keep only the most recent version of each transaction.
latest as (
    select *
    from source
    where true  -- BigQuery requires WHERE/GROUP BY/HAVING alongside QUALIFY
    qualify row_number() over (
        partition by plaid_transaction_id
        order by loaded_at desc
    ) = 1
),

cleaned as (
    select
        plaid_transaction_id as transaction_id,
        plaid_account_id,
        cast(date as date) as transaction_date,
        cast(authorized_date as date) as authorized_date,
        trim(name) as merchant_description,
        cast(amount as numeric) * -1 as amount,
        pending,
        trim(category) as plaid_category,
        loaded_at,
        'plaid' as source_account
    from latest
    -- Removed by Plaid (deleted, or a pending txn replaced by its posted one).
    where coalesce(is_removed, false) = false
      -- When a pending transaction posts, Plaid gives the posted one a NEW
      -- transaction_id. Rows loaded before removals were tracked never got a
      -- tombstone, so drop pending rows here too; they show up once posted.
      and coalesce(pending, false) = false
)

select * from cleaned
