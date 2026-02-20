import React, { useState } from 'react';
import './MessageInput.css';

const MessageInput = ({
    onSend,
    disabled = false,
    placeholder = 'Type your message...',
    showImageUpload = false,
    onImageUpload
}) => {
    const [message, setMessage] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (message.trim() && !disabled) {
            onSend(message.trim());
            setMessage('');
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="message-input-container">
            {showImageUpload && (
                <button
                    type="button"
                    onClick={onImageUpload}
                    className="btn-icon upload-btn"
                    title="Upload ulcer image"
                    disabled={disabled}
                >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                        <circle cx="12" cy="13" r="4"></circle>
                    </svg>
                </button>
            )}
            <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={placeholder}
                disabled={disabled}
                className="message-input"
            />
            <button
                type="submit"
                disabled={disabled || !message.trim()}
                className="btn btn-primary send-btn"
            >
                <span className="send-icon">➤</span>
                <span className="send-text">Send</span>
            </button>
        </form>
    );
};

export default MessageInput;
