with source as (
    select * from {{ source('finance_raw', 'plaid_transactions') }}
),

deduped as (
    select
        *,
        row_number() over (
            partition by plaid_transaction_id
            order by loaded_at desc
        ) as row_num
    from source
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
    from deduped
    where row_num = 1
)

select * from cleaned
