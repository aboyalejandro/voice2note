
  create view "voice2note"."analytics"."stg_chats_agg__dbt_tmp"
    
    
  as (
    
    

    
        select 
            *
        from user_2.chats
        
            union all
        
    
        select 
            *
        from user_1.chats
        
    

  );