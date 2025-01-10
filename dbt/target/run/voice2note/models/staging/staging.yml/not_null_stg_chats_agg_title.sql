select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select title
from "voice2note"."analytics"."stg_chats_agg"
where title is null



      
    ) dbt_internal_test