with wells_fargo as (
    select
        transaction_id,
        transaction_date,
        merchant_description,
        amount as amount_normalized,
        source_account
    from {{ ref('stg_wells_fargo') }}
    where transaction_date < '2026-03-03'  
),

apple_card_filtered as (
    select
        transaction_id,
        transaction_date,
        merchant_description,
        amount * -1 as amount_normalized,
        source_account
    from {{ ref('stg_apple_card') }}
    where purchased_by = 'Kiera Chiu'
),

plaid as (
    select
        transaction_id,
        transaction_date,
        merchant_description,
        amount * -1 as amount_normalized,
        source_account
    from {{ ref('stg_plaid') }}
),

unioned as (
    select * from wells_fargo
    union all
    select * from apple_card_filtered
    union all
    select * from plaid
)

select * from unioned
