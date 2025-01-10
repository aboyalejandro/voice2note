select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with all_values as (

    select
        audio_conversion_status as value_field,
        count(*) as n_records

    from "voice2note"."analytics"."int_audios"
    group by audio_conversion_status

)

select *
from all_values
where value_field not in (
    'reencoded'','converted'
)



      
    ) dbt_internal_test