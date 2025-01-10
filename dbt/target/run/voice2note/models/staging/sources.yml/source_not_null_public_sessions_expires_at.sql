select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select expires_at
from "voice2note"."public"."sessions"
where expires_at is null



      
    ) dbt_internal_test