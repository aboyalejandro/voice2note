def get_common_styles():
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

    /* Search container styles */
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
        flex: 1;  /* Allow date field to grow */
    }

    .keyword-field {
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 2;  /* Give keyword field more growing space */
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
        flex: 1;  /* Allow inputs to grow within date-field */
        min-width: 110px;  /* Minimum width to prevent too much shrinking */
    }

    .date-input::-webkit-calendar-picker-indicator {
        cursor: pointer;
    }

    /* Note actions alignment */
    .note-actions {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Responsive adjustments */
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

        .note-header {
            flex-direction: row;  /* Keep horizontal layout */
            justify-content: space-between;
            align-items: center;  /* Center align items vertically */
        }

        .note-actions {
            justify-content: flex-end;
            align-items: center;
            width: auto;  /* Remove full width */
        }

        .note-info {
            flex: 1;  /* Allow info to take remaining space */
        }
    }

    @media (max-width: 400px) {
        .date-input {
            min-width: 90px;  /* Even smaller minimum width for very small screens */
        }

        .date-field span {
            min-width: 35px;
        }
    }

    /* Search container and button styles */
    .search-container {
        display: flex;
        gap: 10px;
        align-items: center;
        padding: 12px;
        background-color: #f3f3f3;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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

    /* Responsive adjustments */
    @media (max-width: 755px) {
        .search-container {
            flex-direction: column;
            align-items: stretch;
        }
        
        .date-field, .keyword-field {
            width: 100%;
        }
        
        .button-field {
            display: flex;
            gap: 10px;
            width: 100%;
        }
        
        .search-btn, .clear-btn {
            flex: 1;  /* Make buttons expand equally */
            padding: 10px;  /* Slightly larger padding for better touch targets */
        }
    }

    /* Add back the logout button styles */
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
    """
