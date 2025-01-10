
  create view "voice2note"."analytics"."stg_transcripts_agg__dbt_tmp"
    
    
  as (
    
    

    
        select 
            *
        from user_2.transcripts
        
            union all
        
    
        select 
            *
        from user_1.transcripts
        
    

  );