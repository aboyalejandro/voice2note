select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select message_id
from "voice2note"."analytics"."stg_chat_messages_agg"
where message_id is null



      
    ) dbt_internal_test