
    
    

select
    audio_key as unique_field,
    count(*) as n_records

from "voice2note"."analytics"."int_audios"
where audio_key is not null
group by audio_key
having count(*) > 1


