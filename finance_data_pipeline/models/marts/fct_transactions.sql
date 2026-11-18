with wells_fargo as (
    select
        transaction_id,
        transaction_date,
        merchant_description,
        amount                                          as amount_normalized,
        cast(null 										as string) as raw_category,
        source_account
    from {{ ref('stg_wells_fargo') }}
    where transaction_date < '2026-03-03'
),

apple_card_filtered as (
    select
        transaction_id,
        transaction_date,
        merchant_description,
        amount * -1                                     as amount_normalized,
        apple_category                                  as raw_category,
        source_account
    from {{ ref('stg_apple_card') }}
    where purchased_by = 'Kiera Chiu'
),

plaid as (
    select
        transaction_id,
        transaction_date,
        merchant_description,
        amount * -1                                     as amount_normalized,
        coalesce(
            json_value(plaid_category, '$[2]'),
            json_value(plaid_category, '$[1]'),
            json_value(plaid_category, '$[0]')
        )                                               as raw_category,
        source_account
    from {{ ref('stg_plaid') }}
),

unioned as (
    select * from wells_fargo
    union all
    select * from apple_card_filtered
    union all
    select * from plaid
),

overrides as (
    select * from {{ ref('stg_category_overrides') }}
),

final as (
    select
        u.transaction_id,
        u.transaction_date,
        u.merchant_description,
        u.amount_normalized,
        u.source_account,
        u.raw_category,
        coalesce(o.override_category, u.raw_category)  as category,
    from unioned u
    left join overrides o
        on u.transaction_id = o.transaction_id
)

select * from final
