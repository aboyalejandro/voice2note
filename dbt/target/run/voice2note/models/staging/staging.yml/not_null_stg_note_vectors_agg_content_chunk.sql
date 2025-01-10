select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select content_chunk
from "voice2note"."analytics"."stg_note_vectors_agg"
where content_chunk is null



      
    ) dbt_internal_test