
  create view "voice2note"."analytics"."fct_chat_messages__dbt_tmp"
    
    
  as (
    select 
    chats.chat_id,
    chats.title,
    messages.role,
    messages.content,
    messages.source_refs->>'sources' as chat_note_sources,
    chats.created_at
from "voice2note"."analytics"."stg_chats_agg" as chats
left join "voice2note"."analytics"."stg_chat_messages_agg" as messages
using (chat_id)
where chats.deleted_at is null
  );