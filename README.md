# Voice2Note 🎙️📝

Voice2Note is an AI-powered web application that transforms your voice recordings into organized, searchable notes. Whether you're a student recording lectures, a professional capturing meeting notes, or anyone who prefers speaking over typing, Voice2Note helps you save time by keeping your thoughts organized.

## Features ✨

- **Voice Recording & Upload**
  - Record audio directly in your browser
  - Upload existing audio files (supports MP3, WAV, WebM)
  - Currently supports English and Spanish audios

- **AI-Powered Processing**
  - Automatic speech-to-text transcription
  - Smart note title generation
  - Concise summary creation

- **Note Management**
  - Filter notes by date and keywords
  - Edit transcriptions and titles
  - Real-time audio playback

## How It Works 🔄

Voice2Note uses a combination of AWS services and OpenAI's GPT to process your audio:

1. **Recording**: Record directly in your browser or upload audio files
2. **Processing**: AWS Transcribe converts speech to text
3. **Enhancement**: GPT generates titles and summaries
4. **Organization**: Notes are stored with metadata for easy searching
5. **Access**: Browse, search, and edit your notes anytime

## Tech Stack 🛠️

- **Frontend**: FastHTML, JavaScript
- **Backend**: Python, FastAPI
- **Database**: PostgreSQL
- **Cloud Services**: AWS (S3, Lambda, Transcribe)
- **AI/ML**: OpenAI GPT