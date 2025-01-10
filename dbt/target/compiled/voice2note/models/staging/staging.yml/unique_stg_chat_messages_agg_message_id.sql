
    
    

select
    message_id as unique_field,
    count(*) as n_records

from "voice2note"."analytics"."stg_chat_messages_agg"
where message_id is not null
group by message_id
having count(*) > 1


