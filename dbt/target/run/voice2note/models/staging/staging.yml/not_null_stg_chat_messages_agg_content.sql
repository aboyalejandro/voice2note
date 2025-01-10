select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select content
from "voice2note"."analytics"."stg_chat_messages_agg"
where content is null



      
    ) dbt_internal_test