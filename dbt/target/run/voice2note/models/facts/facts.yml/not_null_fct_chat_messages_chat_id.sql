select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select chat_id
from "voice2note"."analytics"."fct_chat_messages"
where chat_id is null



      
    ) dbt_internal_test