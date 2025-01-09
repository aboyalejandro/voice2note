select 	
    {{ dbt_utils.star(from=ref('int_audios'), except=['created_at'], relation_alias='audios')}},
    {{ dbt_utils.star(from=ref('int_transcripts'), except=['audio_key'], relation_alias='transcripts') }}
from {{ref('int_audios')}} as audios 
left join {{ref('int_transcripts')}} as transcripts
using(audio_key)