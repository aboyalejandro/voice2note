
    
    

with all_values as (

    select
        audio_conversion_status as value_field,
        count(*) as n_records

    from "voice2note"."analytics"."int_audios"
    group by audio_conversion_status

)

select *
from all_values
where value_field not in (
    'pending','completed','failed'
)


