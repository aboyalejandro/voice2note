
  create view "voice2note"."analytics"."stg_sessions__dbt_tmp"
    
    
  as (
    select *
from "voice2note"."public"."sessions"
  );