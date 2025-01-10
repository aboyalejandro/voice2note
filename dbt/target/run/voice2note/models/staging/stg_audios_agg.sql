
  create view "voice2note"."analytics"."stg_audios_agg__dbt_tmp"
    
    
  as (
    
    

    
        select 
            *
        from user_2.audios
        
            union all
        
    
        select 
            *
        from user_1.audios
        
    

  );