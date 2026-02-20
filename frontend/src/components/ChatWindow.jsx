import React, { useRef } from 'react';
import MessageBubble from './MessageBubble';
import MessageInput from './MessageInput';
import './ChatWindow.css';

const ChatWindow = ({
    messages = [],
    onSendMessage,
    loading = false,
    showImageUpload = false,
    onImageUpload,
}) => {
    const messagesEndRef = useRef(null);
    const messagesContainerRef = useRef(null);

    // Auto-scroll to bottom when new messages arrive
    React.useEffect(() => {
        if (messagesContainerRef.current) {
            messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
        }
    }, [messages]);

    return (
        <div className="chat-window">
            <div className="chat-messages" ref={messagesContainerRef}>
                {messages.length === 0 ? (
                    <div className="empty-chat">
                        <h3>Welcome to DiAsure</h3>
                        <p>Start a conversation by typing a message below.</p>
                        <p className="text-muted">
                            Ask me anything about diabetic foot ulcers, or upload an image for personalized assessment.
                        </p>
                    </div>
                ) : (
                    <>
                        {messages.map((msg, index) => (
                            <MessageBubble
                                key={index}
                                role={msg.role}
                                content={msg.content}
                                timestamp={msg.created_at || msg.timestamp}
                            />
                        ))}
                        {loading && (
                            <div className="loading-indicator">
                                <div className="spinner"></div>
                                <span>AI is thinking...</span>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </>
                )}
            </div>

            <MessageInput
                onSend={onSendMessage}
                disabled={loading}
                placeholder={loading ? 'AI is responding...' : 'Type your message...'}
                showImageUpload={showImageUpload}
                onImageUpload={onImageUpload}
            />
        </div>
    );
};

export default ChatWindow;
