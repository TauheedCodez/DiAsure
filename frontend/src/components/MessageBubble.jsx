import React from 'react';
import { useNavigate } from 'react-router-dom';
import './MessageBubble.css';

const MessageBubble = ({ role, content, timestamp }) => {
    const navigate = useNavigate();
    const isUser = role === 'user';

    // Format timestamp if provided
    const formatTime = (time) => {
        if (!time) return '';
        const date = new Date(time);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    // Parse buttons from content - format: [[BUTTON:label:url]]
    const parseButtons = (text) => {
        const buttonRegex = /\[\[BUTTON:([^:]+):([^\]]+)\]\]/g;
        const buttons = [];
        let match;
        while ((match = buttonRegex.exec(text)) !== null) {
            buttons.push({ label: match[1], url: match[2] });
        }
        // Remove button syntax from text
        const cleanText = text.replace(buttonRegex, '');
        return { cleanText, buttons };
    };

    // Simple markdown-like rendering for bold, lists, emojis
    const formatContent = (text) => {
        if (!text) return '';

        // Convert **bold** to <strong>
        let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Preserve line breaks
        formatted = formatted.replace(/\n/g, '<br />');

        return formatted;
    };

    const handleButtonClick = (url) => {
        navigate(url);
    };

    const { cleanText, buttons } = parseButtons(content || '');

    return (
        <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
            <div className="message-content" dangerouslySetInnerHTML={{ __html: formatContent(cleanText) }} />
            {buttons.length > 0 && (
                <div className="message-actions">
                    {buttons.map((btn, index) => (
                        <button
                            key={index}
                            className="action-btn"
                            onClick={() => handleButtonClick(btn.url)}
                        >
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                                <circle cx="12" cy="10" r="3" />
                            </svg>
                            {btn.label}
                        </button>
                    ))}
                </div>
            )}
            {timestamp && <div className="message-timestamp">{formatTime(timestamp)}</div>}
        </div>
    );
};

export default MessageBubble;

