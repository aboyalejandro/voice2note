select 
	audio_id, 
	transcript_id, 
	audios.audio_key, 
	transcription->> 'note_title' as note_title,
	transcription->> 'summary_text' as summary_text,
	transcription->> 'transcript_text' as transcript_text
from audios
left join transcripts 
	on audios.audio_key = transcripts.audio_key 