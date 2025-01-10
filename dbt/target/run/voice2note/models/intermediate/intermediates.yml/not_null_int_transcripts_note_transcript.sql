select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select note_transcript
from "voice2note"."analytics"."int_transcripts"
where note_transcript is null



      
    ) dbt_internal_test