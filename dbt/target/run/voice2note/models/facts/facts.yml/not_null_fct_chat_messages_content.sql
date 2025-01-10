select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select content
from "voice2note"."analytics"."fct_chat_messages"
where content is null



      
    ) dbt_internal_test