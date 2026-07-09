with source as (
    select * from {{ source('finance_raw', 'wells_fargo_historical_06302026') }}
),

cleaned as (
    select
        {{ dbt_utils.generate_surrogate_key(['date', 'description', 'amount']) }} as transaction_id,
        cast(date as date) as transaction_date,
        trim(description) as merchant_description,
        cast(amount as numeric) as amount,
        status as transaction_status,
        'wells_fargo' as source_account
    from source
)

select * from cleaned