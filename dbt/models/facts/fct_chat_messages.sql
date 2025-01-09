select 
    chats.chat_id,
    chats.title,
    messages.role,
    messages.content,
    messages.source_refs->>'sources' as chat_note_sources,
    chats.created_at
from {{ref('stg_chats_agg')}} as chats
left join {{ref('stg_chat_messages_agg')}} as messages
using (chat_id)
where chats.deleted_at is null 