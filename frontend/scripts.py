"""
Frontend JavaScript code for Voice2Note.

This module provides JavaScript functionality for different pages:
- Home: Audio recording, uploading, and playback
- Notes: Search and filtering functionality
- Note Detail: Note editing and audio playback
- Chat Detail: Real-time chat interface and message handling

Each method returns a JavaScript string that gets embedded in the corresponding page.
"""


class Scripts:
    @staticmethod
    def home() -> str:
        """
        JavaScript for the home page.

        Handles:
        - Audio recording with MediaRecorder API
        - File uploads and validation
        - Audio playback controls
        - Timer display during recording
        - Save and navigation functionality

        Returns:
            str: JavaScript code for home page
        """
        return """
                    let mediaRecorder;
                    let audioChunks = [];
                        let recordingDuration = 0;
                    let recordInterval;

                    document.getElementById('upload').addEventListener('click', () => {
                        document.getElementById('uploadInput').click();
                    });

                    document.getElementById('uploadInput').addEventListener('change', async (event) => {
                        const file = event.target.files[0];
                        const saveButton = document.getElementById('save');

                        if (file) {
                            const allowedExtensions = ['wav', 'mp3', 'webm'];
                            const fileExtension = file.name.split('.').pop().toLowerCase();

                            console.log('Detected MIME type:', file.type);
                            console.log('Detected file extension:', fileExtension);

                            if (!allowedExtensions.includes(fileExtension)) {
                                alert(`Invalid file type (${fileExtension}). Please upload a .wav, .mp3, or .webm file.`);
                                event.target.value = '';
                                return;
                            }

                            const audioUrl = URL.createObjectURL(file);
                            const audioPlayback = document.getElementById('audioPlayback');
                            audioPlayback.src = audioUrl;

                            window.audioBlob = file;
                            window.audioType = 'uploaded';
                            saveButton.disabled = false;
                        }
                    });

                    document.getElementById('stop').addEventListener('click', () => {
                        if (mediaRecorder && mediaRecorder.state === 'recording') {
                            mediaRecorder.stop();
                            document.getElementById('start').disabled = false;
                            document.getElementById('stop').disabled = true;
                            mediaRecorder.stream.getTracks().forEach(track => track.stop());
                        }
                    });

                    document.getElementById('start').addEventListener('click', () => {
                        navigator.mediaDevices.getUserMedia({ audio: true })
                        .then(stream => {
                                const options = {
                                    mimeType: 'audio/webm;codecs=opus',
                                    audioBitsPerSecond: 128000
                                };
                                
                                mediaRecorder = new MediaRecorder(stream, options);
                                recordingDuration = 0;
                                audioChunks = [];

                            mediaRecorder.ondataavailable = event => {
                                audioChunks.push(event.data);
                            };

                            mediaRecorder.onstop = () => {
                                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                                const audioUrl = URL.createObjectURL(audioBlob);
                                const audioPlayback = document.getElementById('audioPlayback');
                                audioPlayback.src = audioUrl;

                                clearInterval(recordInterval);
                                document.getElementById('recordTimer').style.display = 'none';

                                window.audioBlob = audioBlob;
                                    window.audioType = 'recorded';
                                    document.getElementById('save').disabled = false;
                            };

                                mediaRecorder.start(1000);
                            document.getElementById('start').disabled = true;
                            document.getElementById('stop').disabled = false;

                            const timerElement = document.getElementById('recordTimer');
                            timerElement.style.display = 'block';
                                
                            recordInterval = setInterval(() => {
                                    recordingDuration++;
                                    const minutes = Math.floor(recordingDuration / 60);
                                    const displaySeconds = recordingDuration % 60;
                                timerElement.textContent = `Recording: ${minutes}:${displaySeconds < 10 ? '0' : ''}${displaySeconds}`;
                            }, 1000);
                            })
                            .catch(error => {
                                console.error('Error accessing microphone:', error);
                                alert('Error accessing microphone. Please ensure you have given permission.');
                        });
                    });

                    document.getElementById('save').addEventListener('click', () => {
                        const audioBlob = window.audioBlob;
                            const audioType = window.audioType;
                            const saveButton = document.getElementById('save');

                        if (!audioBlob) {
                            alert('No audio to save!');
                            return;
                        }

                        const formData = new FormData();
                        const timestamp = Math.floor(Date.now() / 1000);
                            const extension = audioBlob.type.split('/')[1];
                            const filename = `recording_${timestamp}.${extension}`;

                        formData.append('audio_file', audioBlob, filename);
                            formData.append('audio_type', audioType);

                            saveButton.textContent = 'Saving...';
                            saveButton.disabled = true;

                        fetch('/save-audio', {
                            method: 'POST',
                            body: formData,
                            })
                                .then(response => {
                                    if (!response.ok) {
                                        return response.text().then(text => {
                                            throw new Error(`Failed to save audio: ${text}`);
                                        });
                                    }
                                    return response.json();
                                })
                                .then(data => {
                                    alert('Audio saved successfully!');
                                    window.audioBlob = null;
                                    document.getElementById('audioPlayback').src = '';
                                })
                                .catch(error => {
                                    alert(error.message || 'Failed to save audio. Please try again.');
                                })
                                .finally(() => {
                                    saveButton.textContent = 'Save Audio';
                                    saveButton.disabled = false;
                                });
                        });

                    function startNewChat() {
                        const sessionId = Math.random().toString(36).substring(7);
                        window.location.href = `/chat_${sessionId}`;
                    }
            """

    @staticmethod
    def notes() -> str:
        """
        JavaScript for the notes list page.

        Handles:
        - Search form submission
        - Clear search functionality
        - Date range and keyword filtering

        Returns:
            str: JavaScript code for notes page
        """
        return """
                function clearSearch() {
                    document.querySelector('input[name="start_date"]').value = '';
                    document.querySelector('input[name="end_date"]').value = '';
                    document.querySelector('input[name="keyword"]').value = '';
                    window.location.href = '/notes';
                }

                function deleteNote(audioKey) {
                if (confirm('Are you sure you want to delete this note?')) {
                    fetch(`/delete-note/${audioKey}`, {
                        method: 'POST'
                    })
                    .then(response => {
                        if (response.ok) {
                            alert('Note deleted successfully!');
                            window.location.reload();
                        } else {
                            alert('Failed to delete note.');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Error deleting note.');
                    });
                }
            }
                """

    @staticmethod
    def note_detail() -> str:
        """
        JavaScript for the note detail page.

        Handles:
        - Note editing mode toggle
        - Save note changes
        - Delete note confirmation
        - Audio playback controls
        - Form validation

        Returns:
            str: JavaScript code for note detail page
        """
        return """
                function toggleEditMode(show) {
                    const editContainer = document.querySelector('.edit-container');
                    const noteContainer = document.querySelector('.note-container');
                    
                    if (show) {
                        noteContainer.style.display = 'none';
                        editContainer.style.display = 'block';
                        setTimeout(() => {
                            document.getElementById('edit-title').focus();
                        }, 50);
                        } else {
                        editContainer.style.display = 'none';
                        noteContainer.style.display = 'block';
                    }
                }

                async function saveNote(audioKey) {
                    const title = document.getElementById('edit-title').value;
                    const transcript = document.getElementById('edit-transcript').value;

                    if (!title.trim() || !transcript.trim()) {
                        alert('Title and transcript cannot be empty');
                        return;
                    }

                    try {
                        const response = await fetch(`/edit-note/${audioKey}`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                note_title: title,
                                transcript_text: transcript
                            })
                        });

                        if (response.ok) {
                            document.querySelector('.note-title').textContent = title;
                            document.querySelector('.note-transcription').textContent = transcript;
                            toggleEditMode(false);
                        } else {
                            alert('Failed to save changes.');
                        }
                    } catch (error) {
                        console.error('Error:', error);
                        alert('Error saving changes.');
                    }
                }

                document.addEventListener('keydown', function(e) {
                    const editContainer = document.querySelector('.edit-container');
                    if (editContainer.style.display === 'block') {
                        if (e.key === 'Escape') {
                            toggleEditMode(false);
                        }
                        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                            const audioKey = window.location.pathname.split('_')[1];
                            saveNote(audioKey);
                        }
                    }
                });

                function deleteNote(audioKey) {
                    if (confirm('Are you sure you want to delete this note?')) {
                        fetch(`/delete-note/${audioKey}`, {
                            method: 'POST'
                        })
                        .then(response => {
                            if (response.ok) {
                                window.location.href = '/notes';
                            } else {
                                alert('Failed to delete note.');
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('Error deleting note.');
                        });
                    }
                }
                
                let audioPlayer = null;
                let isPlaying = false;

                async function toggleAudio(audioKey) {
                    const playBtn = document.getElementById('play-btn');
                    const durationDisplay = document.getElementById('duration-display');
                    let audioPlayer = document.getElementById('audio-player');

                    if (!isPlaying) {
                        try {
                            playBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                            
                            const response = await fetch(`/get-audio/${audioKey}`);
                            if (!response.ok) throw new Error('Failed to fetch audio');
                            
                            const blob = await response.blob();
                            const audioUrl = URL.createObjectURL(blob);
                            
                            if (!audioPlayer) {
                                audioPlayer = document.createElement('audio');
                                audioPlayer.id = 'audio-player';
                                audioPlayer.className = 'audio-player';
                                playBtn.parentNode.insertBefore(audioPlayer, playBtn.nextSibling);
                            }
                            
                            audioPlayer.src = audioUrl;
                            audioPlayer.style.display = 'block';
                            if (durationDisplay) {
                                durationDisplay.style.display = 'none';
                            }
                            
                            audioPlayer.onerror = (e) => {
                                console.error('Audio playback error:', e);
                                alert('This audio format might not be supported by your browser.');
                                playBtn.innerHTML = '<i class="fas fa-play"></i>';
                                isPlaying = false;
                            };
                            
                            const playPromise = audioPlayer.play();
                            if (playPromise !== undefined) {
                                playPromise
                                    .then(() => {
                                        playBtn.innerHTML = '<i class="fas fa-pause"></i>';
                                        isPlaying = true;
                                    })
                                    .catch(error => {
                                        console.error('Playback failed:', error);
                                        playBtn.innerHTML = '<i class="fas fa-play"></i>';
                                        isPlaying = false;
                                    });
                            }
                            
                            audioPlayer.onended = () => {
                                playBtn.innerHTML = '<i class="fas fa-play"></i>';
                                audioPlayer.style.display = 'none';
                                if (durationDisplay) {
                                    durationDisplay.style.display = 'block';
                                }
                                isPlaying = false;
                            };
                        } catch (error) {
                            console.error('Error playing audio:', error);
                            alert('Failed to play audio.');
                            playBtn.innerHTML = '<i class="fas fa-play"></i>';
                            isPlaying = false;
                        }
                    } else {
                        if (audioPlayer) {
                            audioPlayer.pause();
                            playBtn.innerHTML = '<i class="fas fa-play"></i>';
                            audioPlayer.style.display = 'none';
                            if (durationDisplay) {
                                durationDisplay.style.display = 'block';
                            }
                            isPlaying = false;
                        }
                    }
                }
                """

    @staticmethod
    def chat_detail() -> str:
        """
        JavaScript for the chat detail page.

        Handles:
        - Message sending and display
        - Chat title editing
        - Message loading (pagination)
        - Delete chat confirmation
        - Auto-scroll behavior
        - Textarea auto-resize

        Returns:
            str: JavaScript code for chat detail page
        """
        return """
            let messageOffset = 0;
            const messageLimit = 20;
            let isProcessing = false;

            async function sendMessage() {
                if (isProcessing) return;
                
                const input = document.querySelector('.message-input');
                const content = input.value.trim();
                if (!content) return;
                
                isProcessing = true;
                const sendBtn = document.querySelector('.send-btn');
                sendBtn.disabled = true;
                
                addMessage(content, 'user');
                input.value = '';
                adjustTextarea(input);
                
                showLoadingSpinner();
                
                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            chat_id: window.location.pathname.split('_')[1],
                            message: content
                        })
                    });

                    removeLoadingSpinner();
                    
                    if (!response.ok) {
                        throw new Error(await response.text());
                    }

                    const data = await response.json();
                    if (!data.response) {
                        throw new Error('Invalid response format');
                    }

                    addMessage(data.response, 'assistant', data.references);

                } catch (error) {
                    console.error('Error:', error);
                    removeLoadingSpinner();
                    addMessage('An error occurred. Please try again.', 'assistant');
                } finally {
                    isProcessing = false;
                    sendBtn.disabled = false;
                }
            }

            function addMessage(content, role, references = null, time = null) {
                const container = document.querySelector('.messages-container');
                const message = document.createElement('div');
                message.className = `message ${role}-message`;
                
                let html = `<div class="message-content">${content}</div>`;
                
                if (time) {
                    html += `<div class="message-time">${time}</div>`;
                }
                
                message.innerHTML = html;
                container.appendChild(message);
                container.scrollTop = container.scrollHeight;
            }

            function adjustTextarea(el) {
                el.style.height = '44px';
                el.style.height = (el.scrollHeight) + 'px';
            }

            function showLoadingSpinner() {
                const container = document.querySelector('.messages-container');
                const loading = document.createElement('div');
                loading.className = 'loading-message';
                loading.innerHTML = `
                    <div class="spinner">
                        <i class="fas fa-circle-notch fa-spin"></i>
                    </div>
                    <p>Thinking...</p>
                `;
                container.appendChild(loading);
                container.scrollTop = container.scrollHeight;
            }

            function removeLoadingSpinner() {
                const spinner = document.querySelector('.loading-message');
                if (spinner) spinner.remove();
            }

            function showSourceLoading(event) {
                const link = event.currentTarget;
                const loadingSpinner = link.nextElementSibling;
                loadingSpinner.style.display = 'inline-block';
            }

            async function saveChatTitle(chatId) {
                const titleContainer = document.querySelector('.chat-title');
                const titleInput = titleContainer.querySelector('.chat-title-input');
                const titleText = titleContainer.querySelector('.chat-title-text');
                const newTitle = titleInput.value.trim();

                if (!newTitle) {
                    alert("Title cannot be empty");
                    return;
                }

                try {
                    const response = await fetch(`/api/edit-chat-title/${chatId}`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ title: newTitle }),
                    });

                    if (!response.ok) {
                        throw new Error("Failed to update chat title");
                    }

                    const data = await response.json();
                    titleText.textContent = data.new_title;
                    toggleTitleEdit(false);
                } catch (error) {
                    console.error("Error updating chat title:", error);
                    alert("Failed to update chat title");
                }
            }

            // Event listeners
            document.addEventListener('DOMContentLoaded', () => {
                const input = document.querySelector('.message-input');
                const container = document.querySelector('.messages-container');
                
                container.scrollTop = container.scrollHeight;
                
                input.addEventListener('input', (e) => {
                    adjustTextarea(e.target);
                });
                
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                    }
                });

                const titleInput = document.querySelector('.chat-title-input');
                if (titleInput) {
                    titleInput.addEventListener('keydown', (e) => {
                        const chatId = window.location.pathname.split('_')[1];
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            saveChatTitle(chatId);
                        } else if (e.key === 'Escape') {
                            toggleTitleEdit(false);
                        }
                    });
                }
            });

            async function deleteChat() {
                if (!confirm('Are you sure you want to delete this chat?')) return;
                
                try {
                    const response = await fetch(
                        `/api/delete-chat/${window.location.pathname.split('_')[1]}`,
                        { method: 'POST' }
                    );
                    
                    if (response.ok) {
                        window.location.href = '/notes';
                    } else {
                        alert('Failed to delete chat');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('Error deleting chat');
                }
            }
            """
