select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    message_id as unique_field,
    count(*) as n_records

from "voice2note"."analytics"."stg_chat_messages_agg"
where message_id is not null
group by message_id
having count(*) > 1



      
    ) dbt_internal_test