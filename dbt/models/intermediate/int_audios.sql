select  
    audio_key,
    audio_type,
    round(((metadata->>'size')::int/1024),2) as audio_size, --converted to megabytes
    round((EXTRACT(EPOCH FROM (metadata->>'duration')::interval) / 60),2) as audio_duration, --converted to minutes
    metadata->>'format' as audio_format,
    metadata->>'conversion_status' as audio_conversion_status,
    created_at
from {{ref('stg_audios_agg')}}
where deleted_at is null