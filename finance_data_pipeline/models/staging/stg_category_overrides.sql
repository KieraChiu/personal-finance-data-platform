with source as (
    select * from {{ source('finance_raw', 'category_overrides_raw') }}
),

cleaned as (
    select
        trim(cast(transaction_id as string))        as transaction_id,
        trim(cast(override_category as string))     as override_category,
        trim(cast(subcategory as string))                 as subcategory,
        current_timestamp()                         as _loaded_at
    from source
  
    where override_category is not null
      and trim(cast(override_category as string)) != ''
      and transaction_id is not null
)

select * from cleaned