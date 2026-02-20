import React from 'react';
import './ChatSidebar.css';

const ChatSidebar = ({
    chats = [],
    activeChatId,
    onChatSelect,
    onNewChat,
    onDeleteChat,
    loading = false,
    mobileOpen = false
}) => {
    const handleDelete = (e, chatId) => {
        e.stopPropagation();
        if (window.confirm('Are you sure you want to delete this chat?')) {
            onDeleteChat(chatId);
        }
    };

    if (loading) {
        return (
            <div className={`chat-sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
                <div className="sidebar-header">
                    <button className="btn btn-primary" disabled>
                        <span className="spinner spinner-sm"></span>
                    </button>
                </div>
                <div className="sidebar-loading">
                    <div className="spinner"></div>
                </div>
            </div>
        );
    }

    return (
        <div className={`chat-sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
            <div className="sidebar-header">
                <button className="btn btn-primary" onClick={onNewChat}>
                    + New Chat
                </button>
            </div>

            <div className="chat-list">
                {chats.length === 0 ? (
                    <div className="empty-state">
                        <p>No chats yet</p>
                        <p className="text-muted">Click "New Chat" to start</p>
                    </div>
                ) : (
                    chats.map((chat) => (
                        <div
                            key={chat.chat_id}
                            className={`chat-item ${activeChatId === chat.chat_id ? 'active' : ''}`}
                            onClick={() => onChatSelect(chat.chat_id)}
                        >
                            <div className="chat-item-content">
                                <div className="chat-title">{chat.title || 'New Chat'}</div>
                                <div className="chat-date">
                                    {new Date(chat.created_at).toLocaleDateString()}
                                </div>
                            </div>
                            <button
                                className="chat-delete"
                                onClick={(e) => handleDelete(e, chat.chat_id)}
                                title="Delete chat"
                            >
                                ×
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default ChatSidebar;
