select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    audio_key as unique_field,
    count(*) as n_records

from "voice2note"."analytics"."fct_notes"
where audio_key is not null
group by audio_key
having count(*) > 1



      
    ) dbt_internal_test