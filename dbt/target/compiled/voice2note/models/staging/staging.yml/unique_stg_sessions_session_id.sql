
    
    

select
    session_id as unique_field,
    count(*) as n_records

from "voice2note"."analytics"."stg_sessions"
where session_id is not null
group by session_id
having count(*) > 1

