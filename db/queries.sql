-- notes 
SELECT 
    audios.audio_key,
    TO_CHAR(audios.created_at, 'MM/DD') as note_date,
    COALESCE(transcription->>'note_title','Transcribing note...') as note_title,
    COALESCE(transcription->>'summary_text','Your audio is being transcribed. It will show up in here when is finished.') as note_summary,
FROM audios
LEFT JOIN transcripts
ON audios.audio_key = transcripts.audio_key
WHERE user_id = %s
ORDER BY audios.created_at DESC

-- note_detail

SELECT 
    audios.audio_key,
    TO_CHAR(audios.created_at, 'MM/DD') as note_date,
    COALESCE(transcription->>'note_title','Transcribing note...') as note_title,
    COALESCE(transcription->>'transcript_text','Your audio is being transcribed. It will show up in here when is finished.') as note_transcription
FROM audios
LEFT JOIN transcripts
ON audios.audio_key = transcripts.audio_key
WHERE audios.audio_key = %s