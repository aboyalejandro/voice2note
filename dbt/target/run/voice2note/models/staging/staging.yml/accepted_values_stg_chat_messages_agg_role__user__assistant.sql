select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with all_values as (

    select
        role as value_field,
        count(*) as n_records

    from "voice2note"."analytics"."stg_chat_messages_agg"
    group by role

)

select *
from all_values
where value_field not in (
    'user','assistant'
)



      
    ) dbt_internal_test