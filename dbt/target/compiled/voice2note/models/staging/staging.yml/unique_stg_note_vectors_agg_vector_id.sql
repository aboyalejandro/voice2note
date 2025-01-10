
    
    

select
    vector_id as unique_field,
    count(*) as n_records

from "voice2note"."analytics"."stg_note_vectors_agg"
where vector_id is not null
group by vector_id
having count(*) > 1


