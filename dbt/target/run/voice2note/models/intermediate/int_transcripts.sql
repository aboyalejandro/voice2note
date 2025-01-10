
  create view "voice2note"."analytics"."int_transcripts__dbt_tmp"
    
    
  as (
    select audio_key,
    transcription->>'note_title' as note_title,
    transcription->>'summary_text' as note_summary,
    transcription->>'transcript_text' as note_transcript,
    created_at
from "voice2note"."analytics"."stg_transcripts_agg" 
where deleted_at is null
  );