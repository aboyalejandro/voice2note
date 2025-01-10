select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select vector_id
from "voice2note"."analytics"."stg_note_vectors_agg"
where vector_id is null



      
    ) dbt_internal_test