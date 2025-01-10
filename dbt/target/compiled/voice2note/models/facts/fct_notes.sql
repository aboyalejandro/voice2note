select 	
    audios."audio_key",
  audios."audio_type",
  audios."audio_size",
  audios."audio_duration",
  audios."audio_format",
  audios."audio_conversion_status",
    transcripts."note_title",
  transcripts."note_summary",
  transcripts."note_transcript",
  transcripts."created_at"
from "voice2note"."analytics"."int_audios" as audios 
left join "voice2note"."analytics"."int_transcripts" as transcripts
using(audio_key)