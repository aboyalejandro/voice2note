# Voice2Note 🎙️📝

Voice2Note is an AI-powered web application that transforms your voice recordings into organized, searchable notes. Built for the AI Apps Hackathon, it offers a seamless experience for recording, transcribing, and managing your audio notes.

## Features ✨

- **Voice Recording & Upload**
  - Record audio directly in your browser
  - Upload existing audio files (supports MP3, WAV, WebM)
  - Support for English and Spanish audio

- **AI-Powered Processing**
  - Automatic speech-to-text transcription
  - Smart note title generation
  - Concise summary creation

- **Note Management**
  - Search through transcriptions
  - Filter notes by date
  - Edit transcriptions and titles
  - Real-time audio playback

- **User Experience**
  - Clean, responsive interface
  - Mobile-friendly design
  - Secure user authentication
  - Personal note organization

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

## Why Voice2Note? 🎯

Voice2Note was developed to solve the common problem of managing voice notes effectively. Whether you're a student recording lectures, a professional capturing meeting notes, or anyone who prefers speaking over typing, Voice2Note helps you:

- Save time by automating transcription
- Find specific information quickly
- Keep your thoughts organized
- Access your notes from any device

