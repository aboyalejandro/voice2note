select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select audio_key
from "voice2note"."analytics"."stg_note_vectors_agg"
where audio_key is null



      
    ) dbt_internal_test