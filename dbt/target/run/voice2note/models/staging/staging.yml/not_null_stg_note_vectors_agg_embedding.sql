select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select embedding
from "voice2note"."analytics"."stg_note_vectors_agg"
where embedding is null



      
    ) dbt_internal_test