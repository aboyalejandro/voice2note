
    
    

with all_values as (

    select
        audio_format as value_field,
        count(*) as n_records

    from "voice2note"."analytics"."int_audios"
    group by audio_format

)

select *
from all_values
where value_field not in (
    'mp3','wav','webm'
)

