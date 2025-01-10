
  create view "voice2note"."analytics"."stg_users__dbt_tmp"
    
    
  as (
    select *
from "voice2note"."public"."users"
  );