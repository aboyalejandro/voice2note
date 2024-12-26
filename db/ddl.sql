-- Users Table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Audios Table
CREATE TABLE audios (
    audio_id SERIAL PRIMARY KEY,
    audio_key VARCHAR(15) NOT NULL UNIQUE, 
    user_id INTEGER NOT NULL,
    s3_object_url TEXT NOT NULL,
    audio_type VARCHAR(8) NOT NULL CHECK (audio_type IN ('recorded', 'uploaded')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Transcripts Table
CREATE TABLE transcripts (
    transcript_id SERIAL PRIMARY KEY,
    audio_key VARCHAR(255) NOT NULL,  
    s3_object_url TEXT,
    transcription JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    FOREIGN KEY (audio_key) REFERENCES audios(audio_key)
);

-- Explicitly create an index for the primary key
CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_audios_audio_id ON audios(audio_id);
CREATE INDEX idx_transcripts_transcript_id ON transcripts(transcript_id);
CREATE INDEX idx_transcripts_audio_id ON transcripts(audio_key);