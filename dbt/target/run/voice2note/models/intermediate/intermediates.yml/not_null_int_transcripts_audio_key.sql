select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select audio_key
from "voice2note"."analytics"."int_transcripts"
where audio_key is null



      
    ) dbt_internal_test