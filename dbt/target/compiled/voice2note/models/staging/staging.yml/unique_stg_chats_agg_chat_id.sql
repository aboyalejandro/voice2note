
    
    

select
    chat_id as unique_field,
    count(*) as n_records

from "voice2note"."analytics"."stg_chats_agg"
where chat_id is not null
group by chat_id
having count(*) > 1


