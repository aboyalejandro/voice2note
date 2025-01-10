select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    audio_id as unique_field,
    count(*) as n_records

from "voice2note"."analytics"."stg_audios_agg"
where audio_id is not null
group by audio_id
having count(*) > 1



      
    ) dbt_internal_test