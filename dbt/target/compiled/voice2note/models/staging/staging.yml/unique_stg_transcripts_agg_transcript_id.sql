
    
    

select
    transcript_id as unique_field,
    count(*) as n_records

from "voice2note"."analytics"."stg_transcripts_agg"
where transcript_id is not null
group by transcript_id
having count(*) > 1


