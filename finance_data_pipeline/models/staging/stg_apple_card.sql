with source as (
    select * from {{ source('finance_raw', 'apple_card_transactions') }}
),

cleaned as (
    select
        transaction_id,
        cast(transaction_date as date) as transaction_date,
        cast(clearing_date as date) as clearing_date,
        trim(description) as merchant_description,
        trim(merchant) as merchant_name,
        trim(category) as apple_category,
        transaction_type,
        cast(amount as numeric) as amount,
        purchased_by,
        'apple_card' as source_account
    from source
)

select * from cleaned
