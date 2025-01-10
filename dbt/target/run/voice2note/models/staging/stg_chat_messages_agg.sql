
  create view "voice2note"."analytics"."stg_chat_messages_agg__dbt_tmp"
    
    
  as (
    
    

    
        select 
            *
        from user_2.chat_messages
        
            union all
        
    
        select 
            *
        from user_1.chat_messages
        
    

  );