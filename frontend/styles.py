class Styles:
    @staticmethod
    def common():
        return """
            body {
                font-family: Arial, sans-serif;
                background-color: #f9f9f9;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }

            /* Update text elements to use Arial */
            .auth-title, .title {
                font-weight: bold;
            }

            .note-title {
                font-weight: bold;
            }

            .form-label {
                font-weight: 500;
            }

            .auth-btn, .search-btn, .clear-btn, .view-btn {
                font-family: Arial, sans-serif;
                font-weight: 500;
            }

            .note-date {
                font-weight: 500;
            }

            .note-preview {
                font-weight: normal;
            }

            input, textarea, button {
                font-family: Arial, sans-serif;
            }

            .note-duration {
                color: #666;
                font-size: 0.9em;
                margin: 0;
                font-weight: bold;
                display: inline-flex;
                align-items: center;
            }

            .auth-container {
                width: 90%;
                max-width: 400px;
                background-color: #ffffff;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }
            .auth-title {
                font-size: 24px;
                font-weight: bold;
                color: navy;
                text-align: center;
                margin-bottom: 20px;
            }
            .auth-form {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            .form-group {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            .form-label {
                color: navy;
                font-weight: 500;
            }
            .form-input {
                padding: 10px;
                border: 1px solid navy;
                border-radius: 4px;
                font-size: 16px;
            }
            .form-input:focus {
                outline: none;
                border-color: #004080;
                box-shadow: 0 0 0 2px rgba(0, 64, 128, 0.1);
            }
            .auth-btn {
                font-size: 16px;
                padding: 12px 20px;
                background-color: navy;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            .auth-btn:hover {
                background-color: #004080;
            }
            .auth-link {
                text-align: center;
                margin-top: 15px;
                color: #666;
            }
            .auth-link a {
                color: navy;
                text-decoration: none;
                font-weight: 500;
            }
            .auth-link a:hover {
                text-decoration: underline;
            }
            .error-message {
                color: #dc3545;
                background-color: #ffe6e6;
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 15px;
                font-size: 14px;
                text-align: center;
            }

            /* Common responsive adjustments */
            @media (max-width: 768px) {
                body {
                    padding: 10px;
                }
                
                .container {
                    width: 95%;
                    padding: 15px;
                    margin: 10px auto;
                }

                /* Auth pages responsive styles */
                .auth-container {
                    width: 95%;
                    padding: 15px;
                    margin: 10px;
                }

                .auth-title {
                    font-size: 20px;
                }

                .form-input {
                    padding: 8px;
                    font-size: 14px;
                }

                .auth-btn {
                    padding: 10px 15px;
                    font-size: 14px;
                }

                /* Home page responsive styles */
                .controls {
                    display: flex;
                    flex-wrap: wrap;
                    justify-content: center;
                    gap: 15px;
                }

                .record-btn, .stop-btn, .upload-btn {
                    font-size: 32px;
                    padding: 8px;
                    margin: 0;
                }

                .audio-player {
                    width: 100%;
                    max-width: 300px;
                }

                .save-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 10px;
                }

                .save-btn, .notes-btn {
                    width: 100%;
                    max-width: 200px;
                }

                /* Notes page responsive styles */
                .note {
                    padding: 12px;
                }

                .note-header {
                    flex-direction: column;
                    gap: 10px;
                }

                .note-actions {
                    justify-content: flex-start;
                    width: 100%;
                }

                .note-info {
                    width: 100%;
                }

                .note-title {
                    font-size: 16px;
                    word-break: break-word;
                }

                .note-preview {
                    font-size: 13px;
                }

                .search-container {
                    flex-direction: column;
                    gap: 10px;
                }

                .date-field {
                    flex-direction: column;
                    width: 100%;
                }

                .date-input {
                    width: 100%;
                }

                .keyword-field {
                    width: 100%;
                }

                .button-field {
                    flex-direction: row;
                    justify-content: space-between;
                    width: 100%;
                }

                .search-btn, .clear-btn {
                    flex: 1;
                }

                /* Note detail page responsive styles */
                .note-transcription {
                    font-size: 14px;
                    line-height: 1.4;
                }

                .form-textarea {
                    min-height: 200px;
                    font-size: 14px;
                }

                .form-buttons {
                    flex-direction: column;
                    gap: 10px;
                }

                .save-btn, .cancel-btn {
                    width: 100%;
                }

                .back-button {
                    margin-top: 20px;
                    margin-bottom: 15px;
                    font-size: 14px;
                    padding: 8px 12px;
                }

                /* Audio player responsive styles */
                .audio-player {
                    width: 100%;
                    max-width: none;
                }

                /* Logout button positioning */
                .logout-btn {
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    z-index: 1000;
                }
            }

            /* Small phones */
            @media (max-width: 380px) {
                .auth-title {
                    font-size: 18px;
                }

                .record-btn, .stop-btn, .upload-btn {
                    font-size: 28px;
                    padding: 6px;
                }

                .note-title .note-duration {
                    font-size: 14px;
                }

                .note-preview {
                    font-size: 12px;
                }
            }

            /* Landscape orientation adjustments */
            @media (max-height: 600px) and (orientation: landscape) {
                body {
                    height: auto;
                    min-height: 100vh;
                }

                .container {
                    margin: 60px auto;
                }

                .audio-wrapper {
                    margin: 10px 0;
                }

                .controls {
                    margin: 10px 0;
                }
            }
        """

    @staticmethod
    def home():
        return """
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                background-color: white;
                color: navy;
                padding: 20px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }
            .controls {
                margin: 20px 0;
            }
                .record-btn, .stop-btn, .upload-btn {
                font-size: 40px;
                background: none;
                border: none;
                cursor: pointer;
                padding: 10px;
                margin: 0 10px;
                color: navy;
            }
            .record-btn:hover {
                color: red;
            }
                .upload-btn:hover {
                    color: #004080;
                }
            .stop-btn:hover {
                color: #ff8000;
            }
            .stop-btn[disabled] {
                color: #ccc;
                cursor: not-allowed;
            }
            .audio-wrapper {
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                margin-top: 20px;
            }
            .audio-player {
                margin-top: 20px;
                width: 100%;
                max-width: 400px;
                border: 2px solid navy;
                border-radius: 10px;
                box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
                background-color: #f9f9f9;
            }
            .save-container {
                margin-top: 20px;
            }
            .save-btn {
                font-size: 16px;
                padding: 10px 20px;
                background-color: navy;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            .save-btn[disabled] {
                background-color: #ccc;
                cursor: not-allowed;
            }
            .save-btn:hover:not([disabled]) {
                background-color: #004080;
            }
            .notes-btn {
                font-size: 16px;
                padding: 10px 20px;
                background-color: navy;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            .notes-btn:hover {
                background-color: #004080;
            }
            .logout-btn {
                padding: 8px 16px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                transition: background-color 0.2s;
            }
            .logout-btn:hover {
                background-color: #c82333;
            }
            .chat-btn {
                font-size: 40px;
                background: none;
                border: none;
                cursor: pointer;
                padding: 10px;
                margin: 0 10px;
                color: navy;
            }
            .chat-btn:hover {
                color: #2196F3;
            }
            """

    @staticmethod
    def notes():
        return """
            body {
                font-family: Arial, sans-serif;
                background-color: #f9f9f9;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                width: 90%;
                max-width: 800px;
                background-color: #ffffff;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                overflow-y: auto;
                max-height: 90vh;
            }
            .back-button {
                display: inline-block;
                margin: 40px 0 20px 20px;
                font-size: 16px;
                color: #ffffff;
                background-color: navy;
                padding: 10px 15px;
                text-decoration: none;
                border-radius: 4px;
            }
            .back-button:hover {
                background-color: #004080;
            }
            .title {
                font-size: 24px;
                font-weight: bold;
                color: navy;
                margin-bottom: 15px;
                margin-left: 10px;
            }
            .note {
                display: flex;
                flex-direction: column;
                background-color: #f3f3f3;
                padding: 10px;
                border-radius: 8px;
                margin-bottom: 10px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .note-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 5px;
                color: #333;
            }
            .note-info {
                display: flex;
                align-items: center;
                gap: 10px;
                flex: 1;
            }
            .note-title {
                color: navy;
                font-weight: bold;
                font-size: clamp(0.9em, 2vw, 1.2em);
                margin: 0;
                word-break: break-word;
                line-height: 1.3;
                display: flex;
                align-items: center;
            }
            .note-duration {
                color: #666;
                font-size: 0.9em;
                margin: 0;
                font-weight: bold;
                display: inline-flex;
                align-items: center;
            }
            .note-date {
                color: #666;
                font-size: 0.9em;
                margin: 0;
                font-weight: bold;
            }
            .note-preview {
                color: #666;
                font-size: 14px;
                display: -webkit-box;
                -webkit-box-orient: vertical;
                overflow: hidden;
                text-overflow: ellipsis;
                -webkit-line-clamp: 3;
            }
            .view-btn {
                font-size: 14px;
                padding: 8px 16px;
                background-color: navy;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            .view-btn:hover {
                background-color: #004080;
            }
            .search-wrapper {
                margin-bottom: 20px;
                width: 100%;
            }
            .search-form {
                width: 100%;
            }
            .search-container {
                display: flex;
                gap: 10px;
                align-items: center;
                padding: 12px;
                background-color: #f3f3f3;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .date-field {
                display: flex;
                align-items: center;
                gap: 8px;
                flex: 1;
            }
            .keyword-field {
                display: flex;
                align-items: center;
                gap: 8px;
                flex: 2;
            }
            .keyword-input {
                padding: 6px 12px;
                border: 1px solid navy;
                border-radius: 4px;
                color: #333;
                width: 100%;
                font-size: 14px;
            }
            .keyword-input::placeholder {
                color: #999;
            }
            .date-input {
                padding: 6px;
                border: 1px solid navy;
                border-radius: 4px;
                color: #333;
                width: 130px;
                font-size: 14px;
                flex: 1;
                min-width: 110px;
            }
            .date-input::-webkit-calendar-picker-indicator {
                cursor: pointer;
            }
            .button-field {
                display: flex;
                gap: 6px;
            }
            .search-btn, .clear-btn {
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            .search-btn {
                background-color: navy;
                color: white;
            }
            .clear-btn {
                background-color: #666;
                color: white;
            }
            .logout-btn {
                padding: 8px 16px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                transition: background-color 0.2s;
            }
            .logout-btn:hover {
                background-color: #c82333;
            }
            .chat {
                display: flex;
                flex-direction: column;
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                border-left: 3px solid #2196F3;
            }
            .chat .note-title {
                color: #2196F3;
                font-size: clamp(0.9em, 2vw, 1.2em);
                margin: 0;
                word-break: break-word;
                line-height: 1.3;
            }
            .chat-message-count {
                color: #666;
                font-size: 0.9em;
                margin: 0;
                font-weight: bold;
                display: inline-flex;
                align-items: center;
                gap: 5px;
            }
            .fa-robot {
                color: #2196F3;
                font-size: 1.2em;
                margin-right: 8px;
            }

            @media (max-width: 768px) {
                .search-container {
                    flex-direction: column;
                    align-items: stretch;
                }
                .date-field, .keyword-field {
                    width: 100%;
                }
                .date-field {
                    justify-content: space-between;
                    flex-wrap: wrap;
                    gap: 10px;
                }
                .note-preview {
                    -webkit-line-clamp: 2;
                }
                .chat {
                    padding: 12px;
                }
                .chat .note-header {
                    flex-direction: row;
                    justify-content: space-between;
                    align-items: center;
                }
                .chat-message-count {
                    font-size: 0.85em;
                }
                .chat .note-preview {
                    font-size: 13px;
                    -webkit-line-clamp: 2;
                }
            }

            @media (max-width: 400px) {
                .date-input {
                    min-width: 90px;
                }
                .date-field span {
                    min-width: 35px;
                }
                .chat {
                    padding: 10px;
                }
                .chat .note-title {
                    font-size: 0.95em;
                }
                .chat-message-count {
                    font-size: 0.8em;
                }
                .fa-robot {
                    font-size: 1.1em;
                    margin-right: 6px;
                }
            }

            @media (max-height: 600px) and (orientation: landscape) {
                .chat {
                    margin-bottom: 10px;
                }
            }
            """

    @staticmethod
    def note_detail():
        return """
            body {
                font-family: Arial, sans-serif;
                background-color: #f9f9f9;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }
            .container {
                width: 90%;
                max-width: 800px;
                background-color: #ffffff;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                overflow-y: auto;
                max-height: 90vh;
            }
            .back-button {
                display: inline-block;
                margin-top: 40px;
                margin-bottom: 20px;
                font-size: 16px;
                color: #ffffff;
                background-color: navy;
                padding: 10px 15px;
                text-decoration: none;
                border-radius: 4px;
            }
            .back-button:hover {
                background-color: #004080;
            }
            .title {
                font-size: 24px;
                font-weight: bold;
                color: navy;
                margin-bottom: 15px;
            }
            .note {
                display: flex;
                flex-direction: column;
                background-color: #f3f3f3;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 10px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .note-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 5px;
                color: #333;
            }
            .note-info {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .note-title {
                color: navy;
                font-weight: bold;
                font-size: 1.2em;
                margin: 0;
            }
            .note-date {
                color: #666;
                font-size: 0.9em;
                margin: 0;
                font-weight: bold;
            }
            .note-transcription {
                color: #333;
                font-size: 16px;
                line-height: 1.6;
                white-space: pre-wrap;
            }
            .note-actions {
                display: flex;
                align-items: center;
                gap: 10px;
                justify-content: flex-end;
            }
            .delete-btn {
                background: none;
                border: none;
                color: #dc3545;
                cursor: pointer;
                padding: 5px;
                font-size: 1.1em;
                opacity: 0.7;
                transition: opacity 0.2s;
                margin: 0;
                display: inline-flex;
                align-items: center;
            }
            .delete-btn:hover {
                opacity: 1;
            }
            .edit-btn {
                background: none;
                border: none;
                color: #2196F3;
                cursor: pointer;
                padding: 5px;
                font-size: 1.1em;
                opacity: 0.7;
                transition: opacity 0.2s;
                margin-top: -5px;
            }
            .edit-btn:hover {
                opacity: 1;
            }
            .logout-btn {
                padding: 8px 16px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                transition: background-color 0.2s;
            }
            .logout-btn:hover {
                background-color: #c82333;
            }
            .edit-container {
                margin-top: 20px;
                width: 100%;
            }
            .edit-title {
                color: navy;
                font-size: 1.5em;
                margin-bottom: 20px;
            }
            .edit-form {
                width: 100%;
                background-color: white;
                border-radius: 8px;
            }
            .form-input {
                width: 100%;
                padding: 12px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 1.2em;
                color: navy;
                margin-bottom: 15px;
            }
            .form-textarea {
                width: 100%;
                min-height: 300px;
                padding: 12px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 16px;
                line-height: 1.6;
                resize: vertical;
                color: #333;
                margin-bottom: 15px;
            }
            .form-buttons {
                display: flex;
                gap: 10px;
                justify-content: flex-end;
            }
            .save-btn, .cancel-btn {
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                transition: background-color 0.2s;
            }
            .save-btn {
                background-color: #28a745;
                color: white;
            }
            .save-btn:hover {
                background-color: #218838;
            }
            .cancel-btn {
                background-color: #6c757d;
                color: white;
            }
            .cancel-btn:hover {
                background-color: #5a6268;
            }
            .note-container, .edit-container {
                transition: opacity 0.3s ease;
            }
            .play-btn {
                background: none;
                border: none;
                color: #4CAF50;
                cursor: pointer;
                padding: 5px;
                font-size: 1.1em;
                opacity: 0.7;
                transition: opacity 0.2s;
                margin-top: -5px;
            }
            .play-btn:hover {
                opacity: 1;
            }
            .audio-player {
                width: 100%;
                max-width: 300px;
                margin-right: 10px;
            }
            .play-btn,
            .edit-btn,
            .delete-btn {
                font-size: 1.2em;
                padding: 8px;
            }
            """

    @staticmethod
    def chat_detail():
        return """
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    padding: 20px;
                    box-sizing: border-box;
                    background-color: #f5f5f5;
                }

                .chat-container {
                    width: 100%;
                    font-family: Arial, sans-serif;
                    max-width: 1000px;
                    height: 90vh;
                    display: flex;
                    flex-direction: column;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                }

                .chat-header {
                    padding: 15px 20px;
                    background: navy;
                    font-family: Arial, sans-serif;
                    color: white;
                    border-radius: 8px 8px 0 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .chat-title {
                    display: flex;
                    align-items: center;
                    font-family: Arial, sans-serif;
                    gap: 10px;
                    font-size: 1em;  /* Reduced from 1.2em */
                    margin: 0;
                }

                .chat-title-input {
                    background: transparent;
                    border: 1px solid rgba(255,255,255,0.3);
                    color: white;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-size: 1em;
                    width: 100%;
                    display: none;
                }

                .chat-title-input:focus {
                    outline: none;
                    border-color: white;
                }

                .chat-title-text {
                    margin: 0;
                    padding: 5px 10px;
                    font-size: 1.1em;  /* Controlled size for the title text */
                    font-weight: normal;  /* Remove bold if too heavy */
                }

                .chat-title h1 {
                    font-size: 1.1em;  /* Control the h1 size */
                    margin: 0;
                    font-weight: 500;  /* Semi-bold instead of bold */
                }

                .edit-mode .chat-title-text {
                    display: none;
                }

                .edit-mode .chat-title-input {
                    display: block;
                }

                .chat-actions {
                    display: flex;
                    gap: 10px;
                }

                .action-btn {
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    padding: 5px;
                    font-size: 1.1em;
                    opacity: 0.8;
                    transition: opacity 0.2s;
                }

                .action-btn:hover {
                    opacity: 1;
                }

                .messages-container {
                    flex: 1;
                    overflow-y: auto;
                    padding: 20px;
                    display: flex;
                    flex-direction: column;
                }

                .message {
                    max-width: 80%;
                    margin-bottom: 20px;
                    padding: 10px 15px;
                    border-radius: 8px;
                    position: relative;
                }

                .user-message {
                    background: #E3F2FD;
                    align-self: flex-end;
                    margin-left: 20%;
                }

                .assistant-message {
                    background: #F5F5F5;
                    align-self: flex-start;
                    margin-right: 20%;
                }

                .message-content {
                    margin: 0;
                    line-height: 1.4;
                    white-space: pre-wrap;
                }

                .message-time {
                    font-size: 0.8em;
                    color: #666;
                    margin-top: 5px;
                    text-align: right;
                }

                .input-container {
                    padding: 20px;
                    border-top: 1px solid #eee;
                    display: flex;
                    gap: 10px;
                }

                .message-input {
                    flex: 1;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    resize: none;
                    min-height: 44px;
                    max-height: 200px;
                }

                .send-btn {
                    background: navy;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }

                .send-btn:hover {
                    background: #000080;
                }

                .send-btn:disabled {
                    background: #ccc;
                    cursor: not-allowed;
                }

                .empty-messages {
                    text-align: center;
                    color: #666;
                    margin: auto;
                }

                .loading-message {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    color: #666;
                    margin: 20px 0;
                }

                .spinner {
                    font-size: 1.2em;
                }

                /* Landscape mode */
                @media (max-height: 600px) and (orientation: landscape) {
                    .chat-container {
                        height: auto;
                        min-height: 100vh;
                    }

                    .messages-container {
                        max-height: 60vh;
                    }

                    .message {
                        margin-bottom: 24px;
                    }
                }

                .load-more-container {
                    text-align: center;
                    padding: 10px 0;
                }

                .load-more-btn {
                    background: navy;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                }

                .load-more-btn:hover {
                    background: #004080;
                }

                .source-loading {
                    margin-left: 8px;
                    color: #666;
                }
                """
