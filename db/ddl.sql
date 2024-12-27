-- Users Table
CREATE TABLE public.users (
	user_id serial4 NOT NULL,
	username varchar(255) NOT NULL,
	hashed_password varchar(255) NOT NULL,
	created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	reset_token text NULL,
	reset_token_expires timestamptz NULL,
	CONSTRAINT users_pkey PRIMARY KEY (user_id)
);
CREATE INDEX idx_users_user_id ON public.users USING btree (user_id);

-- Sessions Table
CREATE TABLE public.sessions (
	session_id text NOT NULL,
	user_id int4 NULL,
	created_at timestamptz DEFAULT CURRENT_TIMESTAMP NULL,
	expires_at timestamptz NULL,
	deleted_at timestamptz NULL,
	CONSTRAINT sessions_pkey PRIMARY KEY (session_id)
);
CREATE INDEX idx_sessions_user_active ON public.sessions USING btree (user_id, deleted_at) WHERE (deleted_at IS NULL);
ALTER TABLE public.sessions ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id);

-- Audios Table
CREATE TABLE user_{user_id}.audios (
	audio_id serial4 NOT NULL,
	audio_key varchar(15) NOT NULL,
	user_id int4 NOT NULL,
	s3_object_url text NOT NULL,
	audio_type varchar(8) NOT NULL,
	created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	deleted_at timestamp NULL,
	metadata jsonb NULL,
	CONSTRAINT audios_audio_key_key UNIQUE (audio_key),
	CONSTRAINT audios_audio_type_check CHECK (((audio_type)::text = ANY ((ARRAY['recorded'::character varying, 'uploaded'::character varying])::text[]))),
	CONSTRAINT audios_pkey PRIMARY KEY (audio_id)
);
CREATE INDEX idx_audios_audio_id ON user_{user_id}.audios USING btree (audio_id);
ALTER TABLE user_{user_id}.audios ADD CONSTRAINT audios_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_{user_id}.users(user_id);
ALTER TABLE user_{user_id}.audios ADD CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES user_{user_id}.users(user_id);

-- Transcripts Table
CREATE TABLE user_{user_id}.transcripts (
	transcript_id serial4 NOT NULL,
	audio_key varchar(255) NOT NULL,
	s3_object_url text NULL,
	transcription jsonb NULL,
	created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
	deleted_at timestamp NULL,
	CONSTRAINT transcripts_pkey PRIMARY KEY (transcript_id)
);
CREATE INDEX idx_transcripts_audio_id ON user_{user_id}.transcripts USING btree (audio_key);
CREATE INDEX idx_transcripts_transcript_id ON user_{user_id}.transcripts USING btree (transcript_id);
ALTER TABLE user_{user_id}.transcripts ADD CONSTRAINT transcripts_audio_key_fkey FOREIGN KEY (audio_key) REFERENCES user_{user_id}.audios(audio_key);
