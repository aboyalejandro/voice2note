
    
    

with child as (
    select audio_key as from_field
    from "voice2note"."analytics"."stg_transcripts_agg"
    where audio_key is not null
),

parent as (
    select audio_key as to_field
    from "voice2note"."analytics"."stg_audios_agg"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null

