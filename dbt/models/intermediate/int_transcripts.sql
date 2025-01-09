select audio_key,
    transcription->>'note_title' as note_title,
    transcription->>'summary_text' as note_summary,
    transcription->>'transcript_text' as note_transcript,
    created_at
from {{ref('stg_transcripts_agg')}} 
where deleted_at is null
