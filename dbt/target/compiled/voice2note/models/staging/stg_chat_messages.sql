
    

    
        select 
            'user_2' as source_schema,
            *
        from user_2.chat_messages
        
            union all
        
    
        select 
            'user_1' as source_schema,
            *
        from user_1.chat_messages
        
    
