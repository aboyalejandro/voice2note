select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    username as unique_field,
    count(*) as n_records

from "voice2note"."public"."users"
where username is not null
group by username
having count(*) > 1



      
    ) dbt_internal_test