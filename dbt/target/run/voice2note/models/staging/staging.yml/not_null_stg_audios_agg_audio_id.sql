select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select audio_id
from "voice2note"."analytics"."stg_audios_agg"
where audio_id is null



      
    ) dbt_internal_test