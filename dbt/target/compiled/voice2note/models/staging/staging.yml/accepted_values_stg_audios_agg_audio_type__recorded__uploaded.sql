
    
    

with all_values as (

    select
        audio_type as value_field,
        count(*) as n_records

    from "voice2note"."analytics"."stg_audios_agg"
    group by audio_type

)

select *
from all_values
where value_field not in (
    'recorded','uploaded'
)


