select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with all_values as (

    select
        audio_type as value_field,
        count(*) as n_records

    from "voice2note"."analytics"."stg_audios_agg"
    group by audio_type

)

select *
from all_values
where value_field not in (
    'recorded','uploaded'
)



      
    ) dbt_internal_test