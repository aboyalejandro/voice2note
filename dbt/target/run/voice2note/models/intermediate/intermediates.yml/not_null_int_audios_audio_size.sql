select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select audio_size
from "voice2note"."analytics"."int_audios"
where audio_size is null



      
    ) dbt_internal_test