select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select hashed_password
from "voice2note"."public"."users"
where hashed_password is null



      
    ) dbt_internal_test