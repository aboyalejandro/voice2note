select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with child as (
    select chat_id as from_field
    from "voice2note"."analytics"."stg_chat_messages_agg"
    where chat_id is not null
),

parent as (
    select chat_id as to_field
    from "voice2note"."analytics"."stg_chats_agg"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null



      
    ) dbt_internal_test