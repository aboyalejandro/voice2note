
  create view "voice2note"."analytics"."stg_note_vectors_agg__dbt_tmp"
    
    
  as (
    
    

    
        select 
            *
        from user_2.note_vectors
        
            union all
        
    
        select 
            *
        from user_1.note_vectors
        
    

  );